import os
import sys
import shutil
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Ensure metadata service fails fast if no credentials
os.environ.setdefault("AWS_METADATA_SERVICE_TIMEOUT", "1")
os.environ.setdefault("AWS_METADATA_SERVICE_NUM_ATTEMPTS", "1")

# Ensure User WinGet paths are visible in PATH on Windows
if sys.platform == "win32":
    local_app_data = os.getenv("LOCALAPPDATA", "")
    winget_stripe = os.path.join(
        local_app_data,
        "Microsoft",
        "WinGet",
        "Packages",
        "Stripe.StripeCli_Microsoft.Winget.Source_8wekyb3d8bbwe",
    )
    if os.path.exists(winget_stripe) and winget_stripe not in os.environ.get("PATH", ""):
        os.environ["PATH"] = winget_stripe + os.pathsep + os.environ.get("PATH", "")

# Load .env file
load_dotenv()

# Setup AWS profile default session if configured
aws_profile = os.getenv("AWS_PROFILE")
if aws_profile:
    try:
        import boto3
        boto3.setup_default_session(profile_name=aws_profile)
    except Exception:
        pass

def print_header(title: str):
    print(f"\n=== {title} ===", flush=True)

def main():
    print_header("Rebuttal Pre-Flight Verification (R-00)")
    
    proof_results = {}
    errors = []
    
    # -------------------------------------------------------------
    # 1. Python SDKs & Imports
    # -------------------------------------------------------------
    print("\n[1/8] Checking Python imports...", flush=True)
    try:
        import strands
        import bedrock_agentcore
        import stripe
        import twilio
        import supabase
        import boto3
        import pydantic
        import yaml
        import pytest
        print("  PASS: All required Python SDKs imported successfully.", flush=True)
        proof_results["python"] = "PASS"
    except Exception as e:
        print(f"  FAIL: Failed importing required Python SDKs: {e}", flush=True)
        proof_results["python"] = "FAIL"
        errors.append(f"Python imports failed: {e}")

    # -------------------------------------------------------------
    # 2. AWS Identity & Region
    # -------------------------------------------------------------
    print("\n[2/8] Checking AWS identity & region...", flush=True)
    region = os.getenv("AWS_REGION", "us-east-1")
    has_aws_creds = bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))
    aws_creds_file = Path.home() / ".aws" / "credentials"
    aws_config_file = Path.home() / ".aws" / "config"
    try:
        if not has_aws_creds and not aws_creds_file.exists() and not aws_config_file.exists():
            raise RuntimeError("AWS credentials / config not found.")
        import boto3
        sts = boto3.client("sts", region_name=region)
        caller = sts.get_caller_identity()
        arn = caller.get("Arn", "unknown")
        account = caller.get("Account", "unknown")
        print(f"  PASS: AWS identity verified. Account={account}, Region={region}, Arn={arn}", flush=True)
        proof_results["aws"] = "PASS"
    except Exception as e:
        print(f"  FAIL: AWS identity check failed: {e}", flush=True)
        proof_results["aws"] = "FAIL"
        errors.append(f"AWS identity failed: {e}")

    # -------------------------------------------------------------
    # 3. Bedrock Converse Call
    # -------------------------------------------------------------
    print("\n[3/8] Checking Bedrock Converse call...", flush=True)
    model_id = os.getenv("BEDROCK_MODEL_ID")
    if not model_id:
        print("  FAIL: BEDROCK_MODEL_ID is not set in environment.", flush=True)
        proof_results["bedrock"] = "FAIL"
        errors.append("BEDROCK_MODEL_ID not set")
    elif proof_results.get("aws") != "PASS":
        print("  FAIL: Skipped Bedrock Converse call because AWS identity check failed.", flush=True)
        proof_results["bedrock"] = "FAIL"
        errors.append("Bedrock Converse skipped due to AWS check failure")
    else:
        try:
            import boto3
            bedrock_rt = boto3.client("bedrock-runtime", region_name=region)
            resp = bedrock_rt.converse(
                modelId=model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": "Reply with 'OK'."}]
                    }
                ],
                inferenceConfig={"maxTokens": 10, "temperature": 0.0}
            )
            text_resp = resp["output"]["message"]["content"][0]["text"].strip()
            print(f"  PASS: Bedrock Converse succeeded on model {model_id}. Response: {text_resp}", flush=True)
            proof_results["bedrock"] = "PASS"
        except Exception as e:
            print(f"  FAIL: Bedrock Converse failed on model {model_id}: {e}", flush=True)
            proof_results["bedrock"] = "FAIL"
            errors.append(f"Bedrock Converse failed: {e}")

    # -------------------------------------------------------------
    # 4. Bedrock AgentCore Control Plane
    # -------------------------------------------------------------
    print("\n[4/8] Checking AgentCore control plane (list_agent_runtimes)...", flush=True)
    if proof_results.get("aws") != "PASS":
        print("  FAIL: Skipped AgentCore check because AWS identity check failed.", flush=True)
        proof_results["agentcore"] = "FAIL"
        errors.append("AgentCore check skipped due to AWS check failure")
    else:
        try:
            import boto3
            agentcore_ctrl = boto3.client("bedrock-agentcore-control", region_name=region)
            runtimes_resp = agentcore_ctrl.list_agent_runtimes(maxResults=10)
            runtimes = runtimes_resp.get("agentRuntimeSummaries", [])
            print(f"  PASS: AgentCore control plane reachable. Found {len(runtimes)} agent runtimes.", flush=True)
            proof_results["agentcore"] = "PASS"
        except Exception as e:
            print(f"  FAIL: AgentCore control plane check failed: {e}", flush=True)
            proof_results["agentcore"] = "FAIL"
            errors.append(f"AgentCore control plane failed: {e}")

    # -------------------------------------------------------------
    # 5. Stripe Key & Stripe CLI
    # -------------------------------------------------------------
    print("\n[5/8] Checking Stripe test key and Stripe CLI...", flush=True)
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_cli_ok = False
    stripe_api_ok = False

    # Check Stripe CLI
    stripe_cli_path = shutil.which("stripe")
    if stripe_cli_path:
        try:
            res = subprocess.run([stripe_cli_path, "version"], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                ver_line = res.stdout.strip().splitlines()[0] if res.stdout.strip() else "available"
                print(f"  PASS: Stripe CLI found: {ver_line}", flush=True)
                stripe_cli_ok = True
            else:
                print(f"  FAIL: Stripe CLI exited with code {res.returncode}", flush=True)
        except Exception as e:
            print(f"  FAIL: Stripe CLI execution failed: {e}", flush=True)
    else:
        print("  FAIL: Stripe CLI executable not found on PATH.", flush=True)

    # Live-key guard rule
    if not stripe_key:
        print("  FAIL: STRIPE_SECRET_KEY is not set in environment.", flush=True)
        errors.append("STRIPE_SECRET_KEY not set")
    elif not stripe_key.startswith("sk_test_"):
        print("  FAIL: Live-key guard failed: STRIPE_SECRET_KEY must start with 'sk_test_'.", flush=True)
        errors.append("Live-key guard: STRIPE_SECRET_KEY does not start with sk_test_")
    else:
        try:
            import stripe
            stripe.api_key = stripe_key
            balance = stripe.Balance.retrieve()
            print("  PASS: Stripe Balance.retrieve succeeded with test key.", flush=True)
            stripe_api_ok = True
        except Exception as e:
            print(f"  FAIL: Stripe API call failed: {e}", flush=True)
            errors.append(f"Stripe Balance.retrieve failed: {e}")

    if stripe_cli_ok and stripe_api_ok:
        proof_results["stripe"] = "PASS"
    else:
        proof_results["stripe"] = "FAIL"

    # -------------------------------------------------------------
    # 6. Twilio SMS
    # -------------------------------------------------------------
    print("\n[6/8] Checking Twilio SMS to OWNER_PHONE...", flush=True)
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_FROM")
    owner_phone = os.getenv("OWNER_PHONE")

    if not (account_sid and auth_token and from_phone and owner_phone):
        print("  FAIL: Twilio credentials or phone numbers missing in environment.", flush=True)
        proof_results["twilio"] = "FAIL"
        errors.append("Twilio configuration missing in .env")
    else:
        try:
            from twilio.rest import Client
            client = Client(account_sid, auth_token)
            msg = client.messages.create(
                body="Rebuttal preflight OK",
                from_=from_phone,
                to=owner_phone
            )
            print(f"  PASS: Twilio SMS sent to {owner_phone}. SID: {msg.sid}", flush=True)
            proof_results["twilio"] = f"PASS({msg.sid})"
        except Exception as e:
            print(f"  FAIL: Twilio SMS failed: {e}", flush=True)
            proof_results["twilio"] = "FAIL"
            errors.append(f"Twilio SMS failed: {e}")

    # -------------------------------------------------------------
    # 7. Supabase REST
    # -------------------------------------------------------------
    print("\n[7/8] Checking Supabase REST...", flush=True)
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not (supabase_url and supabase_key):
        print("  FAIL: SUPABASE_URL or SUPABASE_SERVICE_KEY missing in environment.", flush=True)
        proof_results["supabase"] = "FAIL"
        errors.append("Supabase configuration missing in .env")
    else:
        try:
            import requests
            headers = {
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}"
            }
            # Query OpenAPI spec endpoint on Supabase PostgREST
            rest_url = f"{supabase_url.rstrip('/')}/rest/v1/"
            resp = requests.get(rest_url, headers=headers, timeout=10)
            if resp.status_code in [200, 204]:
                print(f"  PASS: Supabase REST answered with service key (status {resp.status_code}).", flush=True)
                proof_results["supabase"] = "PASS"
            else:
                print(f"  FAIL: Supabase REST returned status {resp.status_code}: {resp.text[:100]}", flush=True)
                proof_results["supabase"] = "FAIL"
                errors.append(f"Supabase REST returned status {resp.status_code}")
        except Exception as e:
            print(f"  FAIL: Supabase REST request failed: {e}", flush=True)
            proof_results["supabase"] = "FAIL"
            errors.append(f"Supabase request failed: {e}")

    # -------------------------------------------------------------
    # 8. Google OAuth (WARN-only)
    # -------------------------------------------------------------
    print("\n[8/8] Checking Google OAuth (WARN-only)...", flush=True)
    g_client_id = os.getenv("GOOGLE_CLIENT_ID")
    g_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    g_refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")

    if g_client_id and g_client_secret and g_refresh_token:
        try:
            import requests
            token_resp = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": g_client_id,
                    "client_secret": g_client_secret,
                    "refresh_token": g_refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=10
            )
            if token_resp.status_code == 200:
                print("  PASS: Google OAuth refresh token verified.", flush=True)
                proof_results["google"] = "PASS"
            else:
                print(f"  WARN: Google OAuth token refresh returned {token_resp.status_code} (not required for core path).", flush=True)
                proof_results["google"] = "WARN"
        except Exception as e:
            print(f"  WARN: Google OAuth check error: {e} (not required for core path).", flush=True)
            proof_results["google"] = "WARN"
    else:
        print("  WARN: Google OAuth credentials not set (needed only by S-A stretch).", flush=True)
        proof_results["google"] = "WARN"

    # -------------------------------------------------------------
    # Summary & Proof Line
    # -------------------------------------------------------------
    print_header("Pre-Flight Summary")
    proof_line = (
        f"PROOF R-00: "
        f"aws={proof_results.get('aws', 'FAIL')} "
        f"bedrock={proof_results.get('bedrock', 'FAIL')} "
        f"agentcore={proof_results.get('agentcore', 'FAIL')} "
        f"stripe={proof_results.get('stripe', 'FAIL')} "
        f"twilio={proof_results.get('twilio', 'FAIL')} "
        f"supabase={proof_results.get('supabase', 'FAIL')} "
        f"python={proof_results.get('python', 'FAIL')} "
        f"google={proof_results.get('google', 'WARN')}"
    )
    print(f"\n{proof_line}\n", flush=True)

    # Record proof to docs/proofs/R-00.md
    docs_dir = Path("docs/proofs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    proof_file = docs_dir / "R-00.md"
    
    with open(proof_file, "a", encoding="utf-8") as f:
        f.write(f"{proof_line}\n")
    print(f"Recorded proof to {proof_file}", flush=True)

    all_passed = (
        proof_results.get("aws") == "PASS" and
        proof_results.get("bedrock") == "PASS" and
        proof_results.get("agentcore") == "PASS" and
        proof_results.get("stripe") == "PASS" and
        str(proof_results.get("twilio", "")).startswith("PASS") and
        proof_results.get("supabase") == "PASS" and
        proof_results.get("python") == "PASS"
    )

    if not all_passed:
        print(f"\nFAILED: {len(errors)} checks did not pass.", flush=True)
        for err in errors:
            print(f" - {err}", flush=True)
        sys.exit(1)
    else:
        print("\nSUCCESS: All required pre-flight checks PASSED.", flush=True)
        sys.exit(0)

if __name__ == "__main__":
    main()
