"""agent/models.py - Canonical Pydantic schemas for Rebuttal.

NOTE: This file becomes protected after completion of R-02.
Any future changes require an Architectural Decision Record in docs/decisions/.
"""

from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re


STRIPE_FILE_FIELDS = ("shipping_documentation", "service_documentation", "customer_communication", "uncategorized_file")


def validate_stripe_file_references(evidence):
    """Stripe attachment fields accept uploaded file IDs, never text or paths."""
    for field in STRIPE_FILE_FIELDS:
        value = evidence.get(field)
        if value is not None and (not isinstance(value, str) or not re.fullmatch(r"file_[A-Za-z0-9]+", value)):
            raise ValueError(f"{field} must be an uploaded Stripe file ID")


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
        description="Internal expected value estimate in cents. Use only documented fee amounts; when fees are unknown, use zero as a calculation assumption, never claim fees are zero. Concession and inquiry recommendations use zero."
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
        description="Source-backed observations explaining the proposed action, max 80 words. Convert source cents to dollars by dividing by 100. Recommendations are not completed actions or guarantees of resolution, prevention of escalation, retention, savings, or fee avoidance. Cite merchant policy only when the retrieved policy states that rule."
    )
    owner_summary: str = Field(
        ...,
        description="Begin with Recommend; state the proposed action and its recorded factual basis only, max 320 characters. No promises of resolution, prevention of escalation, retention, relationship preservation, savings, fee avoidance, or completed execution."
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
    shipping_tracking_number: Optional[str] = Field(None, description="Tracking number; put the carrier in shipping_carrier.")
    shipping_date: Optional[str] = Field(None, description="Date shipped (YYYY-MM-DD).")
    shipping_documentation: Optional[str] = Field(None, description="Uploaded Stripe file ID for proof of delivery, otherwise null.")
    service_documentation: Optional[str] = Field(None, description="Uploaded Stripe file ID for service documentation, otherwise null.")
    customer_communication: Optional[str] = Field(None, description="Uploaded Stripe file ID for communications, otherwise null. Put supported message excerpts in narrative or uncategorized_text.")
    refund_policy_disclosure: Optional[str] = Field(None, max_length=20000, description="Recorded evidence that this customer was shown the refund policy before purchase, otherwise null. Policy contents alone do not establish disclosure.")
    cancellation_policy_disclosure: Optional[str] = Field(None, max_length=20000, description="Recorded explanation of how and when this customer was shown the cancellation policy before purchase, otherwise null. Policy contents alone do not establish disclosure.")
    uncategorized_text: Optional[str] = Field(None, max_length=20000, description="Supplementary evidence notes.")
    uncategorized_file: Optional[str] = Field(None, description="Additional file upload ID.")
    narrative: str = Field(
        ...,
        description="Narrative of recorded observations and a separately labeled proposed response. Include relevant support ticket and shipment tracking identifiers in this narrative. Dates must describe their recorded event, not a current status inferred from created_at. Before/after claims require both event times or an explicit source statement. Scope absence findings to supplied records; missing records do not establish that an event never happened. Quote messages as communications records unless sender/direction or unambiguous first-person subject/body content supports authorship. Do not conclude authorization, identity, or agreement compliance from checks, delivery, timing, or an acknowledgment of unseen terms. No retention or savings promises. Scope policy claims to retrieved rules."
    )
    files: List[str] = Field(
        default_factory=list,
        description="List of file paths or Stripe file IDs included in the evidence packet."
    )

    @field_validator(*STRIPE_FILE_FIELDS)
    @classmethod
    def validate_file_reference(cls, value, info):
        validate_stripe_file_references({info.field_name: value})
        return value


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
