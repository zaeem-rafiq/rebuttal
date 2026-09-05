import json
import base64
import time
import hmac
import hashlib
from unittest.mock import MagicMock, patch
import pytest

from infra.lambdas.stripe_webhook.app import (
    verify_stripe_signature,
    lambda_handler as stripe_handler,
)
from infra.lambdas.twilio_webhook.app import (
    validate_twilio_signature,
    parse_reply_answer,
    lambda_handler as twilio_handler,
)
from infra.lambdas.sweep.app import (
    lambda_handler as sweep_handler,
)


def test_stripe_signature_verification():
    secret = "whsec_test_secret_123"
    payload = b'{"id": "evt_test"}'
    now = int(time.time())
    signed_payload = f"{now}.".encode("utf-8") + payload
    sig = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    sig_header = f"t={now},v1={sig}"

    assert verify_stripe_signature(payload, sig_header, secret) is True
    # Tampered signature
    assert verify_stripe_signature(payload, f"t={now},v1=fake", secret) is False
    # Old timestamp (15 min ago)
    old_now = now - 900
    assert verify_stripe_signature(payload, f"t={old_now},v1={sig}", secret) is False


def test_stripe_webhook_dispute_created():
    event_body = {
        "id": "evt_123",
        "type": "charge.dispute.created",
        "data": {
            "object": {
                "id": "dp_S2",
                "metadata": {"scenario": "S2"}
            }
        }
    }
    raw_json = json.dumps(event_body)
    b64_body = base64.b64encode(raw_json.encode("utf-8")).decode("utf-8")

    event = {
        "isBase64Encoded": True,
        "body": b64_body,
        "headers": {"content-type": "application/json"}
    }

    with patch("infra.lambdas.stripe_webhook.app.invoke_bedrock_runtime") as mock_invoke:
        mock_invoke.return_value = {"accepted": True}
        resp = stripe_handler(event, None)
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["received"] is True
        assert data["event_type"] == "charge.dispute.created"
        mock_invoke.assert_called_once()
        args, kwargs = mock_invoke.call_args
        assert args[0]["type"] == "dispute.created"
        assert args[0]["dispute_id"] == "dp_S2"
        assert args[0]["scenario"] == "S2"


def test_stripe_webhook_dispute_closed():
    event_body = {
        "id": "evt_456",
        "type": "charge.dispute.closed",
        "data": {
            "object": {
                "id": "dp_S1",
                "status": "won",
                "reason": "product_not_received",
                "amount": 4800
            }
        }
    }
    event = {
        "isBase64Encoded": False,
        "body": json.dumps(event_body),
        "headers": {"content-type": "application/json"}
    }

    with patch("infra.lambdas.stripe_webhook.app.invoke_bedrock_runtime") as mock_invoke:
        mock_invoke.return_value = {"accepted": True}
        resp = stripe_handler(event, None)
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["received"] is True
        mock_invoke.assert_called_once()
        args, kwargs = mock_invoke.call_args
        assert args[0]["type"] == "dispute.closed"
        assert args[0]["dispute_id"] == "dp_S1"
        assert args[0]["status"] == "won"


def test_twilio_reply_parsing():
    assert parse_reply_answer("1") == "1"
    assert parse_reply_answer("fight") == "1"
    assert parse_reply_answer("FIGHT") == "1"
    assert parse_reply_answer("2") == "2"
    assert parse_reply_answer("concede") == "2"
    assert parse_reply_answer("CONCEDE") == "2"
    assert parse_reply_answer("3") == "3"
    assert parse_reply_answer("hold") == "3"
    assert parse_reply_answer("2. concede") == "2"


def test_twilio_signature_validation():
    auth_token = "auth_token_secret"
    url = "https://example.com/webhook"
    params = {"Body": "2", "From": "+15551234567"}
    
    s = url + "Body2From+15551234567"
    sig = base64.b64encode(hmac.new(auth_token.encode("utf-8"), s.encode("utf-8"), hashlib.sha1).digest()).decode("utf-8")
    
    assert validate_twilio_signature(url, params, sig, auth_token) is True
    assert validate_twilio_signature(url, params, "wrong_sig", auth_token) is False


def test_twilio_webhook_handler():
    form_body = "Body=2&From=%2B15551234567&MessageSid=SM123"
    event = {
        "isBase64Encoded": False,
        "body": form_body,
        "headers": {
            "content-type": "application/x-www-form-urlencoded"
        }
    }

    with patch("infra.lambdas.twilio_webhook.app.query_latest_pending_decision", return_value="dp_S2"):
        with patch("infra.lambdas.twilio_webhook.app.invoke_bedrock_approval") as mock_invoke:
            mock_invoke.return_value = {"accepted": True, "final_status": "lost"}
            resp = twilio_handler(event, None)
            assert resp["statusCode"] == 200
            assert "text/xml" in resp["headers"]["Content-Type"]
            assert "<Message>Got it</Message>" in resp["body"]
            mock_invoke.assert_called_once_with("dp_S2", "2")


def test_sweep_handler():
    event = {"source": "aws.events"}
    with patch("infra.lambdas.sweep.app.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp["response"].read.return_value = b'{"sweep_complete": true}'
        mock_client.invoke_agent_runtime.return_value = mock_resp

        resp = sweep_handler(event, None)
        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["sweep_triggered"] is True
        mock_client.invoke_agent_runtime.assert_called_once()
