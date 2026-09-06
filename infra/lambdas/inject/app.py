import json
import os
import time
import urllib.request
import urllib.parse
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
CONSOLE_KEY = os.environ.get("CONSOLE_KEY", "rebuttal-judge-console-key-2026")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

LAST_INJECT_TIME = 0.0
TIMESTAMP_FILE = "/tmp/last_inject.txt"

SCENARIO_CONFIG = {
    "S1": {
        "order_id": "ORD-1001",
        "amount_cents": 4800,
        "payment_method": "pm_card_createDisputeProductNotReceived",
        "reason": "product_not_received",
    },
    "S2": {
        "order_id": "ORD-1002",
        "amount_cents": 34000,
        "payment_method": "pm_card_createDispute",
        "reason": "fraudulent",
    },
    "S3": {
        "order_id": "ORD-1003",
        "amount_cents": 12900,
        "payment_method": "pm_card_createDisputeInquiry",
        "reason": "subscription_canceled",
    },
}

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Console-Key,x-console-key",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
    "Content-Type": "application/json",
}


def get_last_inject_time() -> float:
    global LAST_INJECT_TIME
    if LAST_INJECT_TIME > 0:
        return LAST_INJECT_TIME
    if os.path.exists(TIMESTAMP_FILE):
        try:
            with open(TIMESTAMP_FILE, "r") as f:
                ts = float(f.read().strip())
                LAST_INJECT_TIME = ts
                return ts
        except Exception:
            pass
    return 0.0


def record_inject_time(ts: float):
    global LAST_INJECT_TIME
    LAST_INJECT_TIME = ts
    try:
        with open(TIMESTAMP_FILE, "w") as f:
            f.write(str(ts))
    except Exception as e:
        logger.warning("Failed to write timestamp to file: %s", e)


def lambda_handler(event, context):
    http_method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "")
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"status": "ok"}),
        }

    headers = event.get("headers", {}) or {}
    provided_key = None
    for k, v in headers.items():
        if k.lower() == "x-console-key":
            provided_key = v
            break

    if not provided_key or provided_key != CONSOLE_KEY:
        logger.warning("Unauthorized inject attempt: provided_key=%s", bool(provided_key))
        return {
            "statusCode": 401,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Unauthorized: invalid or missing X-Console-Key"}),
        }

    now = time.time()
    last_time = get_last_inject_time()
    elapsed = now - last_time
    if elapsed < 60.0:
        remaining = int(60.0 - elapsed)
        logger.warning("Rate limit exceeded: %d seconds remaining", remaining)
        return {
            "statusCode": 429,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "error": "Rate limit exceeded. Maximum 1 inject per 60 seconds.",
                "retry_after_seconds": remaining,
            }),
        }

    if not STRIPE_SECRET_KEY or not STRIPE_SECRET_KEY.startswith("sk_test_"):
        logger.error("Live-key guard triggered or STRIPE_SECRET_KEY missing")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Live-key guard: STRIPE_SECRET_KEY must start with sk_test_"}),
        }

    body_str = event.get("body", "{}") or "{}"
    if event.get("isBase64Encoded", False):
        import base64
        body_str = base64.b64decode(body_str).decode("utf-8")

    try:
        data = json.loads(body_str) if body_str else {}
    except Exception:
        data = {}

    scenario = (data.get("scenario") or "S1").upper().strip()
    if scenario not in SCENARIO_CONFIG:
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Invalid scenario: {scenario}. Must be S1, S2, or S3"}),
        }

    cfg = SCENARIO_CONFIG[scenario]

    try:
        stripe_url = "https://api.stripe.com/v1/payment_intents"
        form_data = {
            "amount": str(cfg["amount_cents"]),
            "currency": "usd",
            "payment_method": cfg["payment_method"],
            "confirm": "true",
            "automatic_payment_methods[enabled]": "true",
            "automatic_payment_methods[allow_redirects]": "never",
            "metadata[order_id]": cfg["order_id"],
            "metadata[scenario]": scenario,
        }
        encoded_data = urllib.parse.urlencode(form_data).encode("utf-8")
        req = urllib.request.Request(
            stripe_url,
            data=encoded_data,
            headers={
                "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            stripe_resp = json.loads(resp.read().decode("utf-8"))
            pi_id = stripe_resp.get("id")
            logger.info("Stripe PaymentIntent created: %s for scenario %s", pi_id, scenario)

    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        logger.error("Stripe API error (%d): %s", e.code, err_body)
        return {
            "statusCode": 502,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Stripe API error: {err_body}"}),
        }
    except Exception as e:
        logger.error("Failed to create Stripe PaymentIntent: %s", e)
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Internal error: {str(e)}"}),
        }

    record_inject_time(now)

    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        try:
            update_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/orders?id=eq.{cfg['order_id']}"
            update_body = json.dumps({"payment_intent_id": pi_id}).encode("utf-8")
            sb_req = urllib.request.Request(
                update_url,
                data=update_body,
                headers={
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                method="PATCH",
            )
            with urllib.request.urlopen(sb_req, timeout=5) as sb_resp:
                logger.info("Supabase order %s updated with PI %s (status %d)", cfg["order_id"], pi_id, sb_resp.status)
        except Exception as e:
            logger.warning("Could not update Supabase order: %s", e)

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": json.dumps({
            "success": True,
            "scenario": scenario,
            "payment_intent_id": pi_id,
            "order_id": cfg["order_id"],
            "amount_cents": cfg["amount_cents"],
            "reason": cfg["reason"],
            "message": f"Successfully injected {scenario}. Webhook will trigger Rebuttal agent.",
        }),
    }
