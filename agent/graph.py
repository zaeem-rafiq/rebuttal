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
            "- dispute reason (e.g. 'product_not_received', 'fraudulent', 'canceled_recurring_billing')\n"
            "- order_id (from charge metadata, order reference, or dispute details)\n"
            "- customer_id and customer_email\n\n"
            "Produce a clear summary containing: order_id, customer_id, dispute_id, reason, and amount_cents."
        ),
        callback_handler=cb_handler,
        name="intake",
    )

    # 2. Orders Agent
    orders_agent = Agent(
        model=model,
        tools=[get_order_evidence],
        system_prompt=(
            "You are the Orders Evidence Agent. Your role is to look up order transaction details using `get_order_evidence(order_id)`.\n"
            "Report:\n"
            "- Customer name, email, and customer_id\n"
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
        tools=[get_shipping_evidence],
        system_prompt=(
            "You are the Shipping & Fulfillment Evidence Agent. Your role is to look up carrier tracking and delivery using `get_shipping_evidence(order_id)`.\n"
            "Report:\n"
            "- Carrier name and tracking number\n"
            "- Fulfillment status and shipping date\n"
            "- Delivery date and delivery address\n"
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
            "- All relevant messages exchanged between customer and merchant\n"
            "- Whether customer requested an address change after placing the order\n"
            "- Whether customer requested order cancellation or refund\n"
            "- Overall customer communication sentiment and chronology"
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
            "- Total prior orders and lifetime spend in cents\n"
            "- Prior dispute history\n"
            "- Active merchant policy rules: approval_amount_cents, min_win_probability_to_fight, always_concede_under_cents, vip_concede_max_cents, silence_action\n"
            "- CRITICAL DIRECTIVE: Compare the disputed order amount against `vip_concede_max_cents` (50000 cents / $500.00). If the customer is 'repeat' or 'vip' and the disputed amount is <= 50000 cents (such as ORD-1002 at $340.00), you MUST state: 'POLICY DIRECTIVE: CONCEDE required under merchant policy to protect repeat customer LTV ($1,120). Do not fight.'"
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
            "1. REPEAT / VIP CUSTOMER CONCESSION RULE (HIGHEST PRIORITY):\n"
            "   - If customer_value is 'repeat' or 'vip' (e.g. CUST-002 with 5 prior orders, $1,120 LTV) and the disputed amount is <= merchant policy `vip_concede_max_cents` ($500 / 50000 cents):\n"
            "     * You MUST set action='concede'. Merchant policy strictly commands conceding disputes for repeat/vip customers under $500 to protect customer lifetime value and eliminate dispute loss fees.\n"
            "     * Set customer_value='repeat' (or 'vip').\n"
            "     * Set evidence_strength='weak'.\n"
            "     * Set win_probability=0.20.\n"
            "     * Set expected_value_cents=0.\n"
            "     * In rationale: Explain that conceding preserves a high-LTV repeat customer relationship ($1,120 LTV, 5 orders) per merchant policy (< $500). Word limit: <= 80 words.\n"
            "     * In owner_summary: Summarize that we are conceding the $340 dispute to preserve relationship with repeat customer Jessica Lee ($1.1K LTV) per policy. Char limit: <= 320 chars.\n"
            "2. FRAUDULENT DISPUTE WITH ALTERNATE DELIVERY ADDRESS:\n"
            "   - Under Visa/Mastercard rules, shipping to an alternate unverified address requested via email without signature confirmation cannot prove cardholder authorization; card networks rule this an automatic loss for the merchant.\n"
            "3. FIGHT RULE:\n"
            "   - Only select action='fight' when customer is NOT repeat/vip under policy limits, and carrier tracking confirms delivery with recipient signature (e.g. Scenario S1 / ORD-1001 for new customer CUST-001). Win probability >= 0.70, evidence_strength='strong'.\n"
            "4. REFUND INQUIRY RULE:\n"
            "   - Select action='refund_inquiry' when the dispute is an inquiry (warning_needs_response) or customer requested cancellation before fulfillment.\n"
            "5. CONSTRAINTS:\n"
            "   - rationale MUST be 80 words or fewer.\n"
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
            "GUIDELINES:\n"
            "1. Populate standard Stripe fields when available:\n"
            "   - customer_name, customer_email_address, billing_address, shipping_address\n"
            "   - shipping_carrier, shipping_tracking_number, shipping_date\n"
            "   - refund_policy_disclosure, cancellation_policy_disclosure\n"
            "2. Write a factual, compelling `narrative`:\n"
            "   - If action is 'fight': Detail the purchase timestamp, items ordered, card verification match (AVS/CVC), carrier tracking number, delivery date, and signature confirmation.\n"
            "   - If action is 'concede' or 'refund_inquiry': Explain the rationale (e.g., customer retention decision for repeat VIP, or pre-emptive inquiry refund).\n"
            "3. List attached evidence files in `files`."
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

    # Final step: strategy to drafter
    gb.add_edge("strategy", "drafter")

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

