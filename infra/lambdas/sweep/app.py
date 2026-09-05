import json
import os
import logging
import uuid
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AGENT_RUNTIME_ARN = os.environ.get(
    "AGENT_RUNTIME_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:292341338711:runtime/rebuttal-pASUe6CVmu"
)
AWS_REGION_NAME = os.environ.get("AWS_REGION_NAME", os.environ.get("AWS_REGION", "us-east-1"))


def lambda_handler(event, context):
    """Handle scheduled dispute deadline sweep."""
    logger.info("Executing scheduled sweep trigger event: %s", json.dumps(event))

    client = boto3.client("bedrock-agentcore", region_name=AWS_REGION_NAME)
    session_id = f"rebuttal-sweep-{uuid.uuid4().hex}"

    payload_dict = {
        "type": "sweep"
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")

    logger.info("Invoking AgentCore sweep ARN=%s session=%s", AGENT_RUNTIME_ARN, session_id)

    try:
        resp = client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            runtimeSessionId=session_id,
            qualifier="DEFAULT",
            contentType="application/json",
            accept="application/json",
            payload=payload_bytes
        )
        body = resp["response"].read().decode("utf-8")
        try:
            res = json.loads(body)
        except Exception:
            res = {"raw": body}

        logger.info("Sweep execution result: %s", res)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"sweep_triggered": True, "result": res})
        }
    except Exception as e:
        logger.exception("Error executing sweep: %s", e)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"sweep_triggered": False, "error": str(e)})
        }
