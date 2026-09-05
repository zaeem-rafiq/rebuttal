#!/usr/bin/env python3
"""
scripts/seed_supabase.py

Idempotent seed script for Rebuttal synthetic world.
Loads fixtures from data/fixtures/ and seeds either Supabase REST (if configured)
or local SQLite database (for offline local development and test runs).

Usage:
    python scripts/seed_supabase.py [--reset] [--verify] [--local-only]
"""

import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
LOCAL_DB_PATH = REPO_ROOT / "data" / "local_supabase.db"
PROOF_PATH = REPO_ROOT / "docs" / "proofs" / "R-01.md"


def load_fixture(name: str) -> list[dict]:
    """Load JSON fixture by name (e.g. 'customers' -> data/fixtures/customers.json)."""
    file_path = FIXTURES_DIR / f"{name}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------------------------------------------------------
# Local SQLite fallback implementation
# -----------------------------------------------------------------------------
SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    shipping_address TEXT NOT NULL DEFAULT '{}',
    billing_address TEXT NOT NULL DEFAULT '{}',
    customer_value TEXT NOT NULL DEFAULT 'new',
    order_count INTEGER NOT NULL DEFAULT 0,
    lifetime_value_cents INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    amount_cents INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'usd',
    status TEXT NOT NULL DEFAULT 'processing',
    payment_intent_id TEXT,
    charge_id TEXT,
    card_brand TEXT,
    card_last4 TEXT,
    avs_postal_match TEXT DEFAULT 'match',
    cvc_match TEXT DEFAULT 'match',
    shipping_address TEXT NOT NULL DEFAULT '{}',
    billing_address TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_name TEXT NOT NULL,
    sku TEXT,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price_cents INTEGER NOT NULL,
    total_price_cents INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS shipments (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    carrier TEXT NOT NULL,
    tracking_number TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'label_created',
    shipped_at TEXT NOT NULL,
    delivered_at TEXT,
    signed_by TEXT,
    shipping_address TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS shipment_events (
    id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    timestamp TEXT NOT NULL,
    status TEXT NOT NULL,
    location TEXT,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS customer_messages (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    order_id TEXT REFERENCES orders(id) ON DELETE SET NULL,
    direction TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'email',
    subject TEXT,
    body TEXT NOT NULL,
    has_shipping_change INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS disputes (
    id TEXT PRIMARY KEY,
    order_id TEXT REFERENCES orders(id) ON DELETE SET NULL,
    payment_intent_id TEXT,
    charge_id TEXT,
    amount_cents INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'usd',
    reason TEXT NOT NULL,
    status TEXT NOT NULL,
    evidence_due_by TEXT,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    dispute_id TEXT NOT NULL REFERENCES disputes(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    win_probability REAL NOT NULL DEFAULT 0.0,
    expected_value_cents INTEGER NOT NULL DEFAULT 0,
    evidence_strength TEXT NOT NULL DEFAULT 'mixed',
    customer_value TEXT NOT NULL DEFAULT 'new',
    rationale TEXT,
    owner_summary TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    approved_at TEXT,
    executed_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    dispute_id TEXT REFERENCES disputes(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS merchant_policy (
    id TEXT PRIMARY KEY,
    merchant_name TEXT NOT NULL,
    approval_amount_cents INTEGER NOT NULL DEFAULT 20000,
    min_win_probability_to_fight REAL NOT NULL DEFAULT 0.50,
    always_concede_under_cents INTEGER NOT NULL DEFAULT 1500,
    vip_concede_max_cents INTEGER NOT NULL DEFAULT 50000,
    silence_action TEXT NOT NULL DEFAULT 'fight',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

TABLE_ORDER = [
    "customers",
    "orders",
    "order_items",
    "shipments",
    "shipment_events",
    "customer_messages",
    "disputes",
    "merchant_policy",
]


def init_local_db(db_path: Path = LOCAL_DB_PATH) -> sqlite3.Connection:
    """Initialize local SQLite database with schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SQLITE_SCHEMA)
    conn.commit()
    return conn


def serialize_for_sql(val):
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    if isinstance(val, bool):
        return 1 if val else 0
    return val


def seed_local_db(conn: sqlite3.Connection, reset: bool = False):
    """Seed fixtures into local SQLite database."""
    cursor = conn.cursor()
    if reset:
        # Clear tables in reverse dependency order
        for table in reversed(TABLE_ORDER):
            cursor.execute(f"DELETE FROM {table};")
        conn.commit()

    for table in TABLE_ORDER:
        try:
            records = load_fixture(table)
        except FileNotFoundError:
            continue

        for rec in records:
            cols = list(rec.keys())
            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join(cols)
            vals = [serialize_for_sql(rec[k]) for k in cols]

            update_assignments = ", ".join([f"{c}=excluded.{c}" for c in cols if c != "id"])
            if update_assignments:
                sql = f"""
                    INSERT INTO {table} ({col_names})
                    VALUES ({placeholders})
                    ON CONFLICT(id) DO UPDATE SET {update_assignments};
                """
            else:
                sql = f"""
                    INSERT INTO {table} ({col_names})
                    VALUES ({placeholders})
                    ON CONFLICT(id) DO NOTHING;
                """
            cursor.execute(sql, vals)

    conn.commit()


def get_local_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """Retrieve row counts from local SQLite database."""
    cursor = conn.cursor()
    counts = {}
    for table in ["customers", "orders", "shipments", "customer_messages", "merchant_policy"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        counts[table] = cursor.fetchone()[0]
    return counts


# -----------------------------------------------------------------------------
# Supabase REST client implementation
# -----------------------------------------------------------------------------
def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not (url and key):
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        print(f"Warning: Failed to create Supabase client: {e}")
        return None


def seed_supabase_cloud(client, reset: bool = False):
    """Seed fixtures into remote Supabase database."""
    if reset:
        for table in reversed(TABLE_ORDER):
            try:
                # Delete all rows where id is not null
                client.table(table).delete().neq("id", "___nonexistent___").execute()
            except Exception as e:
                print(f"Note on resetting remote {table}: {e}")

    for table in TABLE_ORDER:
        try:
            records = load_fixture(table)
        except FileNotFoundError:
            continue

        if records:
            # Upsert records
            client.table(table).upsert(records).execute()


def get_supabase_cloud_counts(client) -> dict[str, int]:
    """Get row counts from remote Supabase database."""
    counts = {}
    for table in ["customers", "orders", "shipments", "customer_messages", "merchant_policy"]:
        resp = client.table(table).select("id", count="exact").execute()
        counts[table] = resp.count or len(resp.data or [])
    return counts


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Seed Supabase / local database with synthetic fixtures.")
    parser.add_argument("--reset", action="store_true", help="Clear existing rows before seeding")
    parser.add_argument("--verify", action="store_true", help="Verify counts and output proof line")
    parser.add_argument("--local-only", action="store_true", help="Skip remote Supabase and seed local SQLite only")
    args = parser.parse_args()

    supabase_client = None
    if not args.local_only:
        supabase_client = get_supabase_client()

    if supabase_client:
        print("Connected to Supabase cloud instance.")
        seed_supabase_cloud(supabase_client, reset=args.reset)
        counts = get_supabase_cloud_counts(supabase_client)
        backend_name = "Supabase"
    else:
        print("Supabase credentials not available or --local-only specified. Using local database store.")
        conn = init_local_db()
        seed_local_db(conn, reset=args.reset)
        counts = get_local_counts(conn)
        backend_name = "Local SQLite"

    print(f"\n{backend_name} Seeding complete.")
    print(f"  Customers: {counts.get('customers', 0)}")
    print(f"  Orders: {counts.get('orders', 0)}")
    print(f"  Shipments: {counts.get('shipments', 0)}")
    print(f"  Messages: {counts.get('customer_messages', 0)}")
    print(f"  Policy: {counts.get('merchant_policy', 0)}")

    c_count = counts.get("customers", 0)
    o_count = counts.get("orders", 0)
    s_count = counts.get("shipments", 0)
    m_count = counts.get("customer_messages", 0)
    p_count = counts.get("merchant_policy", 0)

    is_valid = (
        c_count == 10
        and o_count == 12
        and s_count == 11
        and m_count >= 8
        and p_count == 1
    )

    proof_line = f"PROOF R-01: rows customers={c_count} orders={o_count} shipments={s_count} messages>=8 policy={p_count} = {'PASS' if is_valid else 'FAIL'}"
    print(f"\n{proof_line}")

    if is_valid:
        # Append proof line to docs/proofs/R-01.md
        PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
        existing_proofs = ""
        if PROOF_PATH.exists():
            with open(PROOF_PATH, "r", encoding="utf-8") as f:
                existing_proofs = f.read()
        if proof_line not in existing_proofs:
            with open(PROOF_PATH, "a", encoding="utf-8") as f:
                f.write(f"{proof_line}\n")
        return 0
    else:
        print("Verification failed: Counts did not match acceptance criteria.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
