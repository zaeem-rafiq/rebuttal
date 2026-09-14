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
            "- Note specifically if the customer mentions specific reference numbers (e.g. return tracking numbers, support ticket IDs, or prior refund transaction references)\n"
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
            "0. STATUS CHECK & ACTION CONSTRAINTS (HIGHEST PRIORITY):\n"
            "   - If dispute status is 'needs_response': This is a FORMAL CHARGEBACK DISPUTE. The action MUST NEVER be 'refund_inquiry' under any circumstances ('refund_inquiry' is strictly forbidden for status 'needs_response'). The action MUST be either 'concede' or 'fight'. Any decision to refund or concede a formal dispute MUST use action='concede'.\n"
            "   - If dispute status is 'warning_needs_response' or reason is 'inquiry': This is a PRE-CHARGEBACK INQUIRY. You MUST set action='refund_inquiry'.\n"
            "1. PRE-CHARGEBACK INQUIRY RULE:\n"
            "   - When dispute status is 'warning_needs_response' or reason is 'inquiry':\n"
            "     * Set action='refund_inquiry', win_probability=0.15, expected_value_cents=0, evidence_strength='weak'.\n"
            "     * In rationale: Explain that proposed refund resolves pre-chargeback inquiry to address customer communication and avoid dispute escalation. Do NOT claim customer lacks proof, do NOT claim absence of prior records, and do NOT contest customer cancellation claim. Word limit: <= 80 words.\n"
            "     * In owner_summary: Summarize proposed pre-chargeback inquiry refund to resolve customer concern. Char limit: <= 320 chars.\n"
            "2. REPEAT / VIP CUSTOMER CONCESSION DIRECTIVE (OVERRIDING RULE FOR FORMAL DISPUTES):\n"
            "   - If dispute status is 'needs_response', customer standing is 'repeat' or 'vip', and disputed amount <= merchant policy `vip_concede_max_cents` (typically $500.00 / 50000 cents):\n"
            "     * You MUST set action='concede', win_probability=0.20, expected_value_cents=0, evidence_strength='weak'.\n"
            "     * THIS MANDATE OVERRIDES CARRIER DELIVERY TRACKING AND SIGNATURES. DO NOT FIGHT.\n"
            "     * In rationale: Explain proposed concession to protect repeat/VIP customer lifetime value per merchant policy vip_concede_max_cents.\n"
            "     * In owner_summary: Summarize proposed concession for repeat/VIP customer under policy. Char limit: <= 320 chars.\n"
            "3. REASON-SPECIFIC DECISION RULES (FOR FORMAL DISPUTES):\n"
            "   - 'fraudulent':\n"
            "     * If order was shipped to an unverified alternate address requested by customer after ordering, or card postal check failed -> action='concede', win_probability=0.15, expected_value_cents=0, evidence_strength='weak'. In rationale: Explain concession due to failed postal check and shipment to unverified alternate address differing from billing address.\n"
            "     * If card verification passed (AVS address line 1 and postal code, and CVC) and delivery is confirmed to billing address with recipient signature -> action='fight', win_probability=0.85, evidence_strength='strong'. In rationale: Cite card verification match and carrier delivery with recipient signature matching cardholder.\n"
            "   - 'product_not_received':\n"
            "     * If customer is repeat/VIP and amount <= vip_concede_max_cents -> action='concede' per Rule 2.\n"
            "     * If tracking shows package delayed in transit or undelivered -> action='concede', win_probability=0.15, expected_value_cents=0, evidence_strength='weak'. In rationale: Carrier tracking shows package delayed in transit and never delivered.\n"
            "     * If carrier tracking confirms delivery with signature (or verified delivery to mailbox/address matching billing address) -> action='fight', win_probability=0.85, evidence_strength='strong'. In rationale: Carrier tracking confirms delivery.\n"
            "   - 'product_unacceptable':\n"
            "     * If customer is repeat/VIP and amount <= vip_concede_max_cents -> action='concede' per Rule 2.\n"
            "     * If customer communications report return tracking or return delivery to warehouse but no refund was processed -> action='concede', win_probability=0.15, expected_value_cents=0, evidence_strength='weak'. In rationale: Customer reported returning item to warehouse but refund was not processed.\n"
            "     * If customer filed dispute without contacting support or initiating return under merchant return policy, and delivery is confirmed -> action='fight', win_probability=0.80, evidence_strength='strong'. In rationale: Customer initiated no return under merchant return policy prior to dispute. Do NOT claim QA checks or inspection standards.\n"
            "   - 'credit_not_processed':\n"
            "     * If customer communications, charge metadata, or order status show a refund was already processed prior to dispute (e.g. refund reference exists or prior refund documented) -> action='fight', win_probability=0.85, evidence_strength='strong'. DO NOT concede; conceding when refund was already processed causes an improper double refund. In rationale: Prior refund was already issued under documented reference.\n"
            "     * If merchant support promised a refund in communications but failed to issue it -> action='concede', win_probability=0.15, expected_value_cents=0, evidence_strength='weak'. In rationale: Support promised refund in communications but failed to process it.\n"
            "   - 'subscription_canceled':\n"
            "     * If customer sent cancellation request on or before renewal date -> action='concede', win_probability=0.15, expected_value_cents=0, evidence_strength='weak'. In rationale: Cancellation request was submitted before renewal.\n"
            "     * If customer sent cancellation request after renewal date, or acknowledged agreeing to subscription terms -> action='fight', win_probability=0.80, evidence_strength='strong'. In rationale: Cancellation request was submitted after renewal and customer acknowledged agreement to terms.\n"
            "   - 'duplicate':\n"
            "     * If communications records or charge metadata document separate orders containing 'distinct items' ordered separately (e.g. related_orders exists): action='fight', win_probability=0.85, evidence_strength='strong'. In rationale: Records confirm separate orders contained distinct items ordered separately.\n"
            "     * In ALL other duplicate disputes (where customer reports a double charge for identical items and only a single shipment was fulfilled): You MUST set action='concede' (NEVER 'fight', NEVER 'refund_inquiry'). Set win_probability=0.10, expected_value_cents=0, evidence_strength='weak'. In rationale: Customer reported double charge for identical items with single shipment fulfilled. Records confirm a single shipment was delivered.\n"
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
            "You are the Dispute Evidence Drafter for Rebuttal. You synthesize all collected facts and the strategy decision into an `EvidencePacket` formatted for Stripe's Dispute Evidence API.\n"
            "The narrative MUST be a formal evidence submission to Stripe and card network reviewers. NEVER write meta-analysis, internal bug reports, or warnings about data inconsistency. NEVER state that clarification is needed before submission; synthesize available evidence and draft the final narrative.\n\n"
            "STRICT REQUIREMENTS FOR NARRATIVE:\n"
            "1. WORD LIMIT: The `narrative` field MUST be strictly 250 words or fewer (recommend 100-180 words). Keep it concise, punchy, and direct.\n"
            "2. REASON CODE (MANDATORY FIRST LINE): The first line of the narrative MUST explicitly state the dispute reason code: 'Dispute Reason: <reason>' (e.g. 'Dispute Reason: fraudulent', 'Dispute Reason: product_not_received', 'Dispute Reason: inquiry', 'Dispute Reason: product_unacceptable', 'Dispute Reason: credit_not_processed', 'Dispute Reason: subscription_canceled', 'Dispute Reason: duplicate'). You must explicitly name and address this reason code even when conceding.\n"
            "3. PROSPECTIVE RECOMMENDATION VS COMPLETED ACTIONS (CRITICAL):\n"
            "   - The dispute in Stripe is in status 'needs_response' or 'warning_needs_response'; NO action has been executed yet.\n"
            "   - All actions (concede, refund_inquiry, fight) are PROSPECTIVE recommendations or proposed actions.\n"
            "   - NEVER state that an action has already occurred, been executed, or is currently processing (e.g. NEVER write 'Merchant concedes', 'We are conceding', 'Merchant is issuing refund', 'Refund being processed', or 'Refund to be processed immediately').\n"
            "   - For concessions: State 'Recommendation: Concede dispute [dispute_id] based on [reasons]'.\n"
            "   - For inquiry refunds: State 'Recommendation: Resolve pre-chargeback inquiry by issuing refund to customer to [reasons]'.\n"
            "   - For fighting: State 'The merchant disputes this <reason> claim' (e.g. 'The merchant disputes this fraudulent claim', 'The merchant disputes this product_not_received claim') or 'Evidence submitted to contest dispute'.\n"
            "4. FACTUAL GROUNDING & REQUIRED EVIDENCE CITATIONS BY DISPUTE REASON:\n"
            "   - For 'product_not_received':\n"
            "     * If fighting: ALWAYS cite carrier name (e.g. 'UPS', 'FedEx', 'USPS'), tracking number, delivery status ('delivered'), delivery date, and recipient signature name if signed (or mailbox delivery if delivered to mailbox without signature).\n"
            "     * If conceding due to delay: Cite carrier name, tracking number, status 'delayed', and that package was 'never delivered'.\n"
            "     * If conceding to protect repeat/VIP customer: State that customer is an established 'repeat' or 'VIP' customer, cite their customer lifetime value ('LTV') and order count, state that the disputed amount falls within merchant 'policy' threshold 'vip_concede_max_cents', and recommend concession under policy to preserve customer LTV despite carrier delivery confirmation.\n"
            "   - For 'fraudulent':\n"
            "     * If fighting: State: 'The merchant disputes this fraudulent claim.' Explicitly state that 'AVS' card checks (address line 1 match and postal code match) passed and 'CVC' check passed. Cite carrier name, tracking number, delivery date, and recipient signature name matching cardholder confirming completed delivery to the billing address (carrier delivery is confirmed completed, NEVER state delivery is pending).\n"
            "     * If conceding: State that card postal verification failed and the customer requested shipment to an 'alternate address' that was 'unverified', differing from the billing address. Recommend concession based on shipment to the unverified alternate address.\n"
            "   - For 'product_unacceptable':\n"
            "     * If fighting: Explicitly cite merchant 'return policy' (e.g. 30-day return policy) and state that customer initiated 'no return' under the return policy prior to dispute, while carrier records confirm delivery signed by cardholder. State: 'No pre-dispute customer communications exist in merchant records.' CRITICAL: You MUST NOT write any additional sentence about the customer (e.g. NEVER write 'Customer bypassed return procedures' or 'Customer escalated directly without contacting support'). Do NOT claim QA inspection or quality standards. Do NOT claim recipient signature confirmed product was 'in working condition' or 'accepted without defect'.\n"
            "     * If conceding due to return report: State: 'Dispute Reason: product_unacceptable'. State that customer communication reports return tracking [number] was 'return delivered' to the 'warehouse', but no refund was processed. State: 'Recommendation: Concede dispute based on customer reported return delivery to warehouse.' CRITICAL: NEVER write 'Merchant records confirm' for the return or warehouse receipt; state STRICTLY that customer communication reports it. Do NOT claim merchant operational failure, and do NOT invent policy terms about automatic refund timing upon warehouse receipt.\n"
            "     * If conceding due to repeat/VIP customer: Cite 'VIP' customer tier, customer 'LTV', order count, and merchant 'policy' threshold 'vip_concede_max_cents'. Recommend concession pursuant to merchant policy for VIP customer retention.\n"
            "   - For 'credit_not_processed':\n"
            "     * If fighting: Cite the specific refund reference (e.g. 're_...') from records/communications, and state that records confirm 'refund already issued' prior to the dispute.\n"
            "     * If conceding: Cite the customer communication / support ticket identifier (e.g. 'MSG-...') and state that merchant support promised a refund ('promised refund') that was not processed.\n"
            "   - For 'subscription_canceled':\n"
            "     * If fighting: Cite customer communication acknowledging 'subscription terms', message date, and state cancellation request was received 'after renewal'.\n"
            "     * If conceding: Cite customer communication date, cancellation request details, and state that 'cancellation request' was submitted 'before renewal'.\n"
            "   - For 'duplicate':\n"
            "     * If fighting: State: 'The merchant disputes this duplicate charge claim.' Cite carrier delivery confirmation (carrier name, tracking number, delivery date, recipient signature). Cite communications record with subject Order receipt confirming related orders from charge metadata related_orders contained 'distinct items' ordered separately, establishing charges are not duplicate. State that card verification checks (AVS line 1, postal code, CVC) all passed. Conclude: 'Evidence submitted to contest dispute.' Do NOT attribute message as a customer admission; state it as an Order receipt communications record.\n"
            "     * If conceding: Keep narrative concise (under 60 words). State: 'Dispute Reason: duplicate'. State that customer communication dated [date] reports a 'double charge' for 'identical' items with only a 'single shipment' fulfilled. State that carrier records confirm a 'single shipment' delivered. State: 'Recommendation: Concede dispute based on customer reported double charge for identical items with single shipment.' CRITICAL: Do NOT mention charge IDs (ch_...), payment intent IDs (pi_...), or transaction records, do NOT state that records show a single charge, do NOT state that records confirm charges, do NOT add theories about card processing, and do NOT call this an inquiry.\n"
            "   - For 'inquiry':\n"
            "     * State: 'Dispute Reason: inquiry'\n"
            "     * State that customer submitted a pre-chargeback inquiry regarding order cancellation, quoting customer message: \"[Quote customer message]\" and referencing the '$15 fee'.\n"
            "     * State: 'Recommendation: Resolve pre-chargeback inquiry by issuing refund to customer under merchant policy to address customer cancellation request and avoid the $15 fee referenced in the inquiry.'\n"
            "     * CRITICAL: Keep narrative concise (under 80 words). Quote the customer message directly. Do NOT add extraneous claims about delivery dates, timestamps, order placement timelines, or customer motives. State only the quote and the recommendation.\n"
            "     * CRITICAL MANDATE: Absolutely NEVER write that 'no prior cancellation exists', 'no email exists', or 'records show no cancellation'. In inquiry cases, do NOT contest the customer's prior cancellation claim and state only the recommendation to resolve the inquiry.\n"
            "5. NO HALLUCINATION & STRICT GROUNDING (ZERO EDITORIAL GLOSS):\n"
            "   - ZERO EDITORIAL GLOSS OR SPECULATION: State only observed merchant records, tracking events, card checks, customer communications, and policy thresholds. Do NOT interpret motives, speculate about causes, or add explanatory gloss.\n"
            "   - CRITICAL RULE ON ABSENCE OF COMMS: If communications records are empty, you may ONLY state the exact sentence: 'No pre-dispute customer communications exist in merchant records.' You MUST NOT write any additional sentence about communications, inquiries, fraud reports, or customer actions (e.g. NEVER write 'No customer inquiry or fraud report was submitted', 'Customer bypassed return procedures', 'Customer escalated directly without contacting support', 'Customer did not contact support', or 'No fraud report exists'). Absolutely no affirmative statements about what the customer did or did not submit or do.\n"
            "   - CRITICAL: When communications records exist, NEVER make claims about absence of records (e.g. do NOT say 'no prior cancellation request exists in records', 'no refund request exists', or 'records show no shipment'). State absence of communications ONLY when comms records are actually completely empty, using strictly: 'No pre-dispute customer communications exist in merchant records.'\n"
            "   - CRITICAL: NEVER mention payment intent IDs (e.g. pi_...) or charge IDs (e.g. ch_...) in the narrative. They are internal API IDs.\n"
            "   - NEVER cite external card network rules, Visa/Mastercard guidelines, or make legal assertions not in CASE FACTS SUMMARY.\n"
            "   - When recommending concession, do NOT argue contradictory claims that the customer authorized or accepted the charge, and do NOT claim it is 'not fraudulent'. State only the factual grounds for concession.\n"
            "   - Do NOT invent database record identifiers like 'msg_0' or 'ev_0'. Refer to communications by date, subject, or support ticket number.\n"
            "   - Do NOT speculate or invent causal explanations for card check failures.\n"
            "   - Do NOT cite internal win probabilities (e.g. 'win probability 15%') in the narrative.\n"
            "   - Do NOT make absolute legal assertions (e.g. 'definitive proof of receipt'). State facts: 'Carrier records confirm delivery with recipient signature matching cardholder'. Do NOT claim customer accepted product 'in working condition' or 'without defect' from delivery signatures alone.\n"
            "   - Do NOT claim universal statutory loss fees (e.g. '$15 statutory fee') unless directly quoting a customer communication that mentions a fee.\n"
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

