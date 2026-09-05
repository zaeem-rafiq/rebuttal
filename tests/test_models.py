"""tests/test_models.py

Unit tests for DisputeStrategy, EvidencePacket, and intermediate evidence models.
Enforces constraints defined in HAC-4 / R-02.
"""

import pytest
from pydantic import ValidationError

from agent.models import (
    DisputeStrategy,
    EvidencePacket,
    OrderEvidence,
    ShippingEvidence,
    CommsEvidence,
    HistoryEvidence,
)


def test_dispute_strategy_valid():
    """Test valid DisputeStrategy instantiation."""
    strategy = DisputeStrategy(
        action="fight",
        win_probability=0.85,
        expected_value_cents=3855,
        customer_value="new",
        evidence_strength="strong",
        rationale="Carrier tracking confirms UPS delivery with signature matching customer. AVS/CVC matched.",
        owner_summary="Dispute S1: Fighting $48.00 claim. UPS tracking signed by OKAFOR.",
    )
    assert strategy.action == "fight"
    assert strategy.win_probability == 0.85
    assert strategy.expected_value_cents == 3855
    assert strategy.customer_value == "new"
    assert strategy.evidence_strength == "strong"


def test_dispute_strategy_invalid_action():
    """Test that invalid action strings raise validation errors."""
    with pytest.raises(ValidationError):
        DisputeStrategy(
            action="ignore",  # Not in {'fight', 'concede', 'refund_inquiry'}
            win_probability=0.5,
            expected_value_cents=0,
            customer_value="new",
            evidence_strength="mixed",
            rationale="Valid rationale.",
            owner_summary="Valid summary.",
        )


def test_dispute_strategy_word_limit_enforced():
    """Test that rationale exceeding 80 words raises a validation error."""
    long_rationale = " ".join(["word"] * 85)
    with pytest.raises(ValidationError) as exc_info:
        DisputeStrategy(
            action="fight",
            win_probability=0.75,
            expected_value_cents=2000,
            customer_value="new",
            evidence_strength="strong",
            rationale=long_rationale,
            owner_summary="Short summary.",
        )
    assert "Rationale exceeds 80 words" in str(exc_info.value)


def test_dispute_strategy_char_limit_enforced():
    """Test that owner_summary exceeding 320 chars raises a validation error."""
    long_summary = "A" * 325
    with pytest.raises(ValidationError) as exc_info:
        DisputeStrategy(
            action="fight",
            win_probability=0.75,
            expected_value_cents=2000,
            customer_value="new",
            evidence_strength="strong",
            rationale="Valid rationale under eighty words.",
            owner_summary=long_summary,
        )
    assert "Owner summary exceeds 320 characters" in str(exc_info.value)


def test_evidence_packet_structure():
    """Test EvidencePacket field serialization."""
    packet = EvidencePacket(
        customer_name="Michael Okafor",
        customer_email_address="m.okafor@example.com",
        billing_address="1424 Elm St, Apt 4B, Austin, TX 78701",
        shipping_address="1424 Elm St, Apt 4B, Austin, TX 78701",
        shipping_carrier="UPS",
        shipping_tracking_number="1Z9999999999999991",
        shipping_date="2026-08-25",
        narrative="Customer placed order ORD-1001 for $48.00. Carrier tracking confirms delivery.",
        files=["receipt.pdf", "delivery_confirmation.pdf"],
    )
    dumped = packet.model_dump()
    assert dumped["shipping_tracking_number"] == "1Z9999999999999991"
    assert dumped["shipping_carrier"] == "UPS"
    assert len(dumped["files"]) == 2
    assert "ORD-1001" in dumped["narrative"]


def test_intermediate_evidence_models():
    """Test OrderEvidence, ShippingEvidence, CommsEvidence, HistoryEvidence."""
    order_ev = OrderEvidence(
        order_id="ORD-1001",
        customer_id="CUST-001",
        amount_cents=4800,
        status="delivered",
    )
    assert order_ev.order_id == "ORD-1001"
    assert order_ev.amount_cents == 4800

    ship_ev = ShippingEvidence(
        order_id="ORD-1001",
        carrier="UPS",
        tracking_number="1Z9999999999999991",
        signed_by="OKAFOR",
    )
    assert ship_ev.signed_by == "OKAFOR"

    comms_ev = CommsEvidence(
        customer_id="CUST-002",
        order_id="ORD-1002",
        has_address_change_request=True,
    )
    assert comms_ev.has_address_change_request is True

    hist_ev = HistoryEvidence(
        customer_id="CUST-002",
        customer_tier="repeat",
        total_prior_orders=5,
        total_prior_spend_cents=112000,
    )
    assert hist_ev.customer_tier == "repeat"
    assert hist_ev.total_prior_orders == 5
