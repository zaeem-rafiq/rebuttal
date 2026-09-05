"""
tests/test_fixtures.py

Verifies the fixture data in data/fixtures/:
- 10 customers
- 12 orders (including S1 ORD-1001, S2 ORD-1002, S3 ORD-1003)
- 11 shipments
- >= 8 customer messages
- 1 merchant policy
- Validates scenario specifics for S1, S2, and S3.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"


def load_fixture(name: str):
    path = FIXTURES_DIR / f"{name}.json"
    assert path.exists(), f"Fixture file not found: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_fixture_counts():
    customers = load_fixture("customers")
    orders = load_fixture("orders")
    shipments = load_fixture("shipments")
    messages = load_fixture("customer_messages")
    policy = load_fixture("merchant_policy")

    assert len(customers) == 10, f"Expected 10 customers, got {len(customers)}"
    assert len(orders) == 12, f"Expected 12 orders, got {len(orders)}"
    assert len(shipments) == 11, f"Expected 11 shipments, got {len(shipments)}"
    assert len(messages) >= 8, f"Expected >= 8 messages, got {len(messages)}"
    assert len(policy) == 1, f"Expected 1 merchant policy, got {len(policy)}"


def test_scenario_s1_fixture():
    """S1 (ORD-1001): $48.00 trail-mix sampler, M. Okafor, UPS delivered + signed 'OKAFOR', AVS/CVC match."""
    orders = {o["id"]: o for o in load_fixture("orders")}
    shipments = {s["order_id"]: s for s in load_fixture("shipments")}
    order_items = [i for i in load_fixture("order_items") if i["order_id"] == "ORD-1001"]
    messages = [m for m in load_fixture("customer_messages") if m.get("order_id") == "ORD-1001"]

    assert "ORD-1001" in orders
    s1_order = orders["ORD-1001"]
    assert s1_order["amount_cents"] == 4800
    assert s1_order["card_brand"] == "visa"
    assert s1_order["avs_postal_match"] == "match"
    assert s1_order["cvc_match"] == "match"
    assert s1_order["status"] == "delivered"

    assert len(order_items) >= 1
    assert "trail-mix" in order_items[0]["product_name"].lower()

    assert "ORD-1001" in shipments
    s1_shipment = shipments["ORD-1001"]
    assert s1_shipment["carrier"] == "UPS"
    assert s1_shipment["signed_by"] == "OKAFOR"
    assert s1_shipment["status"] == "delivered"
    assert s1_shipment["tracking_number"]

    # Inquiry/tracking thread
    assert len(messages) >= 2
    inbound = [m for m in messages if m["direction"] == "inbound"]
    outbound = [m for m in messages if m["direction"] == "outbound"]
    assert any("arrive" in m["subject"].lower() for m in inbound)
    assert any("tracking" in m["body"].lower() or "ups" in m["body"].lower() for m in outbound)


def test_scenario_s2_fixture():
    """S2 (ORD-1002): $340.00 ceramic pour-over set, J. Lee (4 prior orders, LTV $1,120), shipped to alternate address, no signature."""
    customers = {c["id"]: c for c in load_fixture("customers")}
    orders = {o["id"]: o for o in load_fixture("orders")}
    shipments = {s["order_id"]: s for s in load_fixture("shipments")}
    order_items = [i for i in load_fixture("order_items") if i["order_id"] == "ORD-1002"]
    messages = [m for m in load_fixture("customer_messages") if m.get("order_id") == "ORD-1002"]

    assert "ORD-1002" in orders
    s2_order = orders["ORD-1002"]
    assert s2_order["amount_cents"] == 34000
    customer_id = s2_order["customer_id"]
    customer = customers[customer_id]

    assert customer["name"] == "Jessica Lee"
    assert customer["customer_value"] in ("repeat", "vip")
    assert customer["order_count"] >= 4
    assert customer["lifetime_value_cents"] >= 112000

    assert len(order_items) >= 1
    assert "pour-over" in order_items[0]["product_name"].lower()

    assert "ORD-1002" in shipments
    s2_shipment = shipments["ORD-1002"]
    assert s2_shipment["signed_by"] is None or s2_shipment["signed_by"] == ""
    # Alternate shipping address
    assert "880 Harrison" in str(s2_shipment["shipping_address"])

    # Emailed request for address change
    assert len(messages) >= 2
    inbound = [m for m in messages if m["direction"] == "inbound"]
    assert any(m.get("has_shipping_change") for m in inbound)


def test_scenario_s3_fixture():
    """S3 (ORD-1003): $129.00 coffee subscription, R. Alvarez, inquiry stage, emailed to cancel."""
    customers = {c["id"]: c for c in load_fixture("customers")}
    orders = {o["id"]: o for o in load_fixture("orders")}
    order_items = [i for i in load_fixture("order_items") if i["order_id"] == "ORD-1003"]
    messages = [m for m in load_fixture("customer_messages") if m.get("order_id") == "ORD-1003"]
    disputes = {d.get("order_id"): d for d in load_fixture("disputes")}

    assert "ORD-1003" in orders
    s3_order = orders["ORD-1003"]
    assert s3_order["amount_cents"] == 12900

    customer = customers[s3_order["customer_id"]]
    assert customer["name"] == "Roberto Alvarez"

    assert len(order_items) >= 1
    assert "subscription" in order_items[0]["product_name"].lower()

    # Emailed to cancel
    inbound = [m for m in messages if m["direction"] == "inbound"]
    assert any("cancel" in m["subject"].lower() or "cancel" in m["body"].lower() for m in inbound)

    # Dispute is inquiry stage
    if "ORD-1003" in disputes:
        s3_dispute = disputes["ORD-1003"]
        assert s3_dispute["status"] == "warning_needs_response"


def test_merchant_policy_fixture():
    policies = load_fixture("merchant_policy")
    p = policies[0]
    assert p["approval_amount_cents"] == 20000
    assert p["min_win_probability_to_fight"] == 0.50
    assert p["silence_action"] == "fight"
