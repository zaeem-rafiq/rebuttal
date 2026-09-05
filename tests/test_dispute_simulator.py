"""
tests/test_dispute_simulator.py

Unit tests for scripts/simulate_dispute.py:
- Scenario definitions (S1, S2, S3) and test PaymentMethods.
- Mock dispute simulation and database/fixture order updates.
- Charge context retrieval and order metadata matching.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.simulate_dispute import (
    SCENARIO_CONFIG,
    simulate_mock,
    update_order_fixture,
    REPO_ROOT,
)


def test_scenario_configurations():
    assert "S1" in SCENARIO_CONFIG
    assert "S2" in SCENARIO_CONFIG
    assert "S3" in SCENARIO_CONFIG

    s1 = SCENARIO_CONFIG["S1"]
    assert s1["order_id"] == "ORD-1001"
    assert s1["payment_method"] == "pm_card_createDisputeProductNotReceived"
    assert s1["expected_reason"] == "product_not_received"
    assert s1["amount_cents"] == 4800

    s2 = SCENARIO_CONFIG["S2"]
    assert s2["order_id"] == "ORD-1002"
    assert s2["payment_method"] == "pm_card_createDispute"
    assert s2["expected_reason"] == "fraudulent"
    assert s2["amount_cents"] == 34000

    s3 = SCENARIO_CONFIG["S3"]
    assert s3["order_id"] == "ORD-1003"
    assert s3["payment_method"] == "pm_card_createDisputeInquiry"
    assert s3["expected_status"] == "warning_needs_response"
    assert s3["amount_cents"] == 12900


def test_simulate_mock_s1_execution():
    res = simulate_mock("S1")
    assert res["reason"] == "product_not_received"
    assert res["amount"] == 4800
    assert res["payment_intent_id"].startswith("pi_mock_s1")

    # Verify fixture was updated with PI id
    orders_path = REPO_ROOT / "data" / "fixtures" / "orders.json"
    with open(orders_path, "r", encoding="utf-8") as f:
        orders = {o["id"]: o for o in json.load(f)}

    assert orders["ORD-1001"]["payment_intent_id"] == res["payment_intent_id"]


def test_simulate_mock_s2_execution():
    res = simulate_mock("S2")
    assert res["reason"] == "fraudulent"
    assert res["amount"] == 34000
    assert res["payment_intent_id"].startswith("pi_mock_s2")

    # Verify fixture was updated with PI id
    orders_path = REPO_ROOT / "data" / "fixtures" / "orders.json"
    with open(orders_path, "r", encoding="utf-8") as f:
        orders = {o["id"]: o for o in json.load(f)}

    assert orders["ORD-1002"]["payment_intent_id"] == res["payment_intent_id"]
