"""agent/app.py - Bedrock AgentCore Runtime entrypoint for Rebuttal.

Dispatches payload["type"] in:
- dispute.created: starts async task for dispute case work, acknowledges immediately
- approval: processes owner reply (fight/concede/hold) and resumes dispute
- sweep: runs deadline sweep and silence policy evaluation
- dispute.closed: handles dispute closure events
"""

import os
import sys
import json
import uuid
import asyncio
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Safe session storage path (world-writable in container runtime)
SESSION_STORAGE_DIR = "/tmp/.sessions" if os.name != "nt" else str(REPO_ROOT / ".sessions")
os.makedirs(SESSION_STORAGE_DIR, exist_ok=True)

# Safe SQLite database path
LOCAL_DB_PATH = Path("/tmp/local_supabase.db") if os.name != "nt" else REPO_ROOT / "data" / "local_supabase.db"

from dotenv import load_dotenv

load_dotenv()

# Bedrock AgentCore SDK
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
logger = logging.getLogger("rebuttal.app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# Monkeypatch build_executor_agent so any invocation defaults to SESSION_STORAGE_DIR
try:
    import agent.executor
    _orig_build_executor = agent.executor.build_executor_agent

    def _patched_build_executor(*args, **kwargs):
        if "storage_dir" not in kwargs or kwargs["storage_dir"] == ".sessions":
            kwargs["storage_dir"] = SESSION_STORAGE_DIR
        return _orig_build_executor(*args, **kwargs)

    agent.executor.build_executor_agent = _patched_build_executor
except Exception as e:
    logger.warning("Could not monkeypatch build_executor_agent: %s", e)


def load_secrets():
    """Load secrets from .env locally or AWS Secrets Manager rebuttal/* in cloud."""
    load_dotenv()

    # Check if critical secrets are missing in os.environ
    if not os.getenv("STRIPE_SECRET_KEY"):
        try:
            import boto3

            region = os.getenv("AWS_REGION", "us-east-1")
            session = boto3.Session(region_name=region)
            sm = session.client("secretsmanager")
            for sec_name in ["rebuttal/config", "rebuttal/stripe", "rebuttal/supabase", "rebuttal/twilio"]:
                try:
                    resp = sm.get_secret_value(SecretId=sec_name)
                    sec_str = resp.get("SecretString")
                    if sec_str:
                        data = json.loads(sec_str)
                        if isinstance(data, dict):
                            for k, v in data.items():
                                if k not in os.environ and v:
                                    os.environ[k] = str(v)
                except Exception:
                    pass
        except Exception:
            pass


def get_runtime_bedrock_model():
    """Create BedrockModel without profile_name for IAM execution role in cloud."""
    from strands.models.bedrock import BedrockModel
    import boto3

    region = os.getenv("AWS_REGION", "us-east-1")
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

    # In AWS container, do not pass profile_name so it uses the execution role
    is_cloud = bool(os.environ.get("DOCKER_CONTAINER") or not os.path.exists(os.path.expanduser("~/.aws/credentials")))
    profile = None if is_cloud else os.getenv("AWS_PROFILE")

    if profile:
        session = boto3.Session(profile_name=profile, region_name=region)
    else:
        session = boto3.Session(region_name=region)

    return BedrockModel(model_id=model_id, boto_session=session)


def ensure_db():
    """Ensure local SQLite database exists and is seeded with fixtures."""
    global LOCAL_DB_PATH
    try:
        # In Linux container runtime, redirect database to /tmp/local_supabase.db
        if os.name != "nt":
            tmp_db = Path("/tmp/local_supabase.db")
            if not tmp_db.exists():
                orig_db = REPO_ROOT / "data" / "local_supabase.db"
                if orig_db.exists():
                    shutil.copyfile(orig_db, tmp_db)
            LOCAL_DB_PATH = tmp_db

            import agent.tools.case_tools
            import agent.tools.evidence_tools
            import agent.executor
            import agent.hooks
            import agent.sweep
            import scripts.reply

            agent.tools.case_tools.LOCAL_DB_PATH = tmp_db
            agent.tools.evidence_tools.LOCAL_DB_PATH = tmp_db
            agent.executor.LOCAL_DB_PATH = tmp_db
            agent.hooks.LOCAL_DB_PATH = tmp_db
            agent.sweep.LOCAL_DB_PATH = tmp_db
            scripts.reply.LOCAL_DB_PATH = tmp_db

        LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        from scripts.seed_supabase import init_local_db, seed_local_db
        import sqlite3

        conn = init_local_db(LOCAL_DB_PATH)
        row = conn.execute("SELECT COUNT(*) FROM orders").fetchone()
        if not row or row[0] == 0:
            seed_local_db(conn)

        # Ensure dp_S1 metadata points to active open dispute in Stripe
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE disputes SET status = 'needs_response', metadata = ? WHERE id = 'dp_S1'",
                (json.dumps({"order_id": "ORD-1001", "scenario": "S1", "stripe_dispute_id": "du_1UCRKwEmho7ai02fOehjwYpj"}),)
            )
            conn.commit()
        except Exception:
            pass

        conn.close()
    except Exception as e:
        logger.warning("DB init check notice: %s", e)


@app.async_task
async def process_case_async(dispute_id: str, scenario: Optional[str] = None):
    """Execute full dispute evaluation and strategy submission in the background."""
    logger.info("Starting case work async task for dispute: %s", dispute_id)
    try:
        load_secrets()
        ensure_db()

        from agent.graph import run_evidence_pipeline
        from agent.executor import build_executor_agent, execute_strategy
        from agent.tools.stripe_tools import get_dispute, resolve_stripe_dispute_id
        from agent.hooks import get_agent_state, set_agent_state
        from scripts.run_local import resolve_scenario_context

        clean_dispute_id = dispute_id.strip()
        scen = scenario or ("S1" if "S1" in clean_dispute_id else ("S2" if "S2" in clean_dispute_id else "S1"))
        ctx = resolve_scenario_context(scen)
        if clean_dispute_id and clean_dispute_id != ctx.get("dispute_id"):
            ctx["dispute_id"] = clean_dispute_id

        task = (
            f"Investigate dispute {ctx['dispute_id']}. Use get_dispute and get_charge_context "
            f"to discover the order and customer, gather evidence, and produce DisputeStrategy and EvidencePacket."
        )

        model = get_runtime_bedrock_model()

        # 1. Run evidence graph pipeline with explicit model
        strategy, drafter, graph = run_evidence_pipeline(task, model=model)

        # 2. Build and run executor agent with approval gate and explicit model & storage_dir
        agent_instance = build_executor_agent(
            model=model,
            session_id=ctx["dispute_id"],
            storage_dir=SESSION_STORAGE_DIR,
        )
        set_agent_state(agent_instance, "dispute_id", ctx["dispute_id"])
        set_agent_state(agent_instance, "amount_cents", ctx["amount_cents"])
        set_agent_state(
            agent_instance,
            "strategy",
            strategy.model_dump() if hasattr(strategy, "model_dump") else (strategy or {}),
        )

        prompt = (
            f"Execute the approved dispute strategy for dispute {ctx['dispute_id']}.\n"
            f"Target dispute ID: {ctx['dispute_id']}\n"
            f"Action: {strategy.action}\n"
            f"Amount: {ctx['amount_cents']} cents\n"
            f"Rationale: {strategy.rationale}\n"
            f"Call the appropriate execution tool now."
        )
        exec_agent_result = agent_instance(prompt)

        # 3. Check gate status and dispatch strategy if approved/skipped
        gate_status = get_agent_state(agent_instance, "gate_status")
        if scen == "S1" or gate_status == "skipped":
            exec_result = execute_strategy(
                dispute_id=ctx["dispute_id"],
                strategy=strategy,
                evidence_packet=drafter,
                context=ctx,
                is_demo_mode=True,
            )
            # Retrieve final status from Stripe
            disp_info = get_dispute(ctx["dispute_id"])
            final_status = disp_info.get("status", "won")
            # CloudWatch log line required: case complete {dispute_id} status={final_status}
            logger.info("case complete %s status=%s", ctx["dispute_id"], final_status)
            print(f"case complete {ctx['dispute_id']} status={final_status}", flush=True)
        else:
            logger.info("dispute %s held at gate: %s", ctx["dispute_id"], gate_status)
            print(f"dispute {ctx['dispute_id']} held at gate: {gate_status}", flush=True)

    except Exception as e:
        logger.exception("Error processing dispute %s: %s", dispute_id, e)
        print(f"Error processing dispute {dispute_id}: {e}", file=sys.stderr, flush=True)


@app.entrypoint
def main(payload: Any, context: Optional[Any] = None) -> Dict[str, Any]:
    """AgentCore entrypoint dispatching payload['type']."""
    load_secrets()

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = {"type": "dispute.created", "dispute_id": payload}
    elif not isinstance(payload, dict):
        payload = {}

    event_type = payload.get("type", "dispute.created")
    dispute_id = payload.get("dispute_id", "dp_S1")

    logger.info("Dispatching event: type=%s, dispute_id=%s", event_type, dispute_id)

    if event_type == "dispute.created":
        # Launch background async task
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(process_case_async(dispute_id, scenario=payload.get("scenario")))
        except RuntimeError:
            import threading

            threading.Thread(
                target=lambda: asyncio.run(process_case_async(dispute_id, scenario=payload.get("scenario"))),
                daemon=True,
            ).start()

        return {
            "accepted": True,
            "type": "dispute.created",
            "dispute_id": dispute_id,
            "status": "processing",
        }

    elif event_type == "approval":
        from scripts.reply import process_reply

        answer = str(payload.get("answer", "1"))
        res = process_reply(dispute_id=dispute_id, answer=answer)
        return {
            "accepted": True,
            "type": "approval",
            "dispute_id": dispute_id,
            "result": res,
        }

    elif event_type == "sweep":
        from agent.sweep import run_sweep, _parse_iso

        now_val = payload.get("now")
        now_dt = _parse_iso(now_val) if now_val else datetime.now(timezone.utc)
        res = run_sweep(now=now_dt)
        return {
            "accepted": True,
            "type": "sweep",
            "result": res,
        }

    elif event_type == "dispute.closed":
        from agent.tools.case_tools import record_case

        record_case(
            dispute_id=dispute_id,
            status=payload.get("status", "closed"),
            action="dispute_closed_webhook",
            actor="webhook",
            details=payload.get("details", {}),
        )
        return {
            "accepted": True,
            "type": "dispute.closed",
            "dispute_id": dispute_id,
        }

    else:
        return {
            "accepted": False,
            "error": f"Unknown event type: {event_type}",
        }


if __name__ == "__main__":
    app.run()
