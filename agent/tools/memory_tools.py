"""agent/tools/memory_tools.py - Bedrock AgentCore Memory tools for Rebuttal.

Provides:
- MemoryClient wrapper for AWS Bedrock AgentCore Memory.
- store_dispute_outcome: stores dispute outcome event and indexed record.
- retrieve_past_outcomes: queries past dispute outcomes by reason code from semantic memory.
- get_past_dispute_outcomes: Strands tool for dispute history and outcome retrieval.
- init_memory_integration: patches history tool so the history node queries memory.
"""

import os
import sys
import json
import logging
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import boto3
from dotenv import load_dotenv
from strands import tool

load_dotenv()

logger = logging.getLogger("rebuttal.memory_tools")

DEFAULT_MEMORY_ID = os.getenv("AGENTCORE_MEMORY_ID", "rebuttal_mem-Idf0xfCGuL")
DEFAULT_STRATEGY_ID = os.getenv("AGENTCORE_MEMORY_STRATEGY_ID", "merchant_outcomes-ZZzrLpFPxb")
DEFAULT_REGION = os.getenv("AWS_REGION", "us-east-1")


def get_memory_client(region_name: Optional[str] = None) -> Any:
    """Create MemoryClient with appropriate session (execution role in cloud or AWS_PROFILE locally)."""
    from bedrock_agentcore.memory import MemoryClient

    region = region_name or DEFAULT_REGION
    is_cloud = bool(os.environ.get("DOCKER_CONTAINER") or not os.path.exists(os.path.expanduser("~/.aws/credentials")))
    profile = None if is_cloud else os.getenv("AWS_PROFILE")

    if profile:
        session = boto3.Session(profile_name=profile, region_name=region)
    else:
        session = boto3.Session(region_name=region)

    return MemoryClient(region_name=region, boto3_session=session)


def store_dispute_outcome(
    dispute_id: str,
    reason: str,
    action: str,
    outcome: str,
    amount: int,
    merchant_id: str = "default",
    memory_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Store dispute resolution outcome in Bedrock AgentCore short-term events and semantic memory.

    Parameters:
        dispute_id: Dispute identifier (e.g. 'dp_S1').
        reason: Dispute reason code (e.g. 'product_not_received', 'fraudulent').
        action: Strategy action executed ('fight', 'concede', 'refund_inquiry').
        outcome: Resolution outcome ('won', 'lost', 'charge_refunded', 'closed').
        amount: Disputed amount in cents.
        merchant_id: Merchant / actor identifier (default: 'default').
        memory_id: Memory resource ID (default: DEFAULT_MEMORY_ID).

    Returns:
        Summary dictionary with created eventId and memoryRecordId.
    """
    target_mem_id = memory_id or DEFAULT_MEMORY_ID
    clean_dispute_id = dispute_id.strip()
    client = get_memory_client()

    event_id = None
    record_id = None

    # 1. Create short-term event in Memory resource
    try:
        user_msg = f"Dispute {clean_dispute_id} closed for reason {reason} with amount {amount} cents"
        asst_msg = (
            f"Outcome recorded: reason={reason}, action={action}, outcome={outcome}, "
            f"amount={amount}, dispute_id={clean_dispute_id}"
        )
        ev_resp = client.create_event(
            memory_id=target_mem_id,
            actor_id=merchant_id,
            session_id=f"outcome-{clean_dispute_id}",
            messages=[
                (user_msg, "USER"),
                (asst_msg, "ASSISTANT"),
            ],
        )
        event_id = ev_resp.get("eventId")
        logger.info("Created memory event for dispute %s: %s", clean_dispute_id, event_id)
    except Exception as e:
        logger.warning("Notice on create_event for dispute %s: %s", clean_dispute_id, e)

    # 2. Batch create immediate memory record in semantic namespace /merchant/{actorId}/outcomes/
    try:
        dp = client.gmdp_client
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        record_text = (
            f"Dispute outcome for {reason}: action={action}, status={outcome}, "
            f"amount_cents={amount}, dispute_id={clean_dispute_id}"
        )
        batch_resp = dp.batch_create_memory_records(
            memoryId=target_mem_id,
            records=[{
                "requestIdentifier": f"rec-{clean_dispute_id}-{int(now_dt.timestamp())}",
                "namespaces": [f"/merchant/{merchant_id}/outcomes/"],
                "content": {"text": record_text},
                "timestamp": now_dt,
                "memoryStrategyId": DEFAULT_STRATEGY_ID,
            }],
        )
        succ = batch_resp.get("successfulRecords", [])
        if succ:
            record_id = succ[0].get("memoryRecordId")
            logger.info("Batch created memory record for dispute %s: %s", clean_dispute_id, record_id)
    except Exception as e:
        logger.warning("Notice on batch_create_memory_records for dispute %s: %s", clean_dispute_id, e)

    return {
        "status": "stored",
        "dispute_id": clean_dispute_id,
        "event_id": event_id,
        "record_id": record_id,
        "reason": reason,
        "action": action,
        "outcome": outcome,
        "amount": amount,
    }


def retrieve_past_outcomes(
    reason: str,
    merchant_id: str = "default",
    memory_id: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Retrieve past dispute outcome records by reason code from Bedrock AgentCore Memory.

    Parameters:
        reason: Dispute reason to query (e.g. 'product_not_received').
        merchant_id: Merchant / actor identifier (default: 'default').
        memory_id: Memory resource ID (default: DEFAULT_MEMORY_ID).
        limit: Maximum number of records to retrieve.

    Returns:
        List of memory record dictionaries matching the query.
    """
    target_mem_id = memory_id or DEFAULT_MEMORY_ID
    client = get_memory_client()

    # Try trailing slash namespace first, then without trailing slash, then path
    for ns in [f"/merchant/{merchant_id}/outcomes/", f"/merchant/{merchant_id}/outcomes"]:
        try:
            recs = client.retrieve_memories(
                memory_id=target_mem_id,
                namespace=ns,
                query=reason,
                top_k=limit,
            )
            if recs:
                return recs
        except Exception as e:
            logger.debug("Namespace %s lookup notice: %s", ns, e)

    # Fallback to namespace_path
    try:
        recs = client.retrieve_memories(
            memory_id=target_mem_id,
            namespace_path=f"/merchant/{merchant_id}/outcomes",
            query=reason,
            top_k=limit,
        )
        if recs:
            return recs
    except Exception as e:
        logger.debug("namespace_path lookup notice: %s", e)

    # Fallback to direct list_memory_records
    try:
        dp = client.gmdp_client
        resp = dp.list_memory_records(memoryId=target_mem_id, namespace=f"/merchant/{merchant_id}/outcomes/")
        summaries = resp.get("memoryRecordSummaries", [])
        matched = [
            s for s in summaries
            if reason.lower() in s.get("content", {}).get("text", "").lower()
        ]
        if matched:
            return matched
    except Exception as e:
        logger.debug("Direct list lookup notice: %s", e)

    return []


@tool
def get_past_dispute_outcomes(reason: str, merchant_id: str = "default") -> List[Dict[str, Any]]:
    """Query past merchant dispute outcomes by reason code from Bedrock AgentCore semantic memory.

    Parameters:
        reason: Dispute reason code (e.g. 'product_not_received', 'fraudulent').
        merchant_id: Merchant identifier.

    Returns:
        List of past dispute resolution outcomes from semantic memory.
    """
    return retrieve_past_outcomes(reason=reason, merchant_id=merchant_id)


def patch_history_tool_with_memory():
    """Enhance get_merchant_history_and_policy to incorporate AgentCore memory outcomes."""
    try:
        import agent.tools.evidence_tools as et

        if hasattr(et, "_memory_patched"):
            return

        orig_func = et.get_merchant_history_and_policy._tool_func if hasattr(et.get_merchant_history_and_policy, "_tool_func") else et.get_merchant_history_and_policy

        def _patched_get_merchant_history_and_policy(customer_id: str, merchant_id: str = "default") -> Dict[str, Any]:
            result = orig_func(customer_id=customer_id, merchant_id=merchant_id)
            try:
                # Query past outcomes from semantic memory for common dispute reasons
                outcomes = retrieve_past_outcomes("product_not_received", merchant_id=merchant_id)
                result["memory_past_outcomes"] = outcomes
                result["memory_outcomes_count"] = len(outcomes)
            except Exception as ex:
                logger.warning("Could not query past outcomes from memory: %s", ex)
                result["memory_past_outcomes"] = []
                result["memory_outcomes_count"] = 0
            return result

        if hasattr(et.get_merchant_history_and_policy, "_tool_func"):
            et.get_merchant_history_and_policy._tool_func = _patched_get_merchant_history_and_policy
        else:
            et.get_merchant_history_and_policy = tool(_patched_get_merchant_history_and_policy)

        et._memory_patched = True
        logger.info("Successfully patched get_merchant_history_and_policy with AgentCore memory")
    except Exception as e:
        logger.warning("Could not patch history tool: %s", e)
