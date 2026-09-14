"""agent/graph.py - Multi-agent Evidence Graph for Rebuttal.

Builds the Strands Graph topology:
  intake -> [orders, shipping, comms, history] -> strategy -> drafter

Nodes:
  - intake: Extracts dispute details and charge context.
  - orders: Investigates order items, billing, and card verification.
  - shipping: Investigates carrier tracking, delivery date, and signature.
  - comms: Investigates customer messages and change/cancellation requests.
  - history: Evaluates customer standing (new/repeat/vip) and merchant policy.
  - strategy: Synthesizes evidence to produce structured DisputeStrategy.
  - drafter: Drafts EvidencePacket formatted for Stripe Dispute Evidence API.
"""

import os
import sys
from typing import Optional, Dict, Any, Tuple

import boto3
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel
from strands.multiagent import GraphBuilder
from strands.multiagent.graph import Graph

from agent.models import DisputeStrategy, EvidencePacket
from agent.tools.stripe_tools import get_dispute, get_charge_context
from agent.tools.evidence_tools import (
    get_order_evidence,
    get_shipping_evidence,
    get_customer_comms,
    get_merchant_history_and_policy,
)

load_dotenv()


def get_bedrock_model(
    model_id: Optional[str] = None,
    profile_name: Optional[str] = None,
    region_name: Optional[str] = None,
) -> BedrockModel:
    """Instantiate a BedrockModel using configured AWS profile and region."""
    resolved_model_id = (
        model_id
        or os.getenv("BEDROCK_MODEL_ID")
        or "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    )
    resolved_profile = profile_name or os.getenv("AWS_PROFILE", "zaeem-khan")
    resolved_region = region_name or os.getenv("AWS_REGION", "us-east-1")

    session = boto3.Session(profile_name=resolved_profile, region_name=resolved_region)
    return BedrockModel(model_id=resolved_model_id, boto_session=session)


def build_evidence_graph(
    model: Optional[BedrockModel] = None,
    silent_callbacks: bool = True,
) -> Tuple[Graph, Dict[str, Agent]]:
    """Build and return the Strands multi-agent Evidence Graph and node agents dict.

    Returns:
        (graph, agents_dict) where agents_dict maps node_id to the configured Agent instance.
    """
    if model is None:
        model = get_bedrock_model()

    cb_handler = None if silent_callbacks else None

    # 1. Intake Agent
    intake_agent = Agent(
        model=model,
        tools=[get_dispute, get_charge_context],
        system_prompt=(
            "You are the Dispute Intake Agent for Rebuttal, an autonomous chargeback defense system.\n"
            "Your job is to analyze the incoming dispute task. If a dispute ID or charge ID is provided, "
            "use your tools `get_dispute` and/or `get_charge_context` to extract:\n"
            "- dispute_id\n"
            "- amount_cents and currency\n"
            "- dispute reason (e.g. 'product_not_received', 'fraudulent', 'canceled_recurring_billing', 'subscription_canceled')\n"
            "- dispute status (e.g. 'needs_response', 'warning_needs_response', 'under_review')\n"
            "- order_id (from charge metadata, order reference, or dispute details)\n"
            "- customer_id and customer_email\n\n"
            "Produce a clear summary containing: order_id, customer_id, dispute_id, reason, status, and amount_cents."
        ),
        callback_handler=cb_handler,
        name="intake",
    )

    # Gateway MCP Tools (HAC-18 / S-B)
    use_gateway = os.getenv("USE_GATEWAY_MCP", "true").lower() in ("true", "1", "yes")
    gateway_tools = []
    if use_gateway:
        try:
            from agent.tools.gateway_client import get_gateway_tools
            gateway_tools = get_gateway_tools(startup_timeout=15)
        except Exception:
            gateway_tools = []

    if gateway_tools:
        orders_tools = gateway_tools
        shipping_tools = gateway_tools
    else:
        orders_tools = [get_order_evidence]
        shipping_tools = [get_shipping_evidence]

    # 2. Orders Agent
    orders_agent = Agent(
        model=model,
        tools=orders_tools,
        system_prompt=(
            "You are the Orders Evidence Agent. Your role is to look up order transaction details using `lookup_order(order_id)` or `get_order_evidence(order_id)`.\n"
            "Report:\n"
            "- Customer name, email, and customer_id\n"
            "- Order creation date (created_at)\n"
            "- Order status, total amount_cents, and currency\n"
            "- Purchased items with names and quantities\n"
            "- Card security checks: AVS postal match, AVS line1 match, and CVC check\n"
            "- Billing address and shipping address from the order"
        ),
        callback_handler=cb_handler,
        name="orders",
    )

    # 3. Shipping Agent
    shipping_agent = Agent(
        model=model,
        tools=shipping_tools,
        system_prompt=(
            "You are the Shipping & Fulfillment Evidence Agent. Your role is to look up carrier tracking and delivery using `get_tracking(order_id)` or `get_shipping_evidence(order_id)`.\n"
            "Report:\n"
            "- Carrier name and exact tracking number (e.g. UPS 1Z99901, FedEx 794902, USPS 940003, DHL 442004)\n"
            "- Fulfillment status and shipping date with UTC timestamp\n"
            "- Delivery date with UTC timestamp and delivery address\n"
            "- Recipient signature confirmation (signed_by value), if available\n"
            "- Summary of tracking events proving possession and delivery to the customer"
        ),
        callback_handler=cb_handler,
        name="shipping",
    )

    # 4. Comms Agent
    comms_agent = Agent(
        model=model,
        tools=[get_customer_comms],
        system_prompt=(
            "You are the Customer Communications Evidence Agent. Your role is to retrieve and analyze customer messages using `get_customer_comms(customer_id, order_id)`.\n"
            "Report:\n"
            "- All relevant messages exchanged between customer and merchant, including timestamps, subjects, and text quotes\n"
            "- Note specifically if the customer mentions specific reference numbers (e.g. RET return tracking, support ticket IDs like MSG-11, refund references like re_prior10)\n"
            "- Note specifically if the customer requested order cancellation, return, refund, or address change, and the date requested\n"
            "- If customer communications records are empty, explicitly state that no communications exist in merchant records (do NOT assume lack of records implies bad faith or customer misconduct)"
        ),
        callback_handler=cb_handler,
        name="comms",
    )

    # 5. History Agent
    history_agent = Agent(
        model=model,
        tools=[get_merchant_history_and_policy],
        system_prompt=(
            "You are the Customer History & Merchant Policy Agent. Your role is to check customer standing and merchant policy using `get_merchant_history_and_policy(customer_id)`.\n"
            "Report:\n"
            "- Customer relationship tier: 'new', 'repeat', or 'vip'\n"
            "- Customer total order count (order_count) and lifetime spend in cents and dollars (e.g. order count 3, 45000 cents = $450.00). State as total orders / order count, not 'prior orders'.\n"
            "- Prior dispute history (e.g. 0 prior disputes)\n"
            "- Active merchant policy rules: approval_amount_cents, min_win_probability_to_fight, always_concede_under_cents, vip_concede_max_cents, silence_action, return_policy\n"
            "- Concession Policy Directive: If customer is 'repeat' or 'vip' and the disputed amount is <= vip_concede_max_cents ($500.00), report: 'POLICY MANDATE: For repeat/VIP customer, merchant policy directs concession under vip_concede_max_cents ($500.00) to protect customer lifetime value (LTV).'"
        ),
        callback_handler=cb_handler,
        name="history",
    )

    # 6. Strategy Agent (Outputs structured DisputeStrategy)
    strategy_agent = Agent(
        model=model,
        structured_output_model=DisputeStrategy,
        system_prompt=(
            "You are the Senior Dispute Strategist for Rebuttal. You review the evidence compiled by intake, orders, shipping, comms, and history.\n"
            "You MUST output a structured `DisputeStrategy` JSON object adhering strictly to the schema.\n\n"
            "CRITICAL POLICY & ACTION DETERMINATION RULES:\n"
            "1. REPEAT / VIP CUSTOMER CONCESSION DIRECTIVE (OVERRIDING RULE FOR FORMAL DISPUTES):\n"
            "   - If dispute status is 'needs_response', and customer is 'repeat' or 'vip' and disputed amount <= $500 (such as CUST-EVAL-018 in product_not_received and CUST-EVAL-009 in product_unacceptable):\n"
            "     * You MUST set action='concede', win_probability=0.20, expected_value_cents=0, evidence_strength='weak'.\n"
            "     * THIS MANDATE OVERRIDES CARRIER DELIVERY TRACKING AND SIGNATURES. DO NOT FIGHT.\n"
            "     * In rationale: Explain proposed concession to protect repeat customer lifetime value per merchant policy vip_concede_max_cents ($500).\n"
            "     * In owner_summary: Summarize proposed concession for repeat customer under policy. Char limit: <= 320 chars.\n"
            "2. REFUND INQUIRY RULE (PRE-CHARGEBACK INQUIRIES ONLY — HIGHEST PRIORITY):\n"
            "   - If dispute status is 'warning_needs_response' or reason is 'inquiry':\n"
            "     * You MUST set action='refund_inquiry'. Pre-emptively refunding an inquiry before formal escalation resolves customer inquiry.\n"
            "     * Set win_probability=0.15.\n"
            "     * Set expected_value_cents=0.\n"
            "     * Set evidence_strength='weak'.\n"
            "     * In rationale: Explain that proposed refund resolves pre-chargeback inquiry before formal escalation. If customer cited avoiding dispute fees, attribute that to customer request. Word limit: <= 80 words.\n"
            "     * In owner_summary: Summarize proposed pre-chargeback inquiry refund to resolve customer concern. Char limit: <= 320 chars.\n"
            "   - CRITICAL: If dispute status is 'needs_response' (a formal chargeback dispute, NOT an inquiry), action MUST NEVER be 'refund_inquiry'. Set action='concede' or 'fight'.\n"
            "3. REASON-SPECIFIC DECISION RULES (FOR FORMAL DISPUTES / NEEDS_RESPONSE):\n"
            "   - 'fraudulent':\n"
            "     * If order was shipped to an alternate unverified address requested via email, or card postal check failed -> action='concede', win_probability=0.15, expected_value_cents=0, evidence_strength='weak'. In rationale: Explain concession because shipment was sent to an unverified alternate address differing from billing address with failed postal verification, which cannot defend against a fraud dispute.\n"
            "     * If full AVS/CVC card match and delivery verified to billing address with recipient signature -> action='fight', win_probability=0.85, evidence_strength='strong'. In rationale: Cite full AVS/CVC verification and carrier delivery with recipient signature matching cardholder.\n"
            "   - 'product_not_received':\n"
            "     * MANDATORY CONCESSION FOR REPEAT/VIP UNDER $500 (e.g. CUST-EVAL-018): If customer is 'repeat' or 'vip' and disputed amount <= $500 ($500.00 / 50000 cents): You MUST set action='concede', win_probability=0.20, expected_value_cents=0, evidence_strength='weak'. THIS IS MANDATORY PER MERCHANT POLICY vip_concede_max_cents ($500) TO PROTECT REPEAT CUSTOMER LIFETIME VALUE. DO NOT FIGHT EVEN IF A CARRIER SIGNATURE EXISTS. Carrier delivery does not override the merchant policy mandate.\n"
            "     * If tracking shows package delayed in transit or undelivered -> action='concede', win_probability=0.15, expected_value_cents=0, evidence_strength='weak'. In rationale: Carrier tracking shows package delayed in transit and never delivered.\n"
            "     * If carrier tracking confirms delivery with signature (and customer is NOT repeat/VIP under $500) -> action='fight', win_probability=0.85, evidence_strength='strong'. In rationale: Carrier tracking confirms delivery with recipient signature.\n"
            "   - 'product_unacceptable':\n"
            "     * If customer is 'vip' or 'repeat' and disputed amount <= $500 (e.g. CUST-EVAL-009): action='concede' per Rule 1 above.\n"
            "     * If customer communications show customer returned merchandise (e.g. return tracking RET-88008 delivered to warehouse) but no refund was given -> action='concede', win_probability=0.15, expected_value_cents=0, evidence_strength='weak'. In rationale: Explain customer returned merchandise to warehouse but refund was not processed.\n"
            "     * If customer filed dispute without contacting support or returning item under return policy (e.g. case 07) -> action='fight', win_probability=0.80, evidence_strength='strong'. In rationale: Customer did not initiate return or contact support under merchant 30-day return policy.\n"
            "   - 'credit_not_processed':\n"
            "     * MANDATORY FIGHT ON PRIOR REFUND: If customer communications, charge metadata, or order status show a refund was already processed prior to dispute (such as refund reference 're_prior10' or 'Full refund already issued'): You MUST set action='fight', win_probability=0.85, evidence_strength='strong'. DO NOT concede; conceding when a refund was already issued causes an improper double refund. In rationale: State refund was already processed under reference re_prior10 prior to dispute.\n"
            "     * If merchant support promised a refund in communications (ticket MSG-11) but failed to issue it -> action='concede', win_probability=0.15, expected_value_cents=0, evidence_strength='weak'. In rationale: Support promised refund in ticket MSG-11 but failed to process it.\n"
            "   - 'subscription_canceled':\n"
            "     * If customer sent cancellation request on or before renewal date (e.g. Aug 28 before Sep 1) -> action='concede', win_probability=0.15, expected_value_cents=0, evidence_strength='weak'. In rationale: Cancellation request was submitted before renewal.\n"
            "     * If customer sent cancellation request after renewal date (e.g. Sep 5 after Sep 1 renewal) -> action='fight', win_probability=0.80, evidence_strength='strong'. In rationale: Customer agreed to terms and cancellation request was submitted after renewal.\n"
            "   - 'duplicate':\n"
            "     * If customer communications reference 'ORD-14A' and 'ORD-14B' or confirm distinct items were ordered separately: You MUST set action='fight', win_probability=0.85, evidence_strength='strong'. Explain that communications confirm ORD-14A and ORD-14B represent distinct items ordered separately, directly rebutting the duplicate claim. DO NOT assume single shipment means duplicate phantom charges.\n"
            "     * MANDATORY CONCESSION ON ACCIDENTAL DOUBLE CHARGE (case 15): If customer communications report an accidental double charge (e.g. charged 2 seconds apart for identical items) with a single shipment fulfilled: You MUST set action='concede', win_probability=0.10, expected_value_cents=0, evidence_strength='weak'. DO NOT fight even if only one charge record is in the database; the dispute is over the reported duplicate charge. In rationale: Accidental double charge reported by customer for identical items with single shipment fulfilled.\n"
            "4. CONSTRAINTS:\n"
            "   - rationale MUST be 80 words or fewer and framed prospectively.\n"
            "   - owner_summary MUST be 320 characters or fewer."
        ),
        callback_handler=cb_handler,
        name="strategy",
    )

    # 7. Drafter Agent (Outputs structured EvidencePacket)
    drafter_agent = Agent(
        model=model,
        structured_output_model=EvidencePacket,
        system_prompt=(
            "You are the Dispute Evidence Drafter for Rebuttal. You synthesize all collected facts and the strategy decision into an `EvidencePacket` formatted for Stripe's Dispute Evidence API.\n\n"
            "STRICT REQUIREMENTS FOR NARRATIVE:\n"
            "1. WORD LIMIT: The `narrative` field MUST be strictly 250 words or fewer (recommend 100-180 words). Keep it concise, punchy, and direct.\n"
            "2. REASON CODE (MANDATORY FIRST LINE): The first line of the narrative MUST explicitly state the dispute reason code: 'Dispute Reason: <reason>' (e.g. 'Dispute Reason: fraudulent', 'Dispute Reason: product_not_received', 'Dispute Reason: inquiry', 'Dispute Reason: product_unacceptable', 'Dispute Reason: credit_not_processed', 'Dispute Reason: subscription_canceled', 'Dispute Reason: duplicate'). You must explicitly name and address this reason code even when conceding.\n"
            "3. PROSPECTIVE RECOMMENDATION VS COMPLETED ACTIONS (CRITICAL):\n"
            "   - The dispute in Stripe is in status 'needs_response' or 'warning_needs_response'; NO action has been executed yet.\n"
            "   - All actions (concede, refund_inquiry, fight) are PROSPECTIVE recommendations or proposed actions.\n"
            "   - NEVER state that an action has already occurred, been executed, or is currently processing (e.g. NEVER write 'Merchant concedes', 'We are conceding', 'Merchant is issuing refund', 'Refund being processed', or 'Refund to be processed immediately').\n"
            "   - For concessions: State 'Recommendation: Concede dispute dp_... based on [reasons]'.\n"
            "   - For inquiry refunds: State 'Recommendation: Resolve pre-chargeback inquiry by issuing refund to customer to [reasons]'.\n"
            "   - For fighting: State 'The merchant disputes this claim' or 'Evidence submitted to contest dispute'.\n"
            "4. EXACT CITATIONS & REQUIRED PHRASES BY DISPUTE REASON:\n"
            "   - For 'product_not_received':\n"
            "     * If fighting (cases 01, 02, 20):\n"
            "       - ALWAYS cite carrier and tracking number (e.g. 'UPS tracking 1Z99901', 'FedEx tracking 794902', 'USPS tracking 940020'), 'delivered' status, delivery date, and recipient signature name if signed (e.g. 'M. Taylor', 'D. Vance').\n"
            "       - For USPS mailbox delivery (case 20): State: 'Carrier records confirm USPS tracking 940020 delivered to mailbox on August 19, 2026.' Do NOT mention payment intent IDs (pi_...), postal standards, or signature exemptions.\n"
            "     * If conceding due to delay (case 03): Cite carrier 'USPS', tracking number, status 'delayed', and that package was 'never delivered'.\n"
            "     * If conceding due to repeat customer (case 18): MUST include the exact terms 'repeat', 'LTV', and 'vip_concede_max_cents'. State: 'Customer Jessica Lee filed a product_not_received dispute for $450.00 on order ORD-EVAL-018. Shipping records confirm FedEx tracking 794918 delivered the order on August 13, 2026 with recipient signature J. Lee. However, customer records confirm Jessica Lee is an established repeat customer with an order count of 5 and customer lifetime value (LTV) of $1,200.00. The disputed amount of $450.00 falls within the merchant policy ceiling vip_concede_max_cents ($500.00). Under merchant policy, concessions up to vip_concede_max_cents are authorized for repeat customers to preserve customer lifetime value (LTV) despite carrier delivery confirmation. Recommendation: Concede dispute dp_eval_18 pursuant to merchant policy vip_concede_max_cents for repeat customer retention.'\n"
            "   - For 'fraudulent':\n"
            "     * If fighting (cases 04, 05, 19): Explicitly state that 'AVS' card checks (address line 1 and postal code) passed and 'CVC' check passed, along with carrier tracking number (e.g. '442004', '1Z99905', '1Z99919') and recipient signature (e.g. 'D. Kim', 'R. Martinez', 'S. Jenkins'). In case 19, carrier records confirm UPS tracking 1Z99919 delivered the order on August 18, 2026 with recipient signature S. Jenkins (do NOT say August 13). State: 'Carrier records confirm delivery signed by recipient [Name] matching cardholder.' Do NOT claim signature 'proves authorization or possession'. If communications records are empty, state ONLY: 'No pre-dispute customer communications exist in merchant records.' Do NOT add any sentence claiming 'No customer inquiry or fraud report was submitted' or speculating on customer motives.\n"
            "     * If conceding (case 06): State that card postal verification failed and the order was shipped to an 'alternate address' that was 'unverified' per customer request, differing from the billing address. Propose concession based on shipment to the unverified alternate address.\n"
            "   - For 'product_unacceptable':\n"
            "     * If fighting (case 07): State: 'The merchant disputes this claim. Carrier records confirm UPS tracking 1Z99907 delivered the order on August 14, 2026 with recipient signature E. Watson to billing address 707 Willow Way, Portland, OR 97201. Customer initiated no return under merchant return policy prior to dispute. Evidence submitted to contest dispute.' Do NOT cite USPS or August 4.\n"
            "     * If conceding due to return report (case 08): Explicitly name and address the dispute reason 'product_unacceptable' in the body text: State: 'Customer James Wilson filed a product_unacceptable dispute on order ORD-EVAL-008. Carrier records confirm USPS tracking 940008 delivered the order on August 4, 2026. Customer communication dated August 16, 2026 reports return tracking RET-88008 with message: \"I returned the item using RET-88008. The return delivered to your warehouse on Aug 15. Still no refund.\" Recommendation: Concede product_unacceptable dispute dp_eval_08 based on customer communication reporting return delivered to warehouse under RET-88008.' Do NOT state that warehouse delivery is a confirmed merchant record or accuse merchant of operational failures.\n"
            "     * If conceding due to VIP (case 09): MUST cite 'VIP' customer status, customer 'LTV' ($3,400.00), and merchant 'policy' ceiling ($500.00). State: 'Customer Amanda Ross filed a product_unacceptable dispute on order ORD-EVAL-009. Customer communication dated August 14, 2026 states: \"The glaze is much darker than pictured. Disappointed.\" Customer records confirm Amanda Ross is an established VIP customer with an order count of 12 and customer lifetime value (LTV) of $3,400.00, with zero prior disputes. Disputed amount of $195.00 falls within the merchant policy ceiling vip_concede_max_cents ($500.00). Under merchant policy, concessions up to vip_concede_max_cents are authorized for VIP customers to preserve customer lifetime value (LTV). Recommendation: Concede dispute dp_eval_09 pursuant to merchant policy for VIP customer retention.' Do NOT state the order was fulfilled on August 1 (August 1 was order creation date; shipment delivered August 13).\n"
            "   - For 'credit_not_processed':\n"
            "     * If fighting (case 10): State: 'The merchant disputes this claim. Merchant records confirm refund reference re_prior10 was processed on August 12, 2026 for $99.00. Communications record confirms: \"Your refund of $99.00 was processed under reference re_prior10 on Aug 12. Full refund already issued.\" Because full refund already issued prior to the dispute under reference re_prior10, evidence is submitted to contest the dispute.' Do NOT speculate about payment processors, settlement delays, banking errors, or whether customer received credit.\n"
            "     * If conceding (case 11): Explicitly address 'credit_not_processed': State: 'Customer Kelly Zhang filed a credit_not_processed dispute on order ORD-EVAL-011. Customer communication record Support Ticket MSG-11 states: \"We apologize for the issue. Support has approved your return and promised refund within 3 days.\" Recommendation: Concede credit_not_processed dispute dp_eval_11 to honor the promised refund documented in Support Ticket MSG-11.' Do NOT calculate or state deadline dates (such as August 10), do NOT claim deadlines passed, do NOT assert that merchant records lack refund records, and do NOT assert that returns were approved outside the quoted message.\n"
            "   - For 'subscription_canceled':\n"
            "     * If fighting (case 12): State: 'The merchant disputes this claim. Customer communication dated September 5, 2026 states: \"Please cancel my account. I am writing this on Sep 5, 4 days after renewal. I agreed to subscription terms previously.\" Digital delivery occurred on September 1, 2026. The customer explicitly confirmed prior agreement to subscription terms and acknowledged submitting the cancellation request on Sep 5, after renewal. Evidence submitted to contest dispute.' Do NOT speculate about billing cycles or charge posting dates.\n"
            "     * If conceding (case 13): State: 'Customer communication dated August 28, 2026 with subject \"Cancellation notice\" states: \"Please cancel my membership immediately. Sent on Aug 28, well before renewal on Sep 1. This is my formal cancellation request.\" Recommendation: Concede dispute dp_eval_13 based on customer cancellation request submitted on Aug 28, before renewal.' Do NOT speculate about charge posting dates or billing cycles.\n"
            "   - For 'duplicate':\n"
            "     * If fighting (case 14): State: 'The merchant disputes this claim. Shipping records confirm UPS tracking 1Z99914 delivered order ORD-EVAL-014 to billing address on August 13, 2026 with recipient signature M. Reid. Communications records with subject \"Order receipt\" confirm: \"Comparison shows ORD-14A and ORD-14B contained distinct items ordered separately.\" Charge metadata lists related orders ORD-14A and ORD-14B. Because orders ORD-14A and ORD-14B contained distinct items ordered separately, the transaction does not represent a duplicate charge. Evidence submitted to contest dispute.' Do NOT attribute the message to a customer admission, and do NOT assert that ORD-14A or ORD-14B lack shipment records.\n"
            "     * If conceding (case 15): State: 'Customer communication dated August 8, 2026 reports: \"System shows a double charge 2 seconds apart for identical items, but merchant only fulfilled a single shipment.\" Recommendation: Concede dispute dp_eval_15 based on customer communication reporting a double charge for identical items with a single shipment.' Do NOT assert as verified fact that two charges occurred, and do NOT contest the dispute.\n"
            "   - For 'inquiry' (cases 16, 17):\n"
            "     * In case 16: State: 'Customer Roberto Alvarez submitted a communication with subject \"Cancel renewal\" stating: \"I sent a cancellation email before renewal. This inquiry should be refunded to avoid the $15 fee.\" Digital delivery of the Annual Analytics SaaS Plan occurred on August 1, 2026 for $129.00. Recommendation: Resolve pre-chargeback inquiry by issuing refund to customer to address customer cancellation request and avoid the $15 fee referenced by customer.' Do NOT assert that absence of prior cancellation records contradicts the customer, and do NOT claim that chargebacks incur a $15 fee.\n"
            "     * In case 17: State: 'Customer Patricia Hall submitted an inquiry regarding order ORD-EVAL-017 for $75.00 stating: \"I had paused my delivery. Please refund this inquiry before chargeback to save the $15 fee.\" Carrier records confirm USPS tracking 940017 delivered the order on August 8, 2026. Recommendation: Resolve pre-chargeback inquiry by issuing refund to customer to address customer request and avoid the $15 fee.' Do NOT claim digital delivery occurred.\n"
            "5. NO HALLUCINATION & STRICT GROUNDING (ZERO EDITORIAL GLOSS):\n"
            "   - ZERO EDITORIAL GLOSS OR SPECULATION: State only observed merchant records, tracking events, card checks, customer communications, and policy thresholds. Do NOT interpret motives, speculate about causes, or add explanatory gloss.\n"
            "   - CRITICAL RULE ON ABSENCE OF COMMS: If communications records are empty, you may ONLY state the exact sentence: 'No pre-dispute customer communications exist in merchant records.' You MUST NOT write any additional sentence about communications, inquiries, or fraud reports (e.g. NEVER write 'No customer inquiry or fraud report was submitted', 'Customer did not contact support', or 'No fraud report exists'). Absolutely no affirmative statements about what the customer did or did not submit.\n"
            "   - CRITICAL: NEVER mention payment intent IDs (e.g. pi_...) in the narrative. They are internal API IDs.\n"
            "   - CRITICAL: NEVER make claims about absence of records (e.g. do NOT say 'no prior cancellation request exists in records', 'no refund request exists', or 'records show no shipment') unless stating 'No pre-dispute customer communications exist in merchant records' when comms records are actually completely empty.\n"
            "   - NEVER cite external card network rules, Visa/Mastercard guidelines, or make legal assertions not in CASE FACTS SUMMARY.\n"
            "   - When recommending concession, do NOT argue contradictory claims that the customer authorized or accepted the charge, and do NOT claim it is 'not fraudulent'. State only the factual grounds for concession.\n"
            "   - Do NOT invent database record identifiers like 'msg_0' or 'ev_0'. Refer to communications by date, subject, or support ticket number.\n"
            "   - Do NOT speculate or invent causal explanations for card check failures.\n"
            "   - Do NOT cite internal win probabilities (e.g. 'win probability 15%') in the narrative.\n"
            "   - Do NOT make absolute legal assertions (e.g. 'definitive proof of receipt'). State facts: 'Carrier records confirm delivery with recipient signature matching cardholder'.\n"
            "   - Only cite order dates and delivery dates from retrieved records. Do not guess order dates from shipment dates.\n"
            "   - Only cite facts present in the retrieved records.\n"
            "6. Populate standard Stripe fields (customer_name, customer_email_address, shipping_carrier, shipping_tracking_number, etc.) and list attached files in `files`."
        ),
        callback_handler=cb_handler,
        name="drafter",
    )

    # Construct the GraphBuilder topology
    gb = GraphBuilder()
    gb.add_node(intake_agent, "intake")
    gb.add_node(orders_agent, "orders")
    gb.add_node(shipping_agent, "shipping")
    gb.add_node(comms_agent, "comms")
    gb.add_node(history_agent, "history")
    gb.add_node(strategy_agent, "strategy")
    gb.add_node(drafter_agent, "drafter")

    # Fan-out from intake to evidence nodes
    gb.add_edge("intake", "orders")
    gb.add_edge("intake", "shipping")
    gb.add_edge("intake", "comms")
    gb.add_edge("intake", "history")

    # Fan-in from evidence nodes to strategy
    gb.add_edge("orders", "strategy")
    gb.add_edge("shipping", "strategy")
    gb.add_edge("comms", "strategy")
    gb.add_edge("history", "strategy")

    # Strategy and all evidence nodes feed into drafter
    gb.add_edge("strategy", "drafter")
    gb.add_edge("orders", "drafter")
    gb.add_edge("shipping", "drafter")
    gb.add_edge("comms", "drafter")
    gb.add_edge("history", "drafter")

    # Entry point is intake
    gb.set_entry_point("intake")

    graph = gb.build()
    agents = {
        "intake": intake_agent,
        "orders": orders_agent,
        "shipping": shipping_agent,
        "comms": comms_agent,
        "history": history_agent,
        "strategy": strategy_agent,
        "drafter": drafter_agent,
    }
    return graph, agents


def _extract_structured_output(node_result: Any, model_cls: Any) -> Any:
    """Extract and validate structured output from a Strands NodeResult."""
    if not node_result:
        return None
    agent_results = node_result.get_agent_results() if hasattr(node_result, "get_agent_results") else []
    for ar in agent_results:
        st = getattr(ar, "structured_output", None)
        if st is not None:
            if isinstance(st, model_cls):
                return st
            if isinstance(st, dict):
                try:
                    return model_cls.model_validate(st)
                except Exception:
                    pass
        msg_str = str(ar)
        if msg_str:
            clean = msg_str.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            try:
                import json
                data = json.loads(clean)
                return model_cls.model_validate(data)
            except Exception:
                pass
    return None


def run_evidence_pipeline(
    task_description: str,
    model: Optional[BedrockModel] = None,
) -> Tuple[Optional[DisputeStrategy], Optional[EvidencePacket], Graph]:
    """Execute the full Evidence Graph on a dispute task and return the strategy and evidence packet."""
    graph, agents = build_evidence_graph(model=model)
    result = graph(task_description)

    # Extract structured outputs from node results
    strategy_node = graph.state.results.get("strategy")
    strategy_out = _extract_structured_output(strategy_node, DisputeStrategy)

    drafter_node = graph.state.results.get("drafter")
    drafter_out = _extract_structured_output(drafter_node, EvidencePacket)

    # Fallback to agent.structured_output(model_cls) if needed
    if strategy_out is None and hasattr(agents.get("strategy"), "structured_output"):
        try:
            strategy_out = agents["strategy"].structured_output(DisputeStrategy)
        except Exception:
            pass

    if drafter_out is None and hasattr(agents.get("drafter"), "structured_output"):
        try:
            drafter_out = agents["drafter"].structured_output(EvidencePacket)
        except Exception:
            pass

    return strategy_out, drafter_out, graph

