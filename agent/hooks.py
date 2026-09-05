"""agent/hooks.py

Hook providers for Rebuttal:
    - ApprovalGate: Human-in-the-loop gate triggering SMS interrupts on high-stakes tool calls.
    - AuditHook: Records all tool invocations and results to audit_log.
"""

import os
import sys
import time
import json
import uuid
import yaml
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from strands.hooks import (
    HookProvider,
    HookRegistry,
    BeforeToolCallEvent,
    AfterToolCallEvent,
)

from agent.tools.case_tools import record_case

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_DB_PATH = REPO_ROOT / "data" / "local_supabase.db"
POLICY_PATH = REPO_ROOT / "data" / "merchant_policy.yaml"

TARGET_GATED_TOOLS = {"submit_evidence", "concede_dispute", "refund_inquiry"}


def load_merchant_policy() -> Dict[str, Any]:
    """Load policy configuration from data/merchant_policy.yaml with defaults."""
    if POLICY_PATH.exists():
        try:
            with open(POLICY_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass

    # Default policy thresholds
    return {
        "approval_amount_cents": 20000,
        "min_win_probability_to_fight": 0.50,
        "always_concede_under_cents": 1500,
        "vip_concede_max_cents": 50000,
        "silence_action": "fight",
    }


def send_owner_sms(body: str) -> str:
    """Send an SMS to OWNER_PHONE via Twilio.

    Returns the message SID. In environments without Twilio credentials, returns a mock SID.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_FROM")
    owner_phone = os.getenv("OWNER_PHONE")

    if account_sid and auth_token and from_phone and owner_phone:
        try:
            from twilio.rest import Client
            client = Client(account_sid, auth_token)
            msg = client.messages.create(body=body, from_=from_phone, to=owner_phone)
            sid = msg.sid

            # Operating rule: treat Twilio message status "delivered" as receipt
            # Poll briefly (up to 5 seconds) to check status without blocking turns
            for _ in range(3):
                if msg.status in ["delivered", "sent"]:
                    break
                time.sleep(1.0)
                try:
                    msg = client.messages(sid).fetch()
                except Exception:
                    break

            return sid
        except Exception as e:
            print(f"  [Twilio Warning] SMS dispatch error: {e}", file=sys.stderr)

    # Fallback / mock SID
    return f"SM_{uuid.uuid4().hex[:30]}"


def get_agent_state(agent: Any, key: str, default: Any = None) -> Any:
    """Safely get a value from agent.state supporting dict and JSONSerializableDict."""
    if not agent or not hasattr(agent, "state"):
        return default
    try:
        if hasattr(agent.state, "get"):
            val = agent.state.get(key)
            return val if val is not None else default
        elif isinstance(agent.state, dict):
            return agent.state.get(key, default)
    except Exception:
        pass
    return default


def set_agent_state(agent: Any, key: str, value: Any) -> None:
    """Safely set a value in agent.state supporting dict and JSONSerializableDict."""
    if not agent or not hasattr(agent, "state"):
        return
    try:
        if hasattr(agent.state, "set"):
            agent.state.set(key, value)
        elif isinstance(agent.state, dict):
            agent.state[key] = value
    except Exception:
        pass


class ApprovalGate(HookProvider):
    """Human-in-the-loop approval gate using SMS interrupts.

    Intercepts submit_evidence, concede_dispute, and refund_inquiry.
    Applies merchant policy thresholds:
        - amount_cents >= policy.approval_amount_cents (20000)
        - 0.35 <= win_probability <= 0.65
        - action != 'fight'
    """

    def __init__(self, policy: Optional[Dict[str, Any]] = None):
        self.policy = policy or load_merchant_policy()

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeToolCallEvent, self.before_tool_call)

    def before_tool_call(self, event: BeforeToolCallEvent) -> None:
        tool_name = event.tool_use.get("name")
        if tool_name not in TARGET_GATED_TOOLS:
            return

        agent = getattr(event, "agent", None)
        inv_state = getattr(event, "invocation_state", {}) or {}

        # Check cached approval
        cached_approval = get_agent_state(agent, "approval")
        action_tool_map = {
            "fight": "submit_evidence",
            "concede": "concede_dispute",
            "refund_inquiry": "refund_inquiry",
        }
        reverse_tool_map = {v: k for k, v in action_tool_map.items()}

        if cached_approval:
            expected_tool = action_tool_map.get(cached_approval)
            if tool_name == expected_tool:
                # Allowed through cached approval
                return
            else:
                event.cancel_tool = f"Owner chose {cached_approval}; call that tool instead"
                return

        # Extract strategy and dispute parameters
        strategy = inv_state.get("strategy") or get_agent_state(agent, "strategy")
        dispute_id = inv_state.get("dispute_id") or get_agent_state(agent, "dispute_id") or "dp_S1"
        amount_cents = inv_state.get("amount_cents") or get_agent_state(agent, "amount_cents", 0)

        if isinstance(strategy, dict):
            win_probability = strategy.get("win_probability", 0.5)
            action = strategy.get("action", reverse_tool_map.get(tool_name, "fight"))
            owner_summary = strategy.get("owner_summary", f"Dispute {dispute_id} needs decision.")
            rationale = strategy.get("rationale", "")
            expected_val = strategy.get("expected_value_cents", 0)
            cust_val = strategy.get("customer_value", "new")
            ev_strength = strategy.get("evidence_strength", "mixed")
        elif strategy:
            win_probability = getattr(strategy, "win_probability", 0.5)
            action = getattr(strategy, "action", reverse_tool_map.get(tool_name, "fight"))
            owner_summary = getattr(strategy, "owner_summary", f"Dispute {dispute_id} needs decision.")
            rationale = getattr(strategy, "rationale", "")
            expected_val = getattr(strategy, "expected_value_cents", 0)
            cust_val = getattr(strategy, "customer_value", "new")
            ev_strength = getattr(strategy, "evidence_strength", "mixed")
        else:
            win_probability = 0.5
            action = reverse_tool_map.get(tool_name, "fight")
            owner_summary = f"Dispute {dispute_id} needs decision."
            rationale = ""
            expected_val = 0
            cust_val = "new"
            ev_strength = "mixed"

        # Check approval condition
        approval_threshold = self.policy.get("approval_amount_cents", 20000)
        is_amount_high = amount_cents >= approval_threshold
        is_prob_uncertain = 0.35 <= win_probability <= 0.65
        is_not_fight = action != "fight"

        requires_approval = is_amount_high or is_prob_uncertain or is_not_fight

        if not requires_approval:
            set_agent_state(agent, "gate_status", "skipped")
            return

        set_agent_state(agent, "gate_status", "required")

        # Record pending decision in database
        decision_id = f"dec_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if LOCAL_DB_PATH.exists():
            try:
                conn = sqlite3.connect(LOCAL_DB_PATH)
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO decisions 
                       (id, dispute_id, action, win_probability, expected_value_cents, evidence_strength, customer_value, rationale, owner_summary, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
                    (
                        decision_id,
                        dispute_id,
                        action,
                        win_probability,
                        expected_val,
                        ev_strength,
                        cust_val,
                        rationale,
                        owner_summary,
                        now_iso,
                    ),
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"  [Gate Notice] Error inserting decision: {e}", file=sys.stderr)

        # Dispatch SMS via Twilio
        sms_body = f"{owner_summary}\n\nReply:\n1 Fight\n2 Concede\n3 Hold"
        sms_sid = send_owner_sms(sms_body)
        set_agent_state(agent, "sms_sid", sms_sid)
        set_agent_state(agent, "decision_id", decision_id)

        # Trigger interrupt
        interrupt_reason = {
            "dispute_id": dispute_id,
            "decision_id": decision_id,
            "proposed_tool": tool_name,
            "proposed_action": action,
            "amount_cents": amount_cents,
            "sms_sid": sms_sid,
        }

        # Strands interrupt call
        answer = event.interrupt("owner-approval", reason=interrupt_reason)

        # Resumed execution from interrupt
        ans_clean = str(answer).strip()
        answer_map = {"1": "fight", "2": "concede", "3": "hold"}
        chosen_action = answer_map.get(ans_clean, ans_clean)
        answered_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if chosen_action == "hold":
            event.cancel_tool = "Owner chose hold; dispute held pending owner review"
            self._update_decision_status(decision_id, status="held", answered_at=answered_iso)
            record_case(
                dispute_id=dispute_id,
                action="hold_decision",
                actor="owner",
                details={"decision_id": decision_id, "answer": ans_clean},
            )
            return

        expected_tool = action_tool_map.get(chosen_action)
        if tool_name == expected_tool:
            # Action approved by owner
            set_agent_state(agent, "approval", chosen_action)
            self._update_decision_status(decision_id, status="approved", answered_at=answered_iso)
            record_case(
                dispute_id=dispute_id,
                action="approve_decision",
                actor="owner",
                details={"decision_id": decision_id, "chosen_action": chosen_action, "answer": ans_clean},
            )
        else:
            # Action overridden by owner
            event.cancel_tool = f"Owner chose {chosen_action}; call that tool instead"
            self._update_decision_status(decision_id, status="overridden", action=chosen_action, answered_at=answered_iso)
            record_case(
                dispute_id=dispute_id,
                action="override_decision",
                actor="owner",
                details={"decision_id": decision_id, "chosen_action": chosen_action, "answer": ans_clean},
            )

    def _update_decision_status(
        self,
        decision_id: str,
        status: str,
        action: Optional[str] = None,
        answered_at: Optional[str] = None,
    ):
        """Update decision record status and answered timestamp in local database."""
        if not LOCAL_DB_PATH.exists():
            return
        try:
            conn = sqlite3.connect(LOCAL_DB_PATH)
            cur = conn.cursor()
            if action:
                cur.execute(
                    "UPDATE decisions SET status = ?, action = ?, answered_at = COALESCE(?, answered_at) WHERE id = ?",
                    (status, action, answered_at, decision_id),
                )
            else:
                cur.execute(
                    "UPDATE decisions SET status = ?, answered_at = COALESCE(?, answered_at) WHERE id = ?",
                    (status, answered_at, decision_id),
                )
            conn.commit()
            conn.close()
        except Exception:
            pass


class AuditHook(HookProvider):
    """AuditHook appends every tool execution to audit_log."""

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(AfterToolCallEvent, self.after_tool_call)

    def after_tool_call(self, event: AfterToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "unknown")
        inv_state = getattr(event, "invocation_state", {}) or {}
        agent = getattr(event, "agent", None)
        dispute_id = inv_state.get("dispute_id") or getattr(agent.state, "dispute_id", "dp_general") if agent else "dp_general"

        details = {
            "tool": tool_name,
            "duration": event.duration,
            "has_exception": event.exception is not None,
            "cancelled": bool(event.cancel_message),
        }
        if event.cancel_message:
            details["cancel_message"] = event.cancel_message

        try:
            record_case(
                dispute_id=dispute_id,
                action=f"tool_executed:{tool_name}",
                actor="executor",
                details=details,
            )
        except Exception:
            pass
