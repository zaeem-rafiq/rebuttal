"""Record a real local Strands / Stripe-test run without modifying shared data.

The developer terminal supplies approval. Notification transports and cloud case
replication are disabled; their delivery is not part of this recording.
"""
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(os.environ.get("RECORD_OUTPUT_DIR", str(Path(__file__).resolve().parent)))
OUT.mkdir(parents=True, exist_ok=True)
REV = os.environ.get("RECORD_REV")
started = time.monotonic()
events = []


def emit(stage, data):
    events.append({"seconds": round(time.monotonic() - started, 3), "stage": stage, "data": data})
    (OUT / "workflow.json").write_text(json.dumps(events, indent=2, default=str))
    print("\n" + stage.upper(), flush=True)
    print(json.dumps(data, indent=2, default=str), flush=True)


def main():
    from dotenv import dotenv_values
    if (OUT / "workflow.json").exists():
        raise RuntimeError("Choose a fresh RECORD_OUTPUT_DIR; prior recordings are preserved")
    if not REV:
        raise RuntimeError("Set RECORD_REV to the verified recording revision")

    config = dotenv_values(ROOT / ".env")
    # Consume only the credential needed for the authorized test operation.
    key = os.environ.get("STRIPE_SECRET_KEY") or config.get("STRIPE_SECRET_KEY", "")
    if not key.startswith("sk_test_"):
        raise RuntimeError("A Stripe test key is required; no operation attempted")
    os.environ["STRIPE_SECRET_KEY"] = key
    os.environ.update({"PYTHON_DOTENV_DISABLED": "1", "USE_GATEWAY_MCP": "false",
                       "USE_AGENTCORE_MEMORY_SESSION": "false", "DEMO_MODE": "false",
                       "AWS_PROFILE": "zaeem-khan", "AWS_REGION": "us-east-1",
                       "BEDROCK_MODEL_ID": "us.anthropic.claude-haiku-4-5-20251001-v1:0"})
    for name in ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "TWILIO_ACCOUNT_SID",
                 "TWILIO_AUTH_TOKEN", "TWILIO_FROM", "OWNER_PHONE", "SUPABASE_URL",
                 "SUPABASE_SERVICE_KEY"]:
        os.environ.pop(name, None)
    scratch = Path(tempfile.mkdtemp(prefix="rebuttal-e54a489-recording-"))
    archive = subprocess.check_output(["git", "archive", REV], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(scratch, filter="data")
    db = scratch / "data/local_supabase.db"
    shutil.copyfile(ROOT / "data/local_supabase.db", db)
    sys.path.insert(0, str(scratch))
    os.chdir(scratch)

    import scripts.run_local as runner
    import agent.tools.case_tools as cases
    from agent.executor import build_executor_agent
    from agent.hooks import set_agent_state
    from agent.tools.stripe_tools import get_dispute, get_charge_context, serialize_stripe_object
    from agent.tools.evidence_tools import get_order_evidence, get_shipping_evidence, get_customer_comms, get_merchant_history_and_policy

    assert serialize_stripe_object({"client_secret": "sentinel", "charge": {"receipt_url": "sentinel"}}) == {"charge": {}}, "Recording revision must exclude client credentials and receipt access URLs"

    # These existing modules use different default DB roots on macOS. Point
    # the recorder's audit writer at the same isolated database as the graph.
    cases.LOCAL_DB_PATH = db
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE disputes SET metadata='{}' WHERE id='dp_S2'")
    emit("environment", {"revision": REV, "merchant_records": "synthetic",
         "model": os.environ["BEDROCK_MODEL_ID"], "stripe": "test mode",
         "approval_interface": "developer CLI", "notification_delivery": "disabled",
         "session_storage": "local FileSessionManager", "database": "isolated copy"})
    stripe_id = os.environ.get("RECORD_STRIPE_ID")
    if not stripe_id:
        stripe_id, _ = runner.ensure_active_stripe_dispute("S2")
    initial = get_dispute(stripe_id)
    def object_id(value):
        return value["id"] if isinstance(value, dict) else value
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE disputes SET metadata=?, charge_id=?, payment_intent_id=?, status=? WHERE id='dp_S2'",
                     (json.dumps({"stripe_dispute_id": stripe_id, "scenario": "S2", "order_id": "ORD-1002"}),
                      object_id(initial["charge"]), object_id(initial["payment_intent"]), initial["status"]))
        conn.execute("UPDATE orders SET charge_id=?, payment_intent_id=? WHERE id='ORD-1002'",
                     (object_id(initial["charge"]), object_id(initial["payment_intent"])))
    assert initial["livemode"] is False and initial["status"] == "needs_response"
    emit("dispute arrived", {k: initial[k] for k in ["id", "amount", "currency", "reason", "status", "livemode"]})
    emit("retrieved facts", {"dispute": initial, "order": get_order_evidence("ORD-1002"),
         "shipment": get_shipping_evidence("ORD-1002"), "communications": get_customer_comms("CUST-002", "ORD-1002"),
         "history_and_policy": get_merchant_history_and_policy("CUST-002"),
         "charge": get_charge_context(object_id(initial["payment_intent"]))})
    original_pipeline = runner.run_evidence_pipeline
    def observed_pipeline(*args, **kwargs):
        strategy, packet, graph = original_pipeline(*args, **kwargs)
        counts = {name: result.execution_count for name, result in graph.state.results.items()}
        emit("graph execution", counts)
        emit("graph usage", dict(graph.state.accumulated_usage))
        emit("model-visible records", {
            name: node.executor.messages for name, node in graph.nodes.items()
            if hasattr(node.executor, "messages")
        })
        assert len(counts) == 7 and all(count == 1 for count in counts.values())
        return strategy, packet, graph
    runner.run_evidence_pipeline = observed_pipeline
    result = runner.run_local("S2", scenario="S2", dry_run=True)
    strategy, packet = result["strategy"], result["evidence_packet"]
    assert strategy is not None and packet is not None
    emit("strategy", strategy.model_dump())
    emit("evidence", packet.model_dump())
    executor = build_executor_agent(session_id="recording-S2", storage_dir=str(scratch / ".sessions"))
    executor.callback_handler = lambda **kwargs: None
    set_agent_state(executor, "dispute_id", "dp_S2")
    set_agent_state(executor, "amount_cents", initial["amount"])
    set_agent_state(executor, "strategy", strategy.model_dump())
    response = executor(
        "Execute the strategy using the provided EvidencePacket and no invented evidence. "
        "The ApprovalGate controls authorization. Use dispute dp_S2. DEMO_MODE=false.\n"
        + json.dumps({"strategy": strategy.model_dump(), "evidence_packet": packet.model_dump()})
    )
    before = get_dispute(stripe_id)
    emit("approval pause", {"stop_reason": response.stop_reason,
         "interrupt_names": [i.name for i in response.interrupts or []],
         "stripe_status": before["status"], "gated_action_calls": runner.MUTATING_CALLS_COUNT,
         "notification_delivery": "disabled; CLI approval only"})
    assert response.stop_reason == "interrupt" and response.interrupts
    assert before["status"] == "needs_response" and runner.MUTATING_CALLS_COUNT == 0
    answer = input("OWNER REVIEW (Stripe test mode): 1 fight, 2 concede, 3 hold > ").strip()
    if answer not in {"1", "2", "3"}:
        raise ValueError("Invalid owner choice; execution remains paused")
    emit("CLI approval", {"answer": answer, "action": {"1": "fight", "2": "concede", "3": "hold"}[answer]})
    resumed = executor([{"interruptResponse": {"interruptId": response.interrupts[0].id, "response": answer}}])
    final = get_dispute(stripe_id)
    emit("Stripe readback", {"id": final["id"], "status": final["status"],
         "livemode": final["livemode"], "executor_stop_reason": resumed.stop_reason,
         "gated_action_calls": runner.MUTATING_CALLS_COUNT})
    if answer == "2":
        assert final["status"] == "lost" and runner.MUTATING_CALLS_COUNT == 1
    elif answer == "1":
        assert final["evidence_details"]["submission_count"] > 0
    else:
        assert runner.MUTATING_CALLS_COUNT == 0 and final["status"] == "needs_response"
    emit("completed", {"assertions": "passed", "scope": "local Strands and Stripe test API; no production recovery or phone delivery claimed"})


if __name__ == "__main__":
    main()
