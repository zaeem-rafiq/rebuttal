"""Synthetic intake tools retain production metadata and reject wrong IDs."""
import json
from unittest.mock import MagicMock

import pytest

import evals.run as runner
from agent.tools.stripe_tools import get_charge_context, get_dispute


def test_eval_intake_tools_require_the_matching_dispute_charge_or_payment_intent(monkeypatch):
    case_path = runner.CASES_DIR / "case_01.json"
    case = json.loads(case_path.read_text())
    checked = []

    def pipeline(task_description):
        dispute_tool = runner.agent.graph.get_dispute
        charge_tool = runner.agent.graph.get_charge_context
        assert dispute_tool.tool_spec == get_dispute.tool_spec
        assert charge_tool.tool_spec == get_charge_context.tool_spec
        dispute = dispute_tool(f" {case['dispute_id']} ")
        assert dispute["id"] == case["dispute_id"]
        for valid_id in (dispute["charge"], dispute["payment_intent"]):
            charge = charge_tool(f" {valid_id} ")
            assert charge["amount"] == case["amount_cents"]
            assert charge["metadata"]["order_id"] == case["order_id"]
        for invalid_id in (case["order_id"], "dp_other_case", dispute["charge"], ""):
            with pytest.raises(ValueError, match="Unknown dispute ID"):
                dispute_tool(invalid_id)
        for invalid_id in (case["order_id"], case["dispute_id"], "ch_other_case", "pi_other_case", ""):
            with pytest.raises(ValueError, match="Unknown charge or payment intent ID"):
                charge_tool(invalid_id)
        checked.append(True)
        return None, None, None

    monkeypatch.setattr(runner.agent.graph, "run_evidence_pipeline", pipeline)
    monkeypatch.setattr(runner, "judge_narrative", lambda **kwargs: {"overall_pass": False})
    judge = MagicMock()

    result = runner.run_single_eval_case(case_path, judge)

    assert checked == [True]
    assert result["pipeline_error"] is None
    assert runner.agent.graph.get_dispute is get_dispute
    assert runner.agent.graph.get_charge_context is get_charge_context
    judge.converse.assert_not_called()
