"""Both model entry points support InvokeModel-only verification permissions."""
from unittest.mock import MagicMock

import pytest


@pytest.mark.parametrize("setting,expected", [(None, True), ("true", True), ("false", False)])
@pytest.mark.parametrize("runtime", [False, True])
def test_bedrock_transport_configuration(monkeypatch, setting, expected, runtime):
    import boto3
    import strands.models.bedrock
    import agent.graph
    from agent.app import get_runtime_bedrock_model

    if setting is None:
        monkeypatch.delenv("BEDROCK_STREAMING", raising=False)
    else:
        monkeypatch.setenv("BEDROCK_STREAMING", setting)
    monkeypatch.setenv("BEDROCK_MODEL_ID", "configured-model")
    session = MagicMock()
    monkeypatch.setattr(boto3, "Session", lambda **kwargs: session)
    constructor = MagicMock()
    monkeypatch.setattr(agent.graph, "BedrockModel", constructor)
    monkeypatch.setattr(strands.models.bedrock, "BedrockModel", constructor)

    (get_runtime_bedrock_model if runtime else agent.graph.get_bedrock_model)()

    assert constructor.call_args.kwargs == {
        "model_id": "configured-model", "boto_session": session,
        "temperature": 0.0, "streaming": expected,
    }
