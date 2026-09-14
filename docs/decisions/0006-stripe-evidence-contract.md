# Stripe evidence contract correction

The final output trace is EvidencePacket -> execute_strategy or executor agent ->
submit_evidence -> Stripe.Dispute.modify. The source contract was verified against
the installed Stripe SDK params/_dispute_modify_params.py and official API:
https://docs.stripe.com/api/disputes/update?api-version=2024-09-30.acacia
and category-specific guidance:
https://docs.stripe.com/disputes/categories?dispute-category=subscription-canceled

The SDK uses refund-policy wording for cancellation_policy_disclosure. The
category guide explicitly describes cancellation-policy disclosure, which is the
source for the distinction in model guidance; the requirement for actual
pre-purchase exposure is consistent in both sources.

The supported communication field accepts an uploaded Stripe file ID, not text.
Shipping/service documentation and uncategorized_file have the same file-ID
requirement. A shared validator now covers the model and direct submission tool;
the graph additionally rejects every artifact because collectors produce none.
Message excerpts remain in narrative or supplementary text.

Policy-disclosure fields require evidence of disclosure before purchase. Policy
contents alone are insufficient. The previous positive explicit_cancellation_policy
control therefore encoded a wrong API expectation. It is preserved in historical
reports, replaced in current controls by a negative policy-content case and genuine
positive disclosure cases. A separate refund disclosure pair was added. The
reference-only-outside-narrative control moved its text from the file-ID field to
uncategorized_text, retaining its original narrative-citation expectation.

Direct fight execution now requires a packet and nonempty narrative, rejects
unsupported files lists, revalidates mutable packet fields, and checks the final
combined text before audit/upload. It no longer fabricates fallback evidence.
Narrative plus supplementary text survives the uploaded dossier and non-demo
submission; the documented demo winning_evidence token remains isolated. Both
disclosure fields and uncategorized_text enforce Stripe's 20,000-character limit.
The inquiry tool description no longer promises future resolution or avoided fees.

The existing broad judge retains all factual checks. A focused outcome extractor
is retained separately from a new premise check for event absence, event order,
and actual policy disclosure. All required premise booleans must be true; missing,
string-valued, and failed results fail closed. Exact duplicate narrative text is
sent once to grounding checks, while differing sibling text remains independently
audited. These evaluator changes require current controls and fresh generation
verification; offline mocks do not prove model accuracy.

Malformed structured model output is retained in a typed pipeline rejection,
including raw fields, validation error, graph usage, and collected source records.
It is never constructed as valid evidence or sent to execution.

## Physical delivery fields

Source review of the next candidate found digital access references mapped into
physical shipping fields (cases 12, 13, 16). The installed Stripe SDK parameter
descriptions define shipping_address, shipping_carrier, shipping_date, and
shipping_tracking_number for physical products. The EvidencePacket descriptions
and shared generator contract now say so; digital access references remain usable
in narrative/uncategorized_text. Positive/negative controls audit this distinction.
No new product field or API parameter was added.
