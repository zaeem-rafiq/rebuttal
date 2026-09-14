"""Persist a Stripe dispute before its decisions and audit events reference it."""

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _stripe_id(value: Any) -> str | None:
    return value.get("id") if isinstance(value, dict) else value or None


def _utc_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Stripe timestamps must be Unix seconds")
    return datetime.fromtimestamp(value, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ingest_stripe_dispute(
    dispute: dict[str, Any], db_path: Path, *, supabase_client: Any = None
) -> dict[str, Any]:
    """Upsert a retrieved TEST dispute and return its actual execution context.

    ``get_dispute`` expands charge and payment_intent, whose metadata can link a
    new dispute to an existing order even when dispute.metadata is empty. A
    configured cloud write must succeed before the caller runs the agent.
    """
    if dispute.get("livemode") is not False:
        raise ValueError("Dispute ingress requires a Stripe TEST record")
    dispute_id = dispute.get("id")
    if not isinstance(dispute_id, str) or not dispute_id.startswith(("du_", "dp_")):
        raise ValueError("Dispute ingress requires a Stripe dispute ID")
    amount = dispute.get("amount")
    if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
        raise ValueError("Dispute amount must be a non-negative integer")
    for field in ("currency", "reason", "status"):
        if not isinstance(dispute.get(field), str) or not dispute[field]:
            raise ValueError(f"Dispute {field} is required")
    created_at = _utc_timestamp(dispute.get("created"))
    if created_at is None:
        raise ValueError("Dispute creation time is required")

    charge = dispute.get("charge")
    payment_intent = dispute.get("payment_intent")
    metadata: dict[str, Any] = {}
    order_links = set()
    for source in (charge, payment_intent, dispute):
        if isinstance(source, dict) and isinstance(source.get("metadata"), dict):
            source_metadata = source["metadata"]
            order_link = source_metadata.get("order_id")
            if order_link is not None:
                if not isinstance(order_link, str):
                    raise ValueError("Stripe order identifiers must be strings")
                if order_link.strip():
                    order_links.add(order_link.strip())
            metadata.update(source_metadata)
    if len(order_links) > 1:
        raise ValueError("Conflicting Stripe order identifiers")
    if order_links:
        metadata["order_id"] = next(iter(order_links))
    charge_id = _stripe_id(charge)
    payment_intent_id = _stripe_id(payment_intent)
    if not payment_intent_id and isinstance(charge, dict):
        payment_intent_id = _stripe_id(charge.get("payment_intent"))

    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        order_id = metadata.get("order_id")
        if order_id:
            order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        else:
            orders = conn.execute(
                "SELECT * FROM orders WHERE payment_intent_id = ? OR charge_id = ?",
                (payment_intent_id, charge_id),
            ).fetchall()
            order = orders[0] if len(orders) == 1 else None
        if order is None:
            raise ValueError("Stripe dispute must resolve to one existing order")

        metadata["order_id"] = order["id"]
        metadata["stripe_dispute_id"] = dispute_id
        record = {
            "id": dispute_id,
            "order_id": order["id"],
            "payment_intent_id": payment_intent_id,
            "charge_id": charge_id,
            "amount_cents": amount,
            "currency": dispute["currency"],
            "reason": dispute["reason"],
            "status": dispute["status"],
            "evidence_due_by": _utc_timestamp((dispute.get("evidence_details") or {}).get("due_by")),
            "metadata": metadata,
            "created_at": created_at,
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        columns = tuple(record)
        updates = ", ".join(f"{name}=excluded.{name}" for name in columns if name not in {"id", "created_at"})
        values = [json.dumps(value) if name == "metadata" else value for name, value in record.items()]
        conn.execute(
            f"INSERT INTO disputes ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)}) "
            f"ON CONFLICT(id) DO UPDATE SET {updates}",
            values,
        )
        if supabase_client is not None:
            # Do not swallow a missing cloud parent: ApprovalGate depends on it.
            supabase_client.table("disputes").upsert(record, on_conflict="id").execute()

    return {
        "dispute_id": dispute_id,
        "order_id": order["id"],
        "customer_id": order["customer_id"],
        "amount_cents": amount,
        "currency": dispute["currency"],
        "reason": dispute["reason"],
        "scenario": metadata.get("scenario"),
    }
