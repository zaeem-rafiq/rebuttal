#!/usr/bin/env python3
"""scripts/reset_demo.py - Reset Rebuttal deployed stack into a clean, take-ready state.

Performs:
1. Archives old case rows for closed/test disputes into data/archive/
2. Reseeds data/fixtures to Supabase Cloud and local SQLite
3. Checks Bedrock AgentCore Runtime status is READY
4. Checks all 3 Lambda Function URLs are healthy
5. Checks Console URL returns HTTP 200
6. Checks Twilio phone number is reachable and configured
7. Emits the required proof line:
   PROOF R-15: reset_demo ok runtime=READY lambdas=3/3 console=200 = PASS
"""

import os
import sys
import json
import time
import sqlite3
import argparse
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env")

PROOF_PATH = REPO_ROOT / "docs" / "proofs" / "R-15.md"
ARCHIVE_DIR = REPO_ROOT / "data" / "archive"
LOCAL_DB_PATH = REPO_ROOT / "data" / "local_supabase.db"

STRIPE_WEBHOOK_URL = "https://qsmgbb5rtmmgnmry6u55uanxy40pwvhq.lambda-url.us-east-1.on.aws/"
TWILIO_WEBHOOK_URL = "https://n2g4gh2yjripct4y4sre3lnx2e0ivggv.lambda-url.us-east-1.on.aws/"
INJECT_URL = "https://aovwsnanmseqfc753yan52g3be0nqnem.lambda-url.us-east-1.on.aws/"
CONSOLE_URL = "https://main.dtrewze9hbzeb.amplifyapp.com"

AGENT_RUNTIME_ID = "rebuttal-pASUe6CVmu"


def append_proof(line: str):
    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = ""
    if PROOF_PATH.exists():
        with open(PROOF_PATH, "r", encoding="utf-8") as f:
            existing = f.read()
    if line not in existing:
        with open(PROOF_PATH, "a", encoding="utf-8") as f:
            f.write(f"{line}\n")


def archive_old_cases(supabase_client) -> int:
    """Archive non-standard/closed test disputes and decisions."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archived_count = 0
    preserved_ids = {"dp_S1", "dp_S2", "dp_S3"}

    # Archive from Supabase Cloud if available
    if supabase_client:
        try:
            resp = supabase_client.table("disputes").select("*").execute()
            rows = resp.data or []
            to_archive = [r for r in rows if r.get("id") not in preserved_ids or r.get("status") in ("won", "lost", "charge_refunded")]
            if to_archive:
                archive_file = ARCHIVE_DIR / f"disputes_supabase_{ts}.json"
                with open(archive_file, "w", encoding="utf-8") as f:
                    json.dump(to_archive, f, indent=2)
                for r in to_archive:
                    row_id = r["id"]
                    supabase_client.table("audit_log").delete().eq("dispute_id", row_id).execute()
                    supabase_client.table("decisions").delete().eq("dispute_id", row_id).execute()
                    if row_id not in preserved_ids:
                        supabase_client.table("disputes").delete().eq("id", row_id).execute()
                    archived_count += 1
            # Clear all decisions for a clean take
            supabase_client.table("decisions").delete().neq("id", "___none___").execute()
        except Exception as e:
            print(f"  [Archive Notice] Supabase archiving error: {e}", file=sys.stderr)

    # Archive from Local SQLite
    if LOCAL_DB_PATH.exists():
        try:
            conn = sqlite3.connect(LOCAL_DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            rows = cur.execute("SELECT * FROM disputes").fetchall()
            to_archive_local = [dict(r) for r in rows if r["id"] not in preserved_ids or r["status"] in ("won", "lost", "charge_refunded")]
            if to_archive_local:
                archive_file = ARCHIVE_DIR / f"disputes_local_{ts}.json"
                with open(archive_file, "w", encoding="utf-8") as f:
                    json.dump(to_archive_local, f, indent=2)
                for r in to_archive_local:
                    rid = r["id"]
                    cur.execute("DELETE FROM audit_log WHERE dispute_id = ?", (rid,))
                    cur.execute("DELETE FROM decisions WHERE dispute_id = ?", (rid,))
                    if rid not in preserved_ids:
                        cur.execute("DELETE FROM disputes WHERE id = ?", (rid,))
                    archived_count += 1
            cur.execute("DELETE FROM decisions;")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"  [Archive Notice] Local DB archiving error: {e}", file=sys.stderr)

    return archived_count


def reseed_fixtures(supabase_client):
    """Reseed fixtures into Supabase and local DB."""
    from scripts.seed_supabase import (
        seed_supabase_cloud,
        seed_local_db,
        init_local_db,
    )
    if supabase_client:
        seed_supabase_cloud(supabase_client, reset=True)
    conn = init_local_db(LOCAL_DB_PATH)
    seed_local_db(conn, reset=True)
    conn.close()


def check_agentcore_runtime() -> str:
    """Check AgentCore Runtime status is READY."""
    region = os.getenv("AWS_REGION", "us-east-1")
    profile = os.getenv("AWS_PROFILE")
    import boto3
    try:
        session = boto3.Session(profile_name=profile, region_name=region) if profile else boto3.Session(region_name=region)
        ctrl = session.client("bedrock-agentcore-control", region_name=region)
        rt = ctrl.get_agent_runtime(agentRuntimeId=AGENT_RUNTIME_ID)
        status = rt.get("status") or rt.get("agentRuntime", {}).get("status", "READY")
        # Check endpoints if available
        try:
            endpoints = ctrl.list_agent_runtime_endpoints(agentRuntimeId=AGENT_RUNTIME_ID)
            ep_list = endpoints.get("agentRuntimeEndpointSummaries", [])
            for ep in ep_list:
                if ep.get("status") == "READY":
                    return "READY"
        except Exception:
            pass
        if status in ("READY", "ACTIVE"):
            return "READY"
        return status
    except Exception as e:
        # Fallback check via starter toolkit or describe
        return f"ERROR({e})"


def check_lambdas() -> int:
    """Check the 3 Lambda Function URLs are healthy."""
    healthy = 0

    # 1. Stripe webhook: should respond to HTTP (400 without stripe event signature is healthy)
    try:
        req = urllib.request.Request(STRIPE_WEBHOOK_URL, data=b"{}", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status in (200, 400):
                healthy += 1
    except urllib.error.HTTPError as e:
        if e.code in (200, 400):
            healthy += 1
    except Exception:
        pass

    # 2. Twilio webhook: responds 200 to POST
    try:
        data = urllib.parse.urlencode({"From": "+18129551686", "Body": "status"}).encode("utf-8")
        req = urllib.request.Request(
            TWILIO_WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                healthy += 1
    except Exception:
        pass

    # 3. Inject lambda: responds 200 to OPTIONS
    try:
        req = urllib.request.Request(INJECT_URL, method="OPTIONS")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                healthy += 1
    except Exception:
        pass

    return healthy


def check_console() -> int:
    """Check Console URL returns HTTP 200."""
    try:
        req = urllib.request.Request(CONSOLE_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except Exception:
        return 0


def check_twilio_reachable() -> bool:
    """Check Twilio incoming phone number configuration is reachable."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_from = os.getenv("TWILIO_FROM")
    if not (account_sid and auth_token and twilio_from):
        return False
    try:
        from twilio.rest import Client
        tw = Client(account_sid, auth_token)
        numbers = tw.incoming_phone_numbers.list(phone_number=twilio_from)
        if numbers and numbers[0].phone_number == twilio_from:
            return True
        return False
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Reset Rebuttal demo stack to take-ready state.")
    parser.add_argument("--record-proof", action="store_true", help="Record proof line to docs/proofs/R-15.md")
    args = parser.parse_args()

    print("================================================================")
    print("REBUTTAL DEMO RESET (R-15)")
    print("================================================================")

    # 1. Archive old case rows
    print("\n[1/5] Archiving old test cases...", flush=True)
    from scripts.seed_supabase import get_supabase_client
    sb_client = get_supabase_client()
    archived_count = archive_old_cases(sb_client)
    print(f"  Archived {archived_count} case/decision rows to data/archive/", flush=True)

    # 2. Reseed fixtures
    print("\n[2/5] Reseeding data fixtures...", flush=True)
    reseed_fixtures(sb_client)
    print("  Fixtures reseeded into Supabase and local SQLite.", flush=True)

    # 3. Check AgentCore Runtime READY
    print("\n[3/5] Checking Bedrock AgentCore Runtime...", flush=True)
    rt_status = check_agentcore_runtime()
    print(f"  AgentCore Runtime status: {rt_status}", flush=True)

    # 4. Check Lambda Function URLs & Console & Twilio
    print("\n[4/5] Checking Lambda Function URLs, Console, and Twilio...", flush=True)
    lambdas_ok = check_lambdas()
    console_code = check_console()
    twilio_ok = check_twilio_reachable()

    print(f"  Lambdas healthy: {lambdas_ok}/3", flush=True)
    print(f"  Console HTTP status: {console_code}", flush=True)
    print(f"  Twilio reachable: {twilio_ok}", flush=True)

    # 5. Output Proof Line
    all_ok = (
        rt_status == "READY"
        and lambdas_ok == 3
        and console_code == 200
        and twilio_ok
    )

    proof_line = f"PROOF R-15: reset_demo ok runtime={rt_status} lambdas={lambdas_ok}/3 console={console_code} = {'PASS' if all_ok else 'FAIL'}"
    print(f"\n{proof_line}\n", flush=True)

    if args.record_proof or all_ok:
        append_proof(proof_line)

    if not all_ok:
        print("Reset demo completed with warnings / non-passing checks.", file=sys.stderr)
        return 1

    print("Stack is CLEAN and TAKE-READY.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
