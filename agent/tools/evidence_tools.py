"""agent/tools/evidence_tools.py

Tools for evidence gathering agents to retrieve order data, shipping/delivery details,
customer communication history, and merchant policy from the database.
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from strands import tool

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_DB_PATH = REPO_ROOT / "data" / "local_supabase.db"


def _get_db_connection() -> sqlite3.Connection:
    """Obtain a SQLite connection to the local database with row factory."""
    if not LOCAL_DB_PATH.exists():
        raise FileNotFoundError(f"Database file not found at {LOCAL_DB_PATH}")
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@tool
def get_order_evidence(order_id: str) -> Dict[str, Any]:
    """Retrieve full order details, line items, card check indicators, and customer billing/shipping details.

    Parameters:
        order_id: Order identifier (e.g. 'ORD-1001').

    Returns:
        Dictionary with order summary, customer info, line items, and card verification results.
    """
    clean_id = order_id.strip()
    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        order_row = cur.execute("SELECT * FROM orders WHERE id = ?", (clean_id,)).fetchone()
        if not order_row:
            return {"error": f"Order {clean_id} not found."}
        
        order = dict(order_row)
        for json_col in ["shipping_address", "billing_address"]:
            if isinstance(order.get(json_col), str):
                try:
                    order[json_col] = json.loads(order[json_col])
                except Exception:
                    pass

        # Fetch order items
        items_rows = cur.execute("SELECT * FROM order_items WHERE order_id = ?", (clean_id,)).fetchall()
        order["items"] = [dict(r) for r in items_rows]

        # Fetch customer info
        cust_row = cur.execute("SELECT * FROM customers WHERE id = ?", (order["customer_id"],)).fetchone()
        if cust_row:
            cust = dict(cust_row)
            order["customer_name"] = cust.get("name")
            order["customer_email"] = cust.get("email")
            order["customer_phone"] = cust.get("phone")
            order["customer_value"] = cust.get("customer_value", "new")
            order["order_count"] = cust.get("order_count", 1)
            order["lifetime_value_cents"] = cust.get("lifetime_value_cents", order.get("amount_cents", 0))

        return order
    finally:
        conn.close()


@tool
def get_shipping_evidence(order_id: str) -> Dict[str, Any]:
    """Retrieve fulfillment and delivery tracking information, carrier timestamps, and signature confirmation.

    Parameters:
        order_id: Order identifier (e.g. 'ORD-1001').

    Returns:
        Dictionary containing carrier, tracking number, ship date, delivery date, signature name, and tracking history.
    """
    clean_id = order_id.strip()
    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        shipment_row = cur.execute("SELECT * FROM shipments WHERE order_id = ?", (clean_id,)).fetchone()
        if not shipment_row:
            return {"error": f"No shipment found for order {clean_id}."}

        shipment = dict(shipment_row)
        if isinstance(shipment.get("shipping_address"), str):
            try:
                shipment["shipping_address"] = json.loads(shipment["shipping_address"])
            except Exception:
                pass

        # Fetch tracking timeline events
        events_rows = cur.execute(
            "SELECT * FROM shipment_events WHERE shipment_id = ? ORDER BY timestamp ASC",
            (shipment["id"],)
        ).fetchall()
        shipment["events"] = [dict(r) for r in events_rows]
        return shipment
    finally:
        conn.close()


@tool
def get_customer_comms(customer_id: str, order_id: str = "") -> Dict[str, Any]:
    """Retrieve communication threads, inquiries, cancellations, or address change requests from the customer.

    Parameters:
        customer_id: Customer ID (e.g. 'CUST-001').
        order_id: Optional order ID filter.

    Returns:
        Dictionary with list of messages, plus boolean flags:
        has_cancellation_request, has_address_change_request, has_inquiry.
    """
    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        query = "SELECT * FROM customer_messages WHERE customer_id = ?"
        params = [customer_id.strip()]
        if order_id.strip():
            query += " AND (order_id = ? OR order_id IS NULL)"
            params.append(order_id.strip())
        query += " ORDER BY created_at ASC"

        rows = cur.execute(query, tuple(params)).fetchall()
        messages = [dict(r) for r in rows]

        has_cancellation = any("cancel" in (m.get("subject", "") + m.get("body", "")).lower() for m in messages)
        has_address_change = any(m.get("has_shipping_change", 0) == 1 for m in messages)
        has_inquiry = len(messages) > 0

        return {
            "customer_id": customer_id,
            "order_id": order_id,
            "messages": messages,
            "message_count": len(messages),
            "has_cancellation_request": has_cancellation,
            "has_address_change_request": has_address_change,
            "has_inquiry": has_inquiry,
        }
    finally:
        conn.close()


@tool
def get_merchant_history_and_policy(customer_id: str, merchant_id: str = "default") -> Dict[str, Any]:
    """Retrieve merchant policy parameters, customer lifetime history, and previous dispute records.

    Parameters:
        customer_id: Customer identifier to assess repeat/VIP standing.
        merchant_id: Merchant identifier.

    Returns:
        Dictionary with merchant policy thresholds, customer tier, prior dispute counts, and prior orders.
    """
    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        # Fetch policy
        policy_row = cur.execute("SELECT * FROM merchant_policy LIMIT 1").fetchone()
        policy = dict(policy_row) if policy_row else {
            "approval_amount_cents": 20000,
            "min_win_probability_to_fight": 0.50,
            "always_concede_under_cents": 1500,
            "vip_concede_max_cents": 50000,
            "silence_action": "fight"
        }

        # Fetch customer stats
        cust_row = cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id.strip(),)).fetchone()
        customer = dict(cust_row) if cust_row else {}

        # Prior orders for this customer
        prior_orders = cur.execute(
            "SELECT id, amount_cents, status, created_at FROM orders WHERE customer_id = ?",
            (customer_id.strip(),)
        ).fetchall()

        # Prior disputes
        prior_disputes = cur.execute(
            "SELECT d.* FROM disputes d JOIN orders o ON d.order_id = o.id WHERE o.customer_id = ?",
            (customer_id.strip(),)
        ).fetchall()

        return {
            "policy": policy,
            "customer_tier": customer.get("customer_value", "new"),
            "order_count": customer.get("order_count", len(prior_orders)),
            "lifetime_value_cents": customer.get("lifetime_value_cents", sum(r["amount_cents"] for r in prior_orders)),
            "prior_disputes_count": len(prior_disputes),
            "prior_orders": [dict(r) for r in prior_orders]
        }
    finally:
        conn.close()
