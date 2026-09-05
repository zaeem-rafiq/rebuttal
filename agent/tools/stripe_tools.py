"""
agent/tools/stripe_tools.py

Stripe tools for chargeback defense agent, exposed as Strands @tool functions.
Strictly adheres to the Live-key guard: asserts STRIPE_SECRET_KEY.startswith("sk_test_").

Tools:
    - get_dispute(dispute_id: str) -> dict
    - get_charge_context(charge_id_or_payment_intent: str) -> dict
    - list_open_disputes(limit: int = 10) -> list[dict]
    - upload_evidence_file(file_path: str, purpose: str = "dispute_evidence") -> dict
    - submit_evidence(dispute_id: str, evidence: dict, submit: bool = False) -> dict
    - concede_dispute(dispute_id: str) -> dict
    - refund_inquiry(dispute_id_or_charge: str) -> dict
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import stripe
from dotenv import load_dotenv
from strands import tool

load_dotenv()


def verify_live_key_guard(api_key: Optional[str] = None) -> str:
    """Verify Stripe API key adheres to live-key guard rule.

    Must start with 'sk_test_'. Never allows live keys ('sk_live_').
    Raises RuntimeError / AssertionError if not compliant.
    """
    key = api_key if api_key is not None else os.getenv("STRIPE_SECRET_KEY", "")
    assert key and key.startswith("sk_test_"), (
        f"Live-key guard violation: STRIPE_SECRET_KEY must be configured and start with 'sk_test_'. Got: '{key[:7]}...'"
        if key else "Live-key guard violation: STRIPE_SECRET_KEY is not set in environment."
    )
    stripe.api_key = key
    return key


def serialize_stripe_object(obj: Any) -> Any:
    """Recursively convert Stripe objects or dictionaries to standard Python dicts."""
    if isinstance(obj, dict):
        return {k: serialize_stripe_object(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_stripe_object(item) for item in obj]
    elif hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        d = obj.to_dict()
        if isinstance(d, dict):
            return {k: serialize_stripe_object(v) for k, v in d.items()}
    return obj


@tool
def get_dispute(dispute_id: str) -> Dict[str, Any]:
    """Retrieve details of a dispute by its Stripe dispute ID.

    Parameters:
        dispute_id: The ID of the dispute (e.g. dp_12345).

    Returns:
        Dictionary containing dispute details including id, amount, currency,
        reason, status, evidence_due_by, charge, and payment_intent.
    """
    verify_live_key_guard()
    dispute = stripe.Dispute.retrieve(dispute_id, expand=["charge", "payment_intent"])
    return serialize_stripe_object(dispute)


@tool
def get_charge_context(charge_id_or_payment_intent: str) -> Dict[str, Any]:
    """Retrieve full contextual information about a charge or payment intent.

    Extracts amount, card checks (AVS/CVC), billing details, metadata.order_id,
    and customer email for evidence building and decision evaluation.

    Parameters:
        charge_id_or_payment_intent: Stripe Charge ID (ch_...) or PaymentIntent ID (pi_...).

    Returns:
        Dictionary containing:
            - amount: Amount in cents (int)
            - currency: Currency string (e.g. 'usd')
            - card_checks: Dict with address_line1_check, address_postal_code_check, cvc_check
            - billing_details: Dict with billing address, name, email, phone
            - metadata: Dict of metadata attached to the charge or payment intent (including order_id)
            - customer_email: Customer email string or None
            - payment_intent_id: Associated PaymentIntent ID
            - charge_id: Associated Charge ID
    """
    verify_live_key_guard()

    target_id = charge_id_or_payment_intent.strip()
    payment_intent_obj = None
    charge_obj = None

    if target_id.startswith("pi_"):
        payment_intent_obj = stripe.PaymentIntent.retrieve(
            target_id, expand=["latest_charge", "payment_method"]
        )
        if payment_intent_obj.latest_charge:
            if isinstance(payment_intent_obj.latest_charge, str):
                charge_obj = stripe.Charge.retrieve(payment_intent_obj.latest_charge)
            else:
                charge_obj = payment_intent_obj.latest_charge
    else:
        charge_obj = stripe.Charge.retrieve(
            target_id, expand=["payment_intent", "payment_method"]
        )
        if charge_obj.payment_intent:
            if isinstance(charge_obj.payment_intent, str):
                payment_intent_obj = stripe.PaymentIntent.retrieve(charge_obj.payment_intent)
            else:
                payment_intent_obj = charge_obj.payment_intent

    # Extract amount & currency
    amount = 0
    currency = "usd"
    if charge_obj:
        amount = getattr(charge_obj, "amount", 0)
        currency = getattr(charge_obj, "currency", "usd")
    elif payment_intent_obj:
        amount = getattr(payment_intent_obj, "amount", 0)
        currency = getattr(payment_intent_obj, "currency", "usd")

    # Extract card checks
    card_checks: Dict[str, Any] = {
        "address_line1_check": None,
        "address_postal_code_check": None,
        "cvc_check": None,
    }
    if charge_obj and hasattr(charge_obj, "payment_method_details") and charge_obj.payment_method_details:
        card = getattr(charge_obj.payment_method_details, "card", None)
        if card and hasattr(card, "checks") and card.checks:
            card_checks = {
                "address_line1_check": getattr(card.checks, "address_line1_check", None),
                "address_postal_code_check": getattr(card.checks, "address_postal_code_check", None),
                "cvc_check": getattr(card.checks, "cvc_check", None),
            }

    # Extract billing details
    billing_details: Dict[str, Any] = {}
    if charge_obj and hasattr(charge_obj, "billing_details") and charge_obj.billing_details:
        billing_details = serialize_stripe_object(charge_obj.billing_details)

    # Extract metadata (merge PI and charge metadata, prioritizing order_id)
    metadata: Dict[str, Any] = {}
    if charge_obj and hasattr(charge_obj, "metadata") and charge_obj.metadata:
        metadata.update(serialize_stripe_object(charge_obj.metadata))
    if payment_intent_obj and hasattr(payment_intent_obj, "metadata") and payment_intent_obj.metadata:
        metadata.update(serialize_stripe_object(payment_intent_obj.metadata))

    # Extract customer email
    customer_email = None
    if billing_details.get("email"):
        customer_email = billing_details.get("email")
    elif charge_obj and getattr(charge_obj, "receipt_email", None):
        customer_email = charge_obj.receipt_email
    elif payment_intent_obj and getattr(payment_intent_obj, "receipt_email", None):
        customer_email = payment_intent_obj.receipt_email

    pi_id = payment_intent_obj.id if payment_intent_obj else None
    ch_id = charge_obj.id if charge_obj else None

    return {
        "amount": amount,
        "currency": currency,
        "card_checks": card_checks,
        "billing_details": billing_details,
        "metadata": metadata,
        "customer_email": customer_email,
        "payment_intent_id": pi_id,
        "charge_id": ch_id,
    }


@tool
def list_open_disputes(limit: int = 10) -> List[Dict[str, Any]]:
    """List open disputes that need attention or response.

    Parameters:
        limit: Maximum number of disputes to retrieve (default: 10).

    Returns:
        List of dispute dictionaries.
    """
    verify_live_key_guard()
    disputes = stripe.Dispute.list(limit=limit)
    return [serialize_stripe_object(d) for d in disputes.data]


@tool
def upload_evidence_file(file_path: str, purpose: str = "dispute_evidence") -> Dict[str, Any]:
    """Upload an evidence file to Stripe Files API for dispute defense.

    Parameters:
        file_path: Local path to file (PDF, PNG, JPG, text, etc.).
        purpose: Purpose of the upload (default: 'dispute_evidence').

    Returns:
        Dictionary containing file ID, purpose, filename, and size.
    """
    verify_live_key_guard()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Evidence file not found: {file_path}")

    with open(path, "rb") as f:
        file_obj = stripe.File.create(file=f, purpose=purpose)
    return serialize_stripe_object(file_obj)


@tool
def submit_evidence(dispute_id: str, evidence: Dict[str, Any], submit: bool = False) -> Dict[str, Any]:
    """Update or officially submit evidence for a Stripe dispute.

    Parameters:
        dispute_id: ID of the dispute.
        evidence: Evidence dictionary (e.g. tracking_number, customer_communication, uncategorized_file).
        submit: If True, evidence is submitted to the card network and cannot be changed. Default False.

    Returns:
        Dictionary of the updated dispute.
    """
    verify_live_key_guard()
    updated = stripe.Dispute.modify(dispute_id, evidence=evidence, submit=submit)
    return serialize_stripe_object(updated)


@tool
def concede_dispute(dispute_id: str) -> Dict[str, Any]:
    """Concede a dispute by closing it with Stripe without submitting evidence.

    Calls Dispute.close under the hood.

    Parameters:
        dispute_id: ID of the dispute to concede.

    Returns:
        Dictionary of the closed dispute.
    """
    verify_live_key_guard()
    closed = stripe.Dispute.close(dispute_id)
    return serialize_stripe_object(closed)


@tool
def refund_inquiry(dispute_id_or_charge: str) -> Dict[str, Any]:
    """Issue a refund for an inquiry (pre-chargeback stage).

    Only valid when dispute status is 'warning_needs_response'.
    Refunding during the inquiry stage resolves the dispute without incurring chargeback fees.

    Parameters:
        dispute_id_or_charge: Dispute ID (dp_...) or Charge ID (ch_...) with an active inquiry.

    Returns:
        Dictionary containing the refund object.

    Raises:
        ValueError: If the dispute is not in 'warning_needs_response' status.
    """
    verify_live_key_guard()

    target = dispute_id_or_charge.strip()
    charge_id: Optional[str] = None
    dispute_status: Optional[str] = None

    if target.startswith("dp_"):
        dispute = stripe.Dispute.retrieve(target, expand=["charge"])
        dispute_status = getattr(dispute, "status", None)
        if dispute.charge:
            charge_id = dispute.charge.id if hasattr(dispute.charge, "id") else str(dispute.charge)
    else:
        charge = stripe.Charge.retrieve(target, expand=["dispute"])
        charge_id = charge.id
        if hasattr(charge, "dispute") and charge.dispute:
            dispute_status = getattr(charge.dispute, "status", None)

    if dispute_status != "warning_needs_response":
        raise ValueError(
            f"refund_inquiry is only valid when dispute status is 'warning_needs_response', got '{dispute_status}'"
        )

    if not charge_id:
        raise ValueError(f"Could not determine charge ID for refund from target '{target}'")

    refund = stripe.Refund.create(charge=charge_id)
    return serialize_stripe_object(refund)
