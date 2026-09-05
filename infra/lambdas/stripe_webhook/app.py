import json
import os
import hmac
import hashlib
import time
import base64
import logging
import uuid
import urllib.request
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AGENT_RUNTIME_ARN = os.environ.get(
    "AGENT_RUNTIME_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:292341338711:runtime/rebuttal-pASUe6CVmu"
)
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
AWS_REGION_NAME = os.environ.get("AWS_REGION_NAME", os.environ.get("AWS_REGION", "us-east-1"))


def verify_stripe_signature(payload_bytes: bytes, sig_header: str, secret: str) -> bool:
    """Verify Stripe-Signature header using HMAC-SHA256."""
    if not secret or not sig_header:
        # In test / sandbox environments without secret, accept with warning
        logger.warning("Stripe signature verification skipped: secret or header missing")
        return True

    try:
        elements = sig_header.split(",")
        timestamp = None
        signatures = []
        for element in elements:
            parts = element.strip().split("=", 1)
            if len(parts) == 2:
                key, val = parts
                if key == "t":
                    timestamp = val
                elif key == "v1":
                    signatures.append(val)

        if not timestamp or not signatures:
            return False

        # Tolerance check: 10 minutes
        current_time = int(time.time())
        if abs(current_time - int(timestamp)) > 600:
            logger.warning("Stripe signature timestamp out of tolerance: %s vs %s", timestamp, current_time)
            return False

        signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
        expected_sig = hmac.new(
            secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256
        ).hexdigest()

        for sig in signatures:
            if hmac.compare_digest(expected_sig, sig):
                return True

        return False
    except Exception as e:
        logger.error("Error verifying Stripe signature: %s", e)
        return False


def invoke_bedrock_runtime(payload_dict: dict, session_id: str) -> dict:
    """Invoke Bedrock AgentCore Runtime."""
    client = boto3.client("bedrock-agentcore", region_name=AWS_REGION_NAME)
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    
    logger.info("Invoking AgentCore runtime ARN=%s session=%s payload=%s",
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
    """Handle incoming Stripe webhook POST requests."""
    logger.info("Received event: %s", json.dumps({k: v for k, v in event.items() if k != "body"}))
    
    # Handle base64 body if sent by Function URL / API Gateway
    body = event.get("body", "")
    is_base64 = event.get("isBase64Encoded", False)
    if is_base64:
        raw_bytes = base64.b64decode(body)
    elif isinstance(body, str):
        raw_bytes = body.encode("utf-8")
    else:
        raw_bytes = body

    # Extract headers (case-insensitive)
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    sig_header = headers.get("stripe-signature", "")

    # Validate signature if secret configured
    if STRIPE_WEBHOOK_SECRET and not verify_stripe_signature(raw_bytes, sig_header, STRIPE_WEBHOOK_SECRET):
        logger.error("Stripe signature verification failed")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid signature"})
        }

    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except Exception as e:
        logger.error("Invalid JSON payload: %s", e)
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid JSON body"})
        }

    event_type = payload.get("type", "")
    data_obj = payload.get("data", {}).get("object", {})
    logger.info("Processing Stripe event type: %s", event_type)

    dispatched = False
    runtime_response = None

    if event_type == "charge.dispute.created":
        dispute_id = data_obj.get("id")
        amount = data_obj.get("amount")
        # Metadata or description may indicate scenario
        metadata = data_obj.get("metadata") or {}
        scenario = metadata.get("scenario")
        if not scenario:
            if amount == 34000:
                scenario = "S2"
            elif amount == 4800:
                scenario = "S1"
            elif amount == 12900:
                scenario = "S3"

        session_id = f"rebuttal-{dispute_id}-{uuid.uuid4().hex}"
        
        runtime_payload = {
            "type": "dispute.created",
            "dispute_id": dispute_id,
        }
        if scenario:
            runtime_payload["scenario"] = scenario

        runtime_response = invoke_bedrock_runtime(runtime_payload, session_id)
        dispatched = True

    elif event_type == "charge.dispute.closed":
        dispute_id = data_obj.get("id")
        status = data_obj.get("status", "lost")
        reason = data_obj.get("reason", "product_not_received")
        amount = data_obj.get("amount", 0)
        session_id = f"rebuttal-{dispute_id}-{uuid.uuid4().hex}"

        runtime_payload = {
            "type": "dispute.closed",
            "dispute_id": dispute_id,
            "status": status,
            "reason": reason,
            "amount": amount,
        }
        runtime_response = invoke_bedrock_runtime(runtime_payload, session_id)
        dispatched = True

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "received": True,
            "event_type": event_type,
            "dispatched": dispatched,
            "runtime_response": runtime_response
        })
    }
