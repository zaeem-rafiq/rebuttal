"""Closure uses execution audits without calling Stripe, Bedrock, or Supabase."""

import json
import socket
import sqlite3
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.fixture
def closure(monkeypatch, tmp_path):
    def no_network(*args, **kwargs):
        raise AssertionError("Network access is forbidden in closure tests")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    from agent import app as runtime
    from agent.tools import case_tools, memory_tools

    db = tmp_path / "case.db"
    with sqlite3.connect(db) as conn:
        conn.executescript("""
            CREATE TABLE disputes (id TEXT, status TEXT, updated_at TEXT);
            INSERT INTO disputes VALUES ('du_test', 'needs_response', NULL);
            CREATE TABLE audit_log (id TEXT, dispute_id TEXT, action TEXT,
                                    actor TEXT, details TEXT, created_at TEXT);
            CREATE TABLE decisions (dispute_id TEXT, action TEXT, status TEXT);
        """)
    monkeypatch.setattr(runtime, "LOCAL_DB_PATH", db)
    monkeypatch.setattr(case_tools, "LOCAL_DB_PATH", db)
    monkeypatch.setattr(runtime, "load_secrets", lambda: None)
    monkeypatch.setattr(runtime, "ensure_db", lambda: None)
    monkeypatch.setattr(case_tools, "_get_supabase_client", lambda: None)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    store = Mock(side_effect=lambda **kwargs: {"status": "stored", **kwargs})
    monkeypatch.setattr(memory_tools, "store_dispute_outcome", store)

    def add_audit(action, actor="owner", dispute_id="du_test"):
        with sqlite3.connect(db) as conn:
            conn.execute("INSERT INTO audit_log VALUES ('prior', ?, ?, ?, '{}', '')",
                         (dispute_id, action, actor))

    def run(**overrides):
        result = runtime.main({"type": "dispute.closed", "dispute_id": "du_test",
                               "status": "lost", "reason": "fraudulent", "amount": 34000,
                               **overrides})
        with sqlite3.connect(db) as conn:
            assert conn.execute("SELECT status FROM disputes").fetchone()[0] == overrides.get("status", "lost")
            details = conn.execute("SELECT details FROM audit_log WHERE action = 'dispute_closed_webhook'").fetchone()[0]
        assert json.loads(details)["memory_event"] == result["memory_event"]
        return result["memory_event"]

    return SimpleNamespace(db=db, store=store, add_audit=add_audit, run=run)


class AuditCloud:
    """Offline query double honoring filters; cloud writes are not needed here."""

    def __init__(self, rows):
        self.rows = rows
        self.filters = {}

    def table(self, name):
        assert name in {"audit_log", "disputes"}
        self.filters = {}
        return self

    def select(self, fields):
        return self

    def eq(self, key, value):
        self.filters[key] = {value}
        return self

    def in_(self, key, values):
        self.filters[key] = set(values)
        return self

    def limit(self, count):
        assert count == 1
        return self

    def execute(self):
        return SimpleNamespace(data=[row for row in self.rows
                                     if all(row.get(k) in v for k, v in self.filters.items())][:1])


@pytest.mark.parametrize("audit_action,expected", [
    ("concede_dispute", "concede"),
    ("submit_evidence", "fight"),
    ("refund_inquiry", "refund_inquiry"),
])
def test_confirmed_local_execution(closure, audit_action, expected):
    closure.add_audit(audit_action, actor="executor")
    assert closure.run()["action"] == expected
    assert closure.store.call_args.kwargs["action"] == expected


def test_cloud_only_concession_in_fresh_session(closure, monkeypatch):
    from agent.tools import case_tools

    cloud = AuditCloud([{"dispute_id": "du_test", "action": "concede_dispute", "actor": "owner"}])
    monkeypatch.setattr(case_tools, "_get_supabase_client", lambda: cloud)
    assert closure.run(action="fight")["action"] == "concede"
    closure.store.assert_called_once()


def test_lost_and_approval_are_not_execution(closure):
    closure.add_audit("approve_decision")
    closure.add_audit("concede_dispute", dispute_id="du_other")
    closure.add_audit("concede_dispute", actor="webhook")
    with sqlite3.connect(closure.db) as conn:
        conn.execute("INSERT INTO decisions VALUES ('du_test', 'concede', 'approved')")
    event = closure.run(action="concede", details={"memory_event": {"status": "stored"}})
    assert event == {"status": "skipped", "reason": "no_confirmed_execution_action", "dispute_id": "du_test"}
    closure.store.assert_not_called()


def test_conflicting_local_cloud_actions_skip_memory(closure, monkeypatch):
    from agent.tools import case_tools

    closure.add_audit("concede_dispute")
    cloud = AuditCloud([{"dispute_id": "du_test", "action": "submit_evidence", "actor": "executor"}])
    monkeypatch.setattr(case_tools, "_get_supabase_client", lambda: cloud)
    assert closure.run()["reason"] == "conflicting_execution_actions"
    closure.store.assert_not_called()


def test_duplicate_cloud_audits_do_not_hide_conflict(closure, monkeypatch):
    from agent.tools import case_tools

    rows = [{"dispute_id": "du_test", "action": "concede_dispute", "actor": "owner"}] * 1001
    rows.append({"dispute_id": "du_test", "action": "submit_evidence", "actor": "executor"})
    monkeypatch.setattr(case_tools, "_get_supabase_client", lambda: AuditCloud(rows))
    assert closure.run()["reason"] == "conflicting_execution_actions"
    closure.store.assert_not_called()


@pytest.mark.parametrize("client_failure", [False, True])
def test_unavailable_cloud_does_not_use_partial_local_evidence(closure, monkeypatch, client_failure):
    from agent.tools import case_tools

    closure.add_audit("concede_dispute")
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    if client_failure:
        cloud = AuditCloud([])
        cloud.execute = Mock(side_effect=RuntimeError("offline"))
        monkeypatch.setattr(case_tools, "_get_supabase_client", lambda: cloud)
    assert closure.run()["reason"] == "execution_audit_unavailable"
    closure.store.assert_not_called()
