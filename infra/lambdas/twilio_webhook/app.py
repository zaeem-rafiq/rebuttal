import json
import os
import hmac
import hashlib
import base64
import logging
import uuid
import urllib.parse
import urllib.request
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AGENT_RUNTIME_ARN = os.environ.get(
    "AGENT_RUNTIME_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:292341338711:runtime/rebuttal-pASUe6CVmu"
)
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ygcmdhmoqvafxrqyqnqv.supabase.co")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
OWNER_PHONE = os.environ.get("OWNER_PHONE", "")
AWS_REGION_NAME = os.environ.get("AWS_REGION_NAME", os.environ.get("AWS_REGION", "us-east-1"))


def validate_twilio_signature(url: str, params: dict, expected_sig: str, auth_token: str) -> bool:
    """Validate Twilio X-Twilio-Signature using standard HMAC-SHA1."""
    if not auth_token or not expected_sig:
        logger.warning("Twilio signature validation skipped: auth_token or signature missing")
        return True

    try:
        # Build signature string: URL followed by sorted key-value pairs
        s = url
        for key in sorted(params.keys()):
            s += f"{key}{params[key]}"

        mac = hmac.new(auth_token.encode("utf-8"), s.encode("utf-8"), hashlib.sha1)
        computed_sig = base64.b64encode(mac.digest()).decode("utf-8")
        return hmac.compare_digest(computed_sig, expected_sig)
    except Exception as e:
        logger.error("Error validating Twilio signature: %s", e)
        return False


def parse_reply_answer(body_text: str) -> str:
    """Parse user reply text (1|2|3|fight|concede|hold) into standardized answer code."""
    cleaned = (body_text or "").strip().lower()
    if cleaned in ("1", "fight", "1. fight", "1 - fight"):
        return "1"
    elif cleaned in ("2", "concede", "2. concede", "2 - concede"):
        return "2"
    elif cleaned in ("3", "hold", "3. hold", "3 - hold"):
        return "3"
    
    # Try finding first digit
    for ch in cleaned:
        if ch in ("1", "2", "3"):
            return ch

    # Default to 1 (fight) if unrecognized per silence/default rules
    return "1"


def query_latest_pending_decision(from_phone: str) -> str:
    """Find latest pending decision from Supabase REST API."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.warning("Supabase credentials not set, using fallback dispute dp_S2")
        return "dp_S2"

    try:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Accept": "application/json"
        }
        
        # 1. Query pending decisions (by status or answered_at)
        for q in [
            "status=eq.pending&order=created_at.desc&limit=1",
            "answered_at=is.null&order=sent_at.desc&limit=1",
            "answered_at=is.null&order=created_at.desc&limit=1"
        ]:
            decisions_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/decisions?{q}"
            try:
                req = urllib.request.Request(decisions_url, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data and isinstance(data, list) and len(data) > 0:
                        dispute_id = data[0].get("dispute_id")
                        if dispute_id:
                            logger.info("Found pending decision for dispute: %s", dispute_id)
                            return dispute_id
            except Exception:
                pass

        # 2. Query open disputes needs_response
        disputes_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/disputes?status=eq.needs_response&order=created_at.desc&limit=1"
        req2 = urllib.request.Request(disputes_url, headers=headers, method="GET")
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            data2 = json.loads(resp2.read().decode("utf-8"))
            if data2 and isinstance(data2, list) and len(data2) > 0:
                dispute_id = data2[0].get("id")
                if dispute_id:
                    logger.info("Found open needs_response dispute: %s", dispute_id)
                    return dispute_id

    except Exception as e:
        logger.error("Error querying Supabase: %s", e)

    # Fallback to S2
    return "dp_S2"


def invoke_bedrock_approval(dispute_id: str, answer: str) -> dict:
    """Invoke Bedrock AgentCore Runtime with approval action."""
    client = boto3.client("bedrock-agentcore", region_name=AWS_REGION_NAME)
    session_id = f"rebuttal-{dispute_id}-{uuid.uuid4().hex}"
    
    payload_dict = {
        "type": "approval",
        "dispute_id": dispute_id,
        "answer": answer
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    
    logger.info("Invoking AgentCore approval ARN=%s session=%s payload=%s",
                AGENT_RUNTIME_ARN, session_id, payload_dict)
    
    resp = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        runtimeSessionId=session_id,
        qualifier="DEFAULT",
        contentType="application/json",
        accept="application/json",
        payload=payload_bytes
    )
    
    body = resp["response"].read().decode("utf-8")
    try:
        return json.loads(body)
    except Exception:
        return {"raw": body}


def lambda_handler(event, context):
    """Handle incoming Twilio messaging webhook POST requests."""
    logger.info("Received event: %s", json.dumps({k: v for k, v in event.items() if k != "body"}))
    
    # Handle base64 body if sent by Function URL
    body = event.get("body", "")
    is_base64 = event.get("isBase64Encoded", False)
    if is_base64:
        raw_str = base64.b64decode(body).decode("utf-8", errors="replace")
    elif isinstance(body, str):
        raw_str = body
    else:
        raw_str = ""

    # Parse URL-encoded form parameters
    form_params = urllib.parse.parse_qs(raw_str)
    # Convert list values to single string
    params = {k: v[0] for k, v in form_params.items() if v}

    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    twilio_sig = headers.get("x-twilio-signature", "")
    custom_secret = headers.get("x-rebuttal-secret", "")

    # Check custom secret or Twilio signature
    if TWILIO_AUTH_TOKEN and twilio_sig:
        # Reconstruct URL from requestContext or headers
        request_context = event.get("requestContext", {})
        http_info = request_context.get("http", {})
        domain = request_context.get("domainName", headers.get("host", ""))
        path = http_info.get("path", event.get("rawPath", "/"))
        url = f"https://{domain}{path}"
        
        is_valid = validate_twilio_signature(url, params, twilio_sig, TWILIO_AUTH_TOKEN)
        if not is_valid and custom_secret != TWILIO_AUTH_TOKEN:
            logger.warning("Twilio signature validation failed for URL=%s. Checking shared secret fallback.", url)
            # Fallback to shared secret check if configured per ADR-003 notes
            if custom_secret and custom_secret != TWILIO_AUTH_TOKEN:
                return {
                    "statusCode": 403,
                    "headers": {"Content-Type": "text/plain"},
                    "body": "Forbidden: Invalid signature"
                }

    message_body = params.get("Body", "")
    from_phone = params.get("From", "")
    logger.info("Inbound Twilio SMS from=%s body='%s'", from_phone, message_body)

    answer = parse_reply_answer(message_body)
    dispute_id = params.get("DisputeId") or params.get("dispute_id") or query_latest_pending_decision(from_phone)

    logger.info("Dispatching approval answer=%s for dispute=%s", answer, dispute_id)
    runtime_res = invoke_bedrock_approval(dispute_id, answer)
    logger.info("AgentCore approval response: %s", runtime_res)

    twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Got it</Message>
</Response>"""

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/xml"
        },
        "body": twiml_response
    }
