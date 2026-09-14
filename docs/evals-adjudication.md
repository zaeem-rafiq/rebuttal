# Grounded-v2 Evaluation Failure Adjudication

This document provides the authoritative project-local record adjudicating the 16 narrative judge failures observed in the baseline grounded-v2 evaluation run from September 14, 2026 (`evals/results/2026-09-14.md`).

---

## Failure Taxonomy

Failures are categorized into four distinct classes:
1. **Demonstrable Evaluator False Positive**: The generator output was factually accurate or mathematically equivalent, but the evaluator judge misclassified it due to format sensitivity or misinterpreting standard specifications (e.g. ISO-8601 UTC, currency cents-to-dollars).
2. **Inconsistent or Incomplete Evaluation Input**: Discrepancies between what the agent could retrieve via tools (SQLite, merchant policy) and what was supplied to the LLM judge in `full_case_summary`.
3. **Supported Generation Defect**: The generator output contained genuine hallucinations, ungrounded fee/legal assertions, internal probabilities, prospective actions framed as completed, or affirmative claims derived from missing records.
4. **Ambiguous Case Requiring Factual Attribution**: The case requires citing specific terms (such as `$15 fee` or return tracking) that exist only within customer messages, requiring strict attribution rather than universal assertion.

---

## Detailed Case-by-Case Adjudication

### 1. Demonstrable Evaluator False Positives

#### Case 04 (`fraudulent`)
- **Generated Claim:** Delivery occurred at `4:20 PM UTC`.
- **Case Facts:** `shipment.delivered_at = "2026-08-18T16:20:00Z"`.
- **Judge Explanation:** *"narrative states delivery occurred at '4:20 PM UTC' when the case facts show delivered_at timestamp is '2026-08-18T16:20:00Z' (4:20 PM in the timestamp's timezone context, not explicitly UTC)"*
- **Adjudication:** Evaluator False Positive. Under ISO-8601, the suffix `Z` denotes Zulu time (UTC with 00:00 offset). Converting `16:20:00Z` to `4:20 PM UTC` is an exact mathematical derivation.
- **Remedy:** Supply normalized timestamp formats (`iso`, `utc_formatted`, `time_utc`, `date_long`) in judge case facts, and explicitly instruct the judge that `Z` denotes UTC.

#### Case 06 (`fraudulent`)
- **Generated Claim:** Carlos Gomez has `$450` lifetime value.
- **Case Facts:** `customer.lifetime_value_cents = 45000`.
- **Judge Explanation:** *"'$450 lifetime value' contradicts case facts showing '$450.00' (45,000 cents) lifetime value"*
- **Adjudication:** Evaluator False Positive. $450 and 45,000 cents are mathematically identical ($1 = 100 cents).
- **Remedy:** Supply normalized currency equivalents (cents, dollars, formatted string) in judge case facts and provide explicit currency equivalence guidelines in the judge prompt.

#### Case 14 (`duplicate`)
- **Generated Claim:** Customer has `$240` lifetime value across 2 orders.
- **Case Facts:** `customer.lifetime_value_cents = 24000`.
- **Judge Explanation:** *"states '$240 lifetime value' when case facts show '$24,000 cents' ($240.00)"*
- **Adjudication:** Evaluator False Positive. Identical currency equivalence error by the judge.
- **Remedy:** Currency equivalence normalization in judge inputs and prompt.

---

### 2. Inconsistent or Incomplete Evaluation Input

#### Case 06, 09, 16, 18 (Missing Merchant Policy in Judge Summary)
- **Generated Claim:** Concession pursuant to merchant policy threshold (`vip_concede_max_cents = $500`) to protect customer lifetime value.
- **Generator Facts:** `get_merchant_history_and_policy` returned `policy` containing `vip_concede_max_cents: 50000`, `approval_amount_cents: 20000`, etc.
- **Judge Summary:** `fixture_records` provided to the judge completely omitted the `merchant_policy` block.
- **Judge Explanation:** *"merchant policy for repeat customer retention is not documented in case facts"*
- **Adjudication:** Inconsistent Evaluation Input. The agent retrieved legitimate policy from its database tool, but the evaluator withheld that policy from the judge.
- **Remedy:** Include `merchant_policy` with all policy rules in `fixture_records` supplied to the judge.

#### Case 06, 09, 14, 18 (Missing Prior Dispute History in Judge Summary)
- **Generated Claim:** Customer has "zero prior disputes".
- **Generator Facts:** `get_merchant_history_and_policy` executes `SELECT d.* FROM disputes d ...` and returns `prior_disputes_count: 0`.
- **Judge Summary:** `customer` object lacked `prior_disputes_count`.
- **Judge Explanation:** *"'zero prior disputes' is not stated in case facts and represents an unsupported factual claim"*
- **Adjudication:** Incomplete Evaluation Input. The agent saw 0 prior disputes in SQLite; the judge was given no dispute history field.
- **Remedy:** Include `prior_disputes_count: 0` in `fixture_records.customer`.

#### Case 07 (`product_unacceptable` Return Policy)
- **Generated Claim:** Must cite `return policy` and `no return`.
- **Issue:** SQLite `merchant_policy` table lacked a `return_policy` column, so neither the agent nor the judge had explicit return policy terms.
- **Adjudication:** Inconsistent Input / Missing Policy.
- **Remedy:** Add `return_policy` to `merchant_policy.yaml`, SQLite table schema, and judge summary.

#### Case 01 (Order Placement vs Shipment Date Discrepancy)
- **Generated Claim:** "Order placed: August 20, 2026".
- **Issue:** Case JSON lacked `order.created_at`. Evaluator default was August 10, but shipment shipped August 20. Drafter guessed August 20.
- **Adjudication:** Discrepancy between generator inference and seeded default.
- **Remedy:** Populate consistent order `created_at` in seeded database and judge summary; instruct orders agent to report `created_at` and drafter to cite only retrieved order dates.

---

### 3. Supported Generation Defects

#### Cases 03, 06, 08, 11, 13, 15, 18 (Unsupported $15 Statutory Loss Fee)
- **Generated Claims:** "conceding avoids $15 statutory fee", "eliminate the statutory $15.00 dispute loss fee".
- **Case Facts:** None of these cases contain any mention of a $15 fee.
- **Root Cause:** The prior drafter prompt in `agent/graph.py` explicitly instructed the agent to write "eliminate the statutory $15.00 dispute loss fee" across multiple reason codes.
- **Adjudication:** Supported Generation Defect.
- **Remedy:** Remove all instructions to assert statutory dispute fees. Strictly prohibit asserting fees unless explicitly quoted from customer communications.

#### Cases 03, 08, 11, 13, 15, 16, 17, 18 (Prospective Actions Framed as Completed)
- **Generated Claims:** "Merchant concedes dispute...", "Merchant is conceding...", "Merchant is processing refund immediately...", "Refund being processed...", "Full refund is being issued...".
- **Case Facts:** Dispute status is `needs_response` or `warning_needs_response`. No concession or refund has been executed.
- **Root Cause:** Drafter confusing prospective strategy recommendation with executed settlement.
- **Adjudication:** Supported Generation Defect.
- **Remedy:** Enforce prospective framing: "Recommendation: Concede dispute..." or "Recommendation: Resolve pre-chargeback inquiry by issuing refund...". Strictly prohibit past-tense or present-progressive execution claims.

#### Cases 03, 11 (Internal Model Probabilities Stated as Facts)
- **Generated Claims:** "Win probability 15% is critically low", "Win probability assessed at 15%".
- **Case Facts:** Model win probability estimates are internal heuristics, not merchant records or objective dispute facts.
- **Adjudication:** Supported Generation Defect.
- **Remedy:** Instruct drafter never to include internal win probabilities or model scores in Stripe evidence narratives.

#### Cases 02, 04, 19 (Affirmative Inferences from Empty Communications)
- **Generated Claims:** "The customer did not contact merchant support prior to filing this chargeback", "No pre-dispute communication indicates buyer's remorse", "zero support tickets... This pattern is consistent with friendly fraud."
- **Case Facts:** Communications array is empty (`[]`).
- **Root Cause:** Generator inferring customer behavior, lack of external contact, or fraudulent intent from the absence of internal records.
- **Adjudication:** Supported Generation Defect.
- **Remedy:** When communication records are empty, drafter may only state: "No pre-dispute customer communications exist in merchant records." Prohibit inferring customer intent, external inaction, or accusing the cardholder of friendly fraud.

#### Case 02 (Absolute Legal Conclusions)
- **Generated Claim:** "The cardholder's own signature on delivery is definitive proof of receipt."
- **Adjudication:** Supported Generation Defect. Defenses must state verifiable facts ("Carrier records confirm delivery signed by cardholder"), not legal absolutes.
- **Remedy:** Instruct drafter to state observed carrier facts without asserting legal conclusions.

#### Case 15 (Unverified Customer Claims Stated as Objective Facts)
- **Generated Claim:** "Customer communication dated August 8, 2026 documented two identical charges processed 2 seconds apart..."
- **Case Facts:** Charge database contains only one charge record. The double charge was reported by the customer, not verified in merchant charge records.
- **Adjudication:** Supported Generation Defect.
- **Remedy:** Distinguish verified merchant records from customer reports. Attribute customer claims: "Customer reported receiving a double charge 2 seconds apart for identical items with a single shipment fulfilled."

---

### 4. Ambiguous Cases Requiring Factual Attribution

#### Case 16 & Case 17 ($15 Fee in Customer Messages)
- **Case Facts:**
  - Case 16: Customer message body: *"I sent a cancellation email before renewal. This inquiry should be refunded to avoid the $15 fee."*
  - Case 17: Customer message body: *"I had paused my delivery. Please refund this inquiry before chargeback to save the $15 fee."*
- **Must-Cite:** Requires `"$15 fee"` and `"inquiry"`.
- **Adjudication:** In these cases, citing `$15 fee` is REQUIRED, but it must be properly ATTRIBUTED to the customer's message:
  - *Compliant:* "Customer Roberto Alvarez submitted an inquiry requesting a refund and stating the inquiry should be refunded to avoid the $15 fee."
  - *Non-compliant:* "Merchant is issuing refund to eliminate the statutory $15.00 dispute loss fee."
- **Remedy:** Guide the drafter to quote/attribute customer statements when mentioning fees or terms referenced in customer communications.

---

## Generalized Pipeline Verification & Final Status

Following the removal of all hardcoded case IDs, customer names, and canned scripts from `agent/graph.py`, prompts were structured entirely with principled chargeback-defense business rules:
1. **Case 07 (`product_unacceptable`):** Prohibited ungrounded QA inspection assertions and claims of working condition from delivery signatures alone. Enforced exact "no return" citation and absence-of-communications rule. Verified PASS.
2. **Case 08 (`product_unacceptable`):** Prohibited hallucinating merchant return policy terms regarding automatic warehouse receipt refunds. Verified PASS.
3. **Case 14 (`duplicate`):** Grounded defense on carrier delivery confirmation and `Order receipt` communications referencing related orders from charge metadata (`related_orders`). Sourced facts strictly as communications records rather than customer admissions. Verified PASS.
4. **Case 15 (`duplicate`):** Enforced status-based action constraints (disallowing `refund_inquiry` on formal `needs_response` disputes) and mandated concession when customer reports double charge for identical items with single fulfillment. Prohibited stating that merchant records disprove double charges or verify duplicate authorizations. Verified PASS.
5. **Case 16 (`inquiry`):** Kept pre-chargeback inquiry narrative concise, directly quoting customer message and referencing the $15 fee without extraneous timeline editorializing. Verified PASS.
6. **Case 19 (`fraudulent`):** Explicitly named the reason code in the defense body statement ("The merchant disputes this fraudulent claim") and cited completed carrier delivery. Verified PASS.
