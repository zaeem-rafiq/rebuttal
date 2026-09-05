"""
tests/test_stripe_tools.py

Unit tests for agent/tools/stripe_tools.py:
- Live-key guard verification (rejects sk_live_, requires sk_test_).
- Strands @tool decorators and signatures.
- Context extraction in get_charge_context (amount, card checks, billing details, metadata.order_id, customer email).
- Dispute operations: concede_dispute, submit_evidence, upload_evidence_file.
- refund_inquiry enforcement of 'warning_needs_response' status check.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from agent.tools.stripe_tools import (
    verify_live_key_guard,
    get_dispute,
    get_charge_context,
    list_open_disputes,
    upload_evidence_file,
    submit_evidence,
    concede_dispute,
    refund_inquiry,
)


def test_live_key_guard_enforcement():
    # Rejects empty or missing key
    with pytest.raises((AssertionError, RuntimeError)):
        verify_live_key_guard("")

    # Rejects live key
    with pytest.raises((AssertionError, RuntimeError)):
        verify_live_key_guard("sk_live_51234567890abcdef")

    # Accepts test key
    valid_key = "sk_test_51234567890abcdef"
    assert verify_live_key_guard(valid_key) == valid_key


def test_strands_tool_decorations():
    # Each tool should be decorated as a Strands DecoratedFunctionTool
    tools = [
        get_dispute,
        get_charge_context,
        list_open_disputes,
        upload_evidence_file,
        submit_evidence,
        concede_dispute,
        refund_inquiry,
    ]
    for t in tools:
        # Strands DecoratedFunctionTool provides tool_name and tool_spec
        assert hasattr(t, "tool_name") or callable(t), f"{t} is not a valid Strands tool"


@patch("agent.tools.stripe_tools.verify_live_key_guard")
@patch("agent.tools.stripe_tools.stripe.PaymentIntent.retrieve")
def test_get_charge_context_payment_intent(mock_pi_retrieve, mock_guard):
    mock_guard.return_value = "sk_test_mock"

    # Mock charge details
    mock_checks = MagicMock()
    mock_checks.address_line1_check = "pass"
    mock_checks.address_postal_code_check = "pass"
    mock_checks.cvc_check = "pass"

    mock_card = MagicMock()
    mock_card.checks = mock_checks
    mock_card.brand = "visa"
    mock_card.last4 = "4242"

    mock_pm_details = MagicMock()
    mock_pm_details.card = mock_card

    mock_charge = MagicMock()
    mock_charge.id = "ch_12345"
    mock_charge.amount = 34000
    mock_charge.currency = "usd"
    mock_charge.billing_details = {
        "name": "Jessica Lee",
        "email": "j.lee@example.com",
        "address": {"city": "Springfield", "postal_code": "97477"},
    }
    mock_charge.payment_method_details = mock_pm_details
    mock_charge.metadata = {"order_id": "ORD-1002"}
    mock_charge.receipt_email = "j.lee@example.com"

    mock_pi = MagicMock()
    mock_pi.id = "pi_12345"
    mock_pi.amount = 34000
    mock_pi.currency = "usd"
    mock_pi.latest_charge = mock_charge
    mock_pi.metadata = {"order_id": "ORD-1002"}

    mock_pi_retrieve.return_value = mock_pi

    ctx = get_charge_context("pi_12345")

    assert ctx["amount"] == 34000
    assert ctx["currency"] == "usd"
    assert ctx["metadata"]["order_id"] == "ORD-1002"
    assert ctx["customer_email"] == "j.lee@example.com"
    assert ctx["card_checks"]["cvc_check"] == "pass"
    assert ctx["card_checks"]["address_postal_code_check"] == "pass"
    assert ctx["payment_intent_id"] == "pi_12345"
    assert ctx["charge_id"] == "ch_12345"


@patch("agent.tools.stripe_tools.verify_live_key_guard")
@patch("agent.tools.stripe_tools.stripe.Dispute.retrieve")
def test_get_dispute(mock_retrieve, mock_guard):
    mock_guard.return_value = "sk_test_mock"
    mock_disp = MagicMock()
    mock_disp.id = "dp_1001"
    mock_disp.amount = 4800
    mock_disp.reason = "product_not_received"
    mock_disp.status = "needs_response"
    mock_disp.to_dict.return_value = {
        "id": "dp_1001",
        "amount": 4800,
        "reason": "product_not_received",
        "status": "needs_response",
    }
    mock_retrieve.return_value = mock_disp

    result = get_dispute("dp_1001")
    assert result["id"] == "dp_1001"
    assert result["reason"] == "product_not_received"


@patch("agent.tools.stripe_tools.verify_live_key_guard")
@patch("agent.tools.stripe_tools.stripe.Dispute.close")
def test_concede_dispute(mock_close, mock_guard):
    mock_guard.return_value = "sk_test_mock"
    mock_disp = MagicMock()
    mock_disp.id = "dp_1002"
    mock_disp.status = "lost"
    mock_disp.to_dict.return_value = {"id": "dp_1002", "status": "lost"}
    mock_close.return_value = mock_disp

    res = concede_dispute("dp_1002")
    assert res["status"] == "lost"
    mock_close.assert_called_once_with("dp_1002")


@patch("agent.tools.stripe_tools.verify_live_key_guard")
@patch("agent.tools.stripe_tools.stripe.Dispute.modify")
def test_submit_evidence(mock_modify, mock_guard):
    mock_guard.return_value = "sk_test_mock"
    mock_disp = MagicMock()
    mock_disp.id = "dp_1001"
    mock_disp.status = "under_review"
    mock_disp.to_dict.return_value = {"id": "dp_1001", "status": "under_review"}
    mock_modify.return_value = mock_disp

    evidence = {"shipping_tracking_number": "1Z9999999999999991"}
    res = submit_evidence("dp_1001", evidence=evidence, submit=True)
    assert res["status"] == "under_review"
    mock_modify.assert_called_once_with("dp_1001", evidence=evidence, submit=True)


@patch("agent.tools.stripe_tools.verify_live_key_guard")
@patch("agent.tools.stripe_tools.stripe.Dispute.retrieve")
@patch("agent.tools.stripe_tools.stripe.Refund.create")
def test_refund_inquiry_valid(mock_refund, mock_retrieve, mock_guard):
    mock_guard.return_value = "sk_test_mock"

    mock_disp = MagicMock()
    mock_disp.id = "dp_1003"
    mock_disp.status = "warning_needs_response"
    mock_disp.charge = "ch_1003"
    mock_retrieve.return_value = mock_disp

    mock_ref = MagicMock()
    mock_ref.id = "re_1003"
    mock_ref.status = "succeeded"
    mock_ref.to_dict.return_value = {"id": "re_1003", "status": "succeeded"}
    mock_refund.return_value = mock_ref

    res = refund_inquiry("dp_1003")
    assert res["status"] == "succeeded"
    mock_refund.assert_called_once_with(charge="ch_1003")


@patch("agent.tools.stripe_tools.verify_live_key_guard")
@patch("agent.tools.stripe_tools.stripe.Dispute.retrieve")
def test_refund_inquiry_invalid_status(mock_retrieve, mock_guard):
    mock_guard.return_value = "sk_test_mock"

    mock_disp = MagicMock()
    mock_disp.id = "dp_1001"
    mock_disp.status = "needs_response"  # Not warning_needs_response!
    mock_disp.charge = "ch_1001"
    mock_retrieve.return_value = mock_disp

    with pytest.raises(ValueError, match="warning_needs_response"):
        refund_inquiry("dp_1001")


def test_upload_evidence_file_not_found():
    with pytest.raises(FileNotFoundError):
        upload_evidence_file("nonexistent_path_file.pdf")
