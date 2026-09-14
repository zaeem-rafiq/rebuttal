"""New Stripe disputes must exist before FK-linked decisions and audit events."""

import copy
import json
import sqlite3
from unittest.mock import MagicMock

import pytest

from agent.ingress import ingest_stripe_dispute
from scripts.seed_supabase import SQLITE_SCHEMA


@pytest.fixture
def ingress_db(tmp_path):
    path = tmp_path / "ingress.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(SQLITE_SCHEMA)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("INSERT INTO customers (id,name,email) VALUES ('customer-1','Owner fixture','fixture@example.test')")
        conn.execute(
            "INSERT INTO orders (id,customer_id,amount_cents,payment_intent_id,charge_id) VALUES (?,?,?,?,?)",
            ("order-1", "customer-1", 34000, "pi_new", "ch_old"),
        )
    return path


@pytest.fixture
def stripe_dispute():
    return {
        "id": "du_new_ingress",
        "livemode": False,
        "amount": 18000,
        "currency": "usd",
        "reason": "fraudulent",
        "status": "needs_response",
        "created": 1789411931,
        "evidence_details": {"due_by": 1790121599},
        "metadata": {},
        "charge": {"id": "ch_new", "metadata": {"order_id": "order-1"}},
        "payment_intent": {"id": "pi_new", "metadata": {"order_id": "order-1", "scenario": "S2"}},
    }


def test_new_dispute_enables_fk_linked_decision_and_audit(ingress_db, stripe_dispute):
    with sqlite3.connect(ingress_db) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            conn.execute("INSERT INTO decisions (id,dispute_id,action) VALUES ('before',?,'concede')", (stripe_dispute["id"],))

    cloud = MagicMock()
    original = copy.deepcopy(stripe_dispute)
    context = ingest_stripe_dispute(stripe_dispute, ingress_db, supabase_client=cloud)

    assert context == {
        "dispute_id": "du_new_ingress", "order_id": "order-1", "customer_id": "customer-1",
        "amount_cents": 18000, "currency": "usd", "reason": "fraudulent", "scenario": "S2",
    }
    assert stripe_dispute == original
    with sqlite3.connect(ingress_db) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("INSERT INTO decisions (id,dispute_id,action) VALUES ('after',?,'concede')", (context["dispute_id"],))
        conn.execute("INSERT INTO audit_log (id,dispute_id,action,actor) VALUES ('audit',?,'concede_dispute','owner')", (context["dispute_id"],))
        row = dict(conn.execute("SELECT * FROM disputes WHERE id=?", (context["dispute_id"],)).fetchone())
    assert row["created_at"] == "2026-09-14T18:52:11Z"
    assert row["evidence_due_by"] == "2026-09-22T23:59:59Z"
    assert row["payment_intent_id"] == "pi_new"
    assert row["charge_id"] == "ch_new"
    assert row["amount_cents"] == 18000  # Partial dispute amount, not the $340 order total.
    assert json.loads(row["metadata"])["stripe_dispute_id"] == context["dispute_id"]
    cloud.table.assert_called_once_with("disputes")
    cloud_record = cloud.table.return_value.upsert.call_args.args[0]
    assert cloud.table.return_value.upsert.call_args.kwargs == {"on_conflict": "id"}
    assert cloud_record == {**row, "metadata": json.loads(row["metadata"])}
    cloud.table.return_value.upsert.return_value.execute.assert_called_once_with()


def test_repeated_ingress_updates_status_without_deleting_decisions(ingress_db, stripe_dispute):
    ingest_stripe_dispute(stripe_dispute, ingress_db)
    with sqlite3.connect(ingress_db) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("INSERT INTO decisions (id,dispute_id,action) VALUES ('pending',?,'fight')", (stripe_dispute["id"],))
    stripe_dispute["status"] = "under_review"
    ingest_stripe_dispute(stripe_dispute, ingress_db)
    with sqlite3.connect(ingress_db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM disputes").fetchone()[0] == 1
        assert conn.execute("SELECT status FROM disputes").fetchone()[0] == "under_review"
        assert conn.execute("SELECT id FROM decisions").fetchone()[0] == "pending"


def test_unexpanded_ids_resolve_by_existing_payment_mapping(ingress_db, stripe_dispute):
    stripe_dispute.update(charge="ch_new", payment_intent="pi_new")
    context = ingest_stripe_dispute(stripe_dispute, ingress_db)
    assert context["order_id"] == "order-1"
    assert context["scenario"] is None


def test_unknown_explicit_order_does_not_fall_back_to_another_order(ingress_db, stripe_dispute):
    stripe_dispute["charge"]["metadata"] = {}
    stripe_dispute["payment_intent"]["metadata"] = {}
    stripe_dispute["metadata"] = {"order_id": "missing-order"}
    cloud = MagicMock()
    with pytest.raises(ValueError, match="one existing order"):
        ingest_stripe_dispute(stripe_dispute, ingress_db, supabase_client=cloud)
    cloud.table.assert_not_called()
    with sqlite3.connect(ingress_db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM disputes").fetchone()[0] == 0


@pytest.mark.parametrize("left,right", [("charge", "payment_intent"), ("charge", "dispute"), ("payment_intent", "dispute")])
def test_conflicting_order_links_fail_before_local_or_cloud_write(ingress_db, stripe_dispute, left, right):
    with sqlite3.connect(ingress_db) as conn:
        conn.execute("INSERT INTO orders (id,customer_id,amount_cents) VALUES ('order-2','customer-1',34000)")
    sources = {"charge": stripe_dispute["charge"], "payment_intent": stripe_dispute["payment_intent"], "dispute": stripe_dispute}
    for source in sources.values():
        source["metadata"] = {}
    sources[left]["metadata"] = {"order_id": "order-1"}
    sources[right]["metadata"] = {"order_id": "order-2"}
    cloud = MagicMock()
    with pytest.raises(ValueError, match="Conflicting Stripe order identifiers"):
        ingest_stripe_dispute(stripe_dispute, ingress_db, supabase_client=cloud)
    cloud.table.assert_not_called()
    with sqlite3.connect(ingress_db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM disputes").fetchone()[0] == 0


def test_empty_order_metadata_does_not_replace_a_known_link(ingress_db, stripe_dispute):
    stripe_dispute["metadata"] = {"order_id": " "}
    assert ingest_stripe_dispute(stripe_dispute, ingress_db)["order_id"] == "order-1"


def test_ambiguous_payment_mapping_is_rejected(ingress_db, stripe_dispute):
    with sqlite3.connect(ingress_db) as conn:
        conn.execute("INSERT INTO orders (id,customer_id,amount_cents,payment_intent_id) VALUES ('order-2','customer-1',34000,'pi_new')")
    stripe_dispute.update(charge="ch_new", payment_intent="pi_new")
    with pytest.raises(ValueError, match="one existing order"):
        ingest_stripe_dispute(stripe_dispute, ingress_db)


def test_cloud_failure_propagates_and_rolls_back_local_ingress(ingress_db, stripe_dispute):
    cloud = MagicMock()
    cloud.table.return_value.upsert.return_value.execute.side_effect = RuntimeError("cloud unavailable")
    with pytest.raises(RuntimeError, match="cloud unavailable"):
        ingest_stripe_dispute(stripe_dispute, ingress_db, supabase_client=cloud)
    with sqlite3.connect(ingress_db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM disputes").fetchone()[0] == 0


@pytest.mark.parametrize("field,value", [("livemode", True), ("livemode", None), ("amount", -1), ("amount", True), ("created", None)])
def test_invalid_or_non_test_record_is_rejected_before_writes(ingress_db, stripe_dispute, field, value):
    stripe_dispute[field] = value
    cloud = MagicMock()
    with pytest.raises(ValueError):
        ingest_stripe_dispute(stripe_dispute, ingress_db, supabase_client=cloud)
    cloud.table.assert_not_called()
    with sqlite3.connect(ingress_db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM disputes").fetchone()[0] == 0
