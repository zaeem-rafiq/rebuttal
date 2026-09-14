"""Owner decisions must persist to the same row locally and in the cloud."""
import sqlite3
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agent.tools import case_tools


class Cloud:
    def __init__(self, rows):
        self.rows = [dict(row) for row in rows]
        self.fail_updates = False

    def table(self, name):
        assert name == 'decisions'
        cloud = self

        class Query:
            def __init__(self):
                self.filters, self.orders, self.values, self.count = [], [], None, None

            def select(self, fields):
                return self

            def update(self, values):
                self.values = values
                return self

            def eq(self, key, value):
                self.filters.append((key, value))
                return self

            def order(self, key, desc=False):
                self.orders.append((key, desc))
                return self

            def limit(self, count):
                self.count = count
                return self

            def execute(self):
                rows = [row for row in cloud.rows if all(row.get(k) == v for k, v in self.filters)]
                for key, desc in reversed(self.orders):
                    rows.sort(key=lambda row: row[key], reverse=desc)
                if self.count is not None:
                    rows = rows[:self.count]
                if self.values is not None:
                    if cloud.fail_updates:
                        raise RuntimeError('test transport failure')
                    for row in rows:
                        row.update(self.values)
                return SimpleNamespace(data=[dict(row) for row in rows])

        return Query()


def decision(id='new', created='2026-09-14T20:00:00Z', **changes):
    return dict(id=id, dispute_id='du_case', action='fight', status='pending',
                created_at=created, answered_at=None, **changes)


@pytest.fixture
def stores(tmp_path, monkeypatch):
    path = tmp_path / 'case.db'
    with sqlite3.connect(path) as conn:
        conn.executescript('''
            CREATE TABLE decisions (id TEXT PRIMARY KEY, dispute_id TEXT, action TEXT,
                status TEXT, created_at TEXT, answered_at TEXT);
            CREATE TABLE disputes (id TEXT, order_id TEXT, status TEXT,
                evidence_due_by TEXT, metadata TEXT);
            INSERT INTO disputes VALUES ('du_case', 'order', 'needs_response', NULL, '{}');
        ''')
        rows = [decision('old', '2026-09-13T20:00:00Z'), decision()]
        for row in rows:
            conn.execute('INSERT INTO decisions VALUES (?,?,?,?,?,?)', tuple(row.values()))
    cloud = Cloud(rows)
    monkeypatch.setattr(case_tools, '_get_supabase_client', lambda: cloud)
    monkeypatch.setattr(case_tools, 'LOCAL_DB_PATH', path)
    return path, cloud


def local_rows(path):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        return {row['id']: dict(row) for row in conn.execute('SELECT * FROM decisions')}


@pytest.mark.parametrize('status,action', [('approved', 'concede'), ('approved', 'fight'),
                                          ('approved', 'refund_inquiry'), ('held', None)])
def test_exact_decision_updates_both_stores_and_preserves_history(stores, status, action):
    path, cloud = stores
    result = case_tools.update_decision_status('new', status, action, '2026-09-14T21:00:00Z', path)
    local = local_rows(path)
    assert local['old'] == cloud.rows[0] == decision('old', '2026-09-13T20:00:00Z')
    assert local['new'] == cloud.rows[1] == result
    assert result['status'] == status
    assert result['action'] == (action or 'fight')
    assert result['answered_at'] == '2026-09-14T21:00:00Z'


def test_newer_cloud_only_decision_is_selected_once(stores):
    path, cloud = stores
    cloud.rows.append(decision('cloud-only', '2026-09-14T21:00:00+00:00'))
    chosen = case_tools.get_latest_decision('du_case', path)
    assert chosen['id'] == 'cloud-only'
    result = case_tools.update_decision_status(chosen['id'], 'approved', 'concede', '2026-09-14T22:00:00Z', path)
    assert result['status'] == 'approved'
    assert all(row['status'] == 'pending' for row in local_rows(path).values())
    assert cloud.rows[1]['status'] == 'pending'


def test_omitted_values_are_preserved(stores):
    path, cloud = stores
    case_tools.update_decision_status('new', 'approved', 'concede', '2026-09-14T21:00:00Z', path)
    result = case_tools.update_decision_status('new', 'held', db_path=path)
    assert result['action'] == 'concede'
    assert result['answered_at'] == '2026-09-14T21:00:00Z'
    assert local_rows(path)['new'] == cloud.rows[1]


def test_cloud_write_failure_is_reported(stores):
    path, cloud = stores
    cloud.fail_updates = True
    with pytest.raises(RuntimeError, match='synchronization failed'):
        case_tools.update_decision_status('new', 'approved', 'concede', db_path=path)


def test_missing_cloud_row_is_not_reported_as_success(stores):
    path, cloud = stores
    cloud.rows.clear()
    with pytest.raises(RuntimeError, match='synchronization failed'):
        case_tools.update_decision_status('new', 'approved', 'concede', db_path=path)


def test_configured_but_unavailable_cloud_fails_before_local_update(stores, monkeypatch):
    path, cloud = stores
    monkeypatch.setattr(case_tools, '_get_supabase_client', lambda: None)
    monkeypatch.setenv('SUPABASE_URL', 'https://example.invalid')
    with pytest.raises(RuntimeError, match='unavailable'):
        case_tools.update_decision_status('new', 'approved', db_path=path)
    assert local_rows(path)['new']['status'] == 'pending'


@pytest.mark.parametrize('answer,expected,proposed', [('1', 'fight', 'fight'), ('2', 'concede', 'fight'),
                                                     ('3', 'fight', 'fight'), ('2', 'refund_inquiry', 'refund_inquiry')])
def test_owner_reply_uses_cloud_only_current_decision(stores, monkeypatch, answer, expected, proposed):
    from scripts import reply
    from agent import executor
    from agent.tools import stripe_tools
    path, cloud = stores
    row = decision('cloud-only', '2026-09-14T21:00:00Z')
    row['action'] = proposed
    cloud.rows.append(row)
    monkeypatch.setattr(stripe_tools, 'refund_inquiry', lambda id: {'id': 're_test'})
    monkeypatch.setattr(reply, 'LOCAL_DB_PATH', path)
    monkeypatch.setattr(reply, 'verify_live_key_guard', lambda: None)
    monkeypatch.setattr(reply, 'resolve_stripe_dispute_id', lambda id: id)
    monkeypatch.setattr(reply, 'record_case', MagicMock())
    monkeypatch.setattr(reply, 'send_owner_sms', lambda *a, **kw: 'SM_test')
    monkeypatch.setattr(reply, 'get_dispute', lambda id: {'id': id, 'status': 'lost'})
    monkeypatch.setattr(reply, 'concede_dispute', lambda id: {'id': id, 'status': 'lost'})
    monkeypatch.setattr(executor, 'build_executor_agent', lambda **kw: SimpleNamespace(_interrupt_state=None))
    result = reply.process_reply('du_case', answer)
    assert result['answered_at']
    assert cloud.rows[-1]['answered_at'] == result['answered_at']
    assert cloud.rows[-1]['status'] == ('held' if answer == '3' else 'approved')
    assert cloud.rows[-1]['action'] == expected
    assert all(row['status'] == 'pending' for row in local_rows(path).values())


def test_hook_persists_cloud_only_decision(stores, monkeypatch):
    from agent.hooks import ApprovalGate
    import agent.hooks as hooks
    path, cloud = stores
    cloud.rows.append(decision('cloud-only', '2026-09-14T21:00:00Z'))
    monkeypatch.setattr(hooks, 'LOCAL_DB_PATH', path)
    ApprovalGate()._update_decision_status('cloud-only', 'held', answered_at='2026-09-14T22:00:00Z')
    assert cloud.rows[-1]['status'] == 'held'
    assert local_rows(path)['new']['status'] == 'pending'


def test_real_local_schema_upgrades_existing_decision_without_data_loss(tmp_path, monkeypatch):
    from scripts.seed_supabase import SQLITE_SCHEMA, init_local_db
    path = tmp_path / 'legacy.db'
    with sqlite3.connect(path) as conn:
        conn.executescript(SQLITE_SCHEMA.replace('    answered_at TEXT,\n', ''))
        conn.execute("INSERT INTO disputes (id, amount_cents, reason, status) VALUES ('du_case', 34000, 'fraudulent', 'needs_response')")
        conn.execute("INSERT INTO decisions (id, dispute_id, action) VALUES ('legacy', 'du_case', 'concede')")
    monkeypatch.setattr(case_tools, '_get_supabase_client', lambda: None)
    monkeypatch.delenv('SUPABASE_URL', raising=False)
    monkeypatch.delenv('SUPABASE_SERVICE_KEY', raising=False)
    init_local_db(path).close()
    init_local_db(path).close()
    result = case_tools.update_decision_status('legacy', 'held', answered_at='2026-09-14T22:00:00Z', db_path=path)
    assert result['action'] == 'concede'
    assert result['status'] == 'held'
    assert result['answered_at'] == '2026-09-14T22:00:00Z'
    assert list(local_rows(path)) == ['legacy']
