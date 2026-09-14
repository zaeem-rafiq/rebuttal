# Structured output descriptions must match the proposed action

The previous EvidencePacket narrative description demanded an argument that the
dispute was invalid, including when strategy recommended concession. The expected
value description demanded a fee operand even when source records omitted fees.
These descriptions are model instructions as well as schema documentation.

Clarify prospective, action-appropriate narratives and explicit internal handling
of unknown fees. Field names, types, validators, and serialized contracts remain
unchanged. Known fees may still be cited from supplied transaction records.

Consumers traced: graph structured outputs and fallback extraction, executor,
Stripe evidence formatting, owner approval notifications, and evaluation harness.
Existing schema and pipeline tests plus Bedrock evaluations verify the change.

Live output still asserted relationship preservation and fee avoidance despite
the system prompt. The rationale/owner-summary schema descriptions now carry
the same observation-only contract at the structured-output tool boundary. The
narrative description also prohibits unsupported outcome and policy promises.
This changes model guidance, not the serialized fields or runtime guarantees.

Further observed errors confused record creation with refund timing, omitted a
support ticket from the narrative, and inferred authorization from an acknowledgment
of unseen terms. The narrative description now requests recorded observations,
event-specific dates, narrative citations, and source-attributed messages.
