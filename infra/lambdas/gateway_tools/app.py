"""
infra/lambdas/gateway_tools/app.py

Lambda target function for Bedrock AgentCore Gateway (MCP).
Exposes `lookup_order` and `get_tracking` backed by Supabase REST API.
"""

import json
import os
import urllib.parse
import urllib.request
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ygcmdhmoqvafxrqyqnqv.supabase.co")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def _supabase_get(endpoint: str) -> list:
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{endpoint}"
    req = urllib.request.Request(
        url,
        headers={
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def lookup_order(order_id: str) -> dict:
    if not order_id:
        return {"error": "Missing order_id parameter."}
    clean_id = order_id.strip()
    orders = _supabase_get(f"orders?id=eq.{urllib.parse.quote(clean_id)}&select=*")
    if not orders:
        return {"error": f"Order {clean_id} not found."}

    order = orders[0]
    for json_col in ["shipping_address", "billing_address"]:
        if isinstance(order.get(json_col), str):
            try:
                order[json_col] = json.loads(order[json_col])
            except Exception:
                pass

    # Fetch items
    items = _supabase_get(f"order_items?order_id=eq.{urllib.parse.quote(clean_id)}&select=*")
    order["items"] = items

    # Fetch customer
    customer_id = order.get("customer_id")
    if customer_id:
        customers = _supabase_get(f"customers?id=eq.{urllib.parse.quote(customer_id)}&select=*")
        if customers:
            cust = customers[0]
            order["customer_name"] = cust.get("name")
            order["customer_email"] = cust.get("email")
            order["customer_phone"] = cust.get("phone")
            order["customer_value"] = cust.get("customer_value", "new")
            order["order_count"] = cust.get("order_count", 1)
            order["lifetime_value_cents"] = cust.get("lifetime_value_cents", order.get("amount_cents", 0))

    return order


def get_tracking(order_id: str = None, tracking_number: str = None) -> dict:
    shipments = []
    if order_id:
        clean_order_id = order_id.strip()
        shipments = _supabase_get(f"shipments?order_id=eq.{urllib.parse.quote(clean_order_id)}&select=*")
    elif tracking_number:
        clean_tracking = tracking_number.strip()
        shipments = _supabase_get(f"shipments?tracking_number=eq.{urllib.parse.quote(clean_tracking)}&select=*")

    if not shipments:
        return {"error": f"No shipment found for {order_id or tracking_number}."}

    shipment = shipments[0]
    for json_col in ["shipping_address", "tracking_events"]:
        if isinstance(shipment.get(json_col), str):
            try:
                shipment[json_col] = json.loads(shipment[json_col])
            except Exception:
                pass

    return shipment


def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event) if isinstance(event, dict) else event)

    tool_name = "unknown"
    if hasattr(context, "client_context") and context.client_context and hasattr(context.client_context, "custom"):
        tool_name = context.client_context.custom.get("bedrockAgentCoreToolName", "unknown")

    # Fallback to inspect event
    if tool_name == "unknown" and isinstance(event, dict):
        tool_name = event.get("bedrockAgentCoreToolName") or event.get("toolName") or event.get("name") or "unknown"

    logger.info("Executing tool: %s", tool_name)

    # Extract args
    args = event
    if isinstance(event, dict):
        if "arguments" in event and isinstance(event["arguments"], dict):
            args = event["arguments"]
        elif "input" in event and isinstance(event["input"], dict):
            args = event["input"]
        elif "parameters" in event and isinstance(event["parameters"], dict):
            args = event["parameters"]

    order_id = args.get("order_id") if isinstance(args, dict) else None
    tracking_number = args.get("tracking_number") if isinstance(args, dict) else None

    # Handle based on tool_name or available parameters
    if "lookup_order" in tool_name or (order_id and not tracking_number and "get_tracking" not in tool_name):
        res = lookup_order(order_id)
    elif "get_tracking" in tool_name or tracking_number:
        res = get_tracking(order_id=order_id, tracking_number=tracking_number)
    else:
        # Default attempt lookup_order if order_id is present
        if order_id:
            res = lookup_order(order_id)
        else:
            res = {"error": f"Unknown tool or missing arguments: tool={tool_name}"}

    return {
        "statusCode": 200,
        "body": json.dumps(res),
    }
