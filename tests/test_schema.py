"""
tests/test_schema.py

Verifies the Supabase schema definition in schema/supabase_schema.sql:
- All 10 required tables are defined with constraints and relations.
- Indexes and foreign keys are created.
- Schema initializes properly in local database store.
"""

import re
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = REPO_ROOT / "schema" / "supabase_schema.sql"

REQUIRED_TABLES = [
    "customers",
    "orders",
    "order_items",
    "shipments",
    "shipment_events",
    "customer_messages",
    "disputes",
    "decisions",
    "audit_log",
    "merchant_policy",
]


def test_schema_file_exists():
    assert SCHEMA_FILE.exists(), f"Schema file missing: {SCHEMA_FILE}"
    content = SCHEMA_FILE.read_text(encoding="utf-8")
    assert len(content) > 500, "Schema file appears empty or incomplete"


def test_all_tables_defined_in_sql():
    content = SCHEMA_FILE.read_text(encoding="utf-8").lower()
    for table in REQUIRED_TABLES:
        pattern = rf"create\s+table\s+(if\s+not\s+exists\s+)?{table}\s*\("
        assert re.search(pattern, content), f"Table '{table}' not defined with CREATE TABLE in schema SQL"


def test_table_constraints_and_foreign_keys():
    content = SCHEMA_FILE.read_text(encoding="utf-8").lower()

    # Foreign key references
    assert "references customers(id)" in content
    assert "references orders(id)" in content
    assert "references shipments(id)" in content
    assert "references disputes(id)" in content

    # Check constraints
    assert "customer_value in ('new', 'repeat', 'vip')" in content
    assert "action in ('fight', 'concede', 'refund_inquiry')" in content
    assert "status in ('needs_response', 'warning_needs_response', 'under_review'" in content
    assert "direction in ('inbound', 'outbound')" in content
    assert "silence_action in ('fight', 'concede')" in content


def test_local_sqlite_schema_initialization(tmp_path):
    from scripts.seed_supabase import init_local_db, SQLITE_SCHEMA

    test_db = tmp_path / "test_supabase.db"
    conn = init_local_db(test_db)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}

    for table in REQUIRED_TABLES:
        assert table in tables, f"Expected table '{table}' in local SQLite database"

    conn.close()
