"""agent/models.py - Canonical Pydantic schemas for Rebuttal.

NOTE: This file becomes protected after completion of R-02.
Any future changes require an Architectural Decision Record in docs/decisions/.
"""

from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class DisputeStrategy(BaseModel):
    """The recommended action and risk calculus produced by the Strategy agent."""
    action: Literal["fight", "concede", "refund_inquiry"] = Field(
        ...,
        description="The recommended dispute action: 'fight' (submit evidence), 'concede' (accept loss/no fight), or 'refund_inquiry' (refund during inquiry stage)."
    )
    win_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated probability of winning the dispute (0.0 to 1.0)."
    )
    expected_value_cents: int = Field(
        ...,
        description="Calculated expected dollar value in cents (win_prob * amount - loss_prob * fee)."
    )
    customer_value: Literal["new", "repeat", "vip"] = Field(
        ...,
        description="Customer classification based on order history and lifetime value."
    )
    evidence_strength: Literal["weak", "mixed", "strong"] = Field(
        ...,
        description="Strength of merchant's documentation against the card network dispute reason."
    )
    rationale: str = Field(
        ...,
        description="Concise strategic rationale for merchant decision (max 80 words)."
    )
    owner_summary: str = Field(
        ...,
        description="Plain-English summary suitable for SMS to merchant owner (max 320 characters)."
    )

    @field_validator("rationale")
    @classmethod
    def validate_rationale_words(cls, v: str) -> str:
        words = v.strip().split()
        if len(words) > 80:
            raise ValueError(f"Rationale exceeds 80 words ({len(words)} words)")
        return v

    @field_validator("owner_summary")
    @classmethod
    def validate_owner_summary_chars(cls, v: str) -> str:
        if len(v) > 320:
            raise ValueError(f"Owner summary exceeds 320 characters ({len(v)} chars)")
        return v


class EvidencePacket(BaseModel):
    """The complete evidence packet ready for submission to Stripe Dispute Evidence API."""
    customer_name: Optional[str] = Field(None, description="Full customer name.")
    customer_email_address: Optional[str] = Field(None, description="Customer email address.")
    billing_address: Optional[str] = Field(None, description="Billing address string.")
    shipping_address: Optional[str] = Field(None, description="Shipping destination address.")
    shipping_carrier: Optional[str] = Field(None, description="Carrier name (e.g. UPS, FedEx, USPS).")
    shipping_tracking_number: Optional[str] = Field(None, description="Tracking number with carrier.")
    shipping_date: Optional[str] = Field(None, description="Date shipped (YYYY-MM-DD).")
    shipping_documentation: Optional[str] = Field(None, description="File ID or path for proof of delivery.")
    service_documentation: Optional[str] = Field(None, description="File ID or path for service documentation.")
    customer_communication: Optional[str] = Field(None, description="Communication threads or transcripts.")
    refund_policy_disclosure: Optional[str] = Field(None, description="Copy of merchant return/refund policy.")
    cancellation_policy_disclosure: Optional[str] = Field(None, description="Copy of cancellation policy.")
    uncategorized_text: Optional[str] = Field(None, description="Supplementary evidence notes.")
    uncategorized_file: Optional[str] = Field(None, description="Additional file upload ID.")
    narrative: str = Field(
        ...,
        description="Structured dispute narrative explaining why the dispute is invalid with timeline of events."
    )
    files: List[str] = Field(
        default_factory=list,
        description="List of file paths or Stripe file IDs included in the evidence packet."
    )


class OrderEvidence(BaseModel):
    """Evidence collected from the orders database."""
    order_id: str
    customer_id: str
    amount_cents: int
    currency: str = "usd"
    status: str
    card_brand: Optional[str] = None
    card_last4: Optional[str] = None
    avs_postal_match: Optional[str] = None
    avs_line1_match: Optional[str] = None
    cvc_check: Optional[str] = None
    items: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[str] = None


class ShippingEvidence(BaseModel):
    """Evidence collected from the shipments database."""
    order_id: str
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    status: Optional[str] = None
    shipped_at: Optional[str] = None
    delivered_at: Optional[str] = None
    signed_by: Optional[str] = None
    events: List[Dict[str, Any]] = Field(default_factory=list)


class CommsEvidence(BaseModel):
    """Evidence collected from customer messages."""
    customer_id: str
    order_id: Optional[str] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    has_cancellation_request: bool = False
    has_address_change_request: bool = False
    has_inquiry: bool = False


class HistoryEvidence(BaseModel):
    """Evidence collected from customer order history and merchant policy."""
    customer_id: str
    total_prior_orders: int = 0
    total_prior_spend_cents: int = 0
    prior_disputes: int = 0
    customer_tier: Literal["new", "repeat", "vip"] = "new"
    policy: Dict[str, Any] = Field(default_factory=dict)
