"""
scripts/deploy_gateway.py

Deploy Bedrock AgentCore Gateway and Lambda target exposing `lookup_order` and `get_tracking`
backed by Supabase REST API as MCP tools over streamable HTTP.
"""

import io
import json
import logging
import os
import sys
import time
import zipfile
import boto3
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("deploy_gateway")

REGION = os.getenv("AWS_REGION", "us-east-1")
GATEWAY_NAME = "rebuttal-mcp-gateway"
TARGET_NAME = "rebuttal-evidence-tools"
LAMBDA_NAME = "rebuttal-gateway-tools"
ROLE_NAME = "AgentCoreGatewayLambdaRole"

from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
from bedrock_agentcore_starter_toolkit.operations.gateway.create_role import append_lambda_target_permission
from bedrock_agentcore_starter_toolkit.utils.runtime.create_with_iam_eventual_consistency import (
    retry_create_with_eventual_iam_consistency,
)


def ensure_lambda_role(iam_client) -> str:
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    try:
        resp = iam_client.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Execution role for Rebuttal Gateway Tools Lambda",
        )
        role_arn = resp["Role"]["Arn"]
        iam_client.attach_role_policy(
            RoleName=ROLE_NAME,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        )
        logger.info("Created Lambda execution role: %s", role_arn)
        time.sleep(10)  # IAM eventual consistency
        return role_arn
    except iam_client.exceptions.EntityAlreadyExistsException:
        role = iam_client.get_role(RoleName=ROLE_NAME)
        return role["Role"]["Arn"]


def package_lambda_zip() -> bytes:
    app_path = os.path.join(os.path.dirname(__file__), "..", "infra", "lambdas", "gateway_tools", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        app_code = f.read()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("app.py", app_code)
    buf.seek(0)
    return buf.read()


def deploy_lambda(session, role_arn: str) -> str:
    lambda_client = session.client("lambda", region_name=REGION)
    zip_bytes = package_lambda_zip()

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")

    env_vars = {
        "SUPABASE_URL": supabase_url,
        "SUPABASE_SERVICE_KEY": supabase_key,
    }

    try:
        resp = lambda_client.get_function(FunctionName=LAMBDA_NAME)
        lambda_arn = resp["Configuration"]["FunctionArn"]
        logger.info("Updating existing Lambda code and config: %s", lambda_arn)
        lambda_client.update_function_code(FunctionName=LAMBDA_NAME, ZipFile=zip_bytes)
        try:
            waiter = lambda_client.get_waiter("function_updated")
            waiter.wait(FunctionName=LAMBDA_NAME, WaiterConfig={"Delay": 2, "MaxAttempts": 15})
        except Exception:
            time.sleep(5)
        lambda_client.update_function_configuration(
            FunctionName=LAMBDA_NAME,
            Environment={"Variables": env_vars},
            Timeout=30,
        )
        return lambda_arn
    except lambda_client.exceptions.ResourceNotFoundException:
        logger.info("Creating Lambda function: %s", LAMBDA_NAME)

        def _create():
            return lambda_client.create_function(
                FunctionName=LAMBDA_NAME,
                Runtime="python3.12",
                Role=role_arn,
                Handler="app.lambda_handler",
                Code={"ZipFile": zip_bytes},
                Description="Rebuttal Gateway Tools Lambda exposing lookup_order and get_tracking",
                Timeout=30,
                Environment={"Variables": env_vars},
            )

        resp = retry_create_with_eventual_iam_consistency(_create, role_arn)
        return resp["FunctionArn"]


def main():
    logger.info("Deploying Bedrock AgentCore Gateway for Rebuttal (HAC-18 / S-B)...")
    session = boto3.Session(region_name=REGION)
    iam_client = session.client("iam")
    lambda_client = session.client("lambda", region_name=REGION)

    role_arn = ensure_lambda_role(iam_client)
    lambda_arn = deploy_lambda(session, role_arn)
    logger.info("✓ Lambda function ready: %s", lambda_arn)

    gw_client = GatewayClient(region_name=REGION)

    # Check if gateway already exists
    gateways = gw_client.list_gateways().get("items", [])
    existing_gw = next((g for g in gateways if g.get("name") == GATEWAY_NAME), None)

    gateway = None
    cognito_info = None

    config_file = os.path.join(os.path.dirname(__file__), "..", "data", "gateway_config.json")
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            cognito_info = json.load(f)

    if existing_gw:
        logger.info("Found existing Gateway: %s (%s)", existing_gw.get("gatewayId"), existing_gw.get("gatewayUrl"))
        res = gw_client.get_gateway(gateway_identifier=existing_gw["gatewayId"])
        gateway = res.get("gateway", res)
    else:
        logger.info("Creating Cognito OAuth authorizer...")
        cognito_info = gw_client.create_oauth_authorizer_with_cognito(GATEWAY_NAME)
        logger.info("Creating MCP Gateway...")
        gateway = gw_client.create_mcp_gateway(
            name=GATEWAY_NAME,
            authorizer_config=cognito_info["authorizer_config"],
            enable_observability=False,
        )

    # Save cognito client info
    if cognito_info:
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        cognito_info["gateway_url"] = gateway["gatewayUrl"]
        cognito_info["gateway_id"] = gateway["gatewayId"]
        cognito_info["gateway_arn"] = gateway["gatewayArn"]
        with open(config_file, "w") as f:
            json.dump(cognito_info, f, indent=2)
        logger.info("Saved Gateway config to %s", config_file)

    # Allow Gateway to invoke Lambda
    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId="AllowAgentCoreGatewayInvoke",
            Action="lambda:InvokeFunction",
            Principal="bedrock-agentcore.amazonaws.com",
            SourceArn=gateway["gatewayArn"],
        )
        logger.info("✓ Added Lambda invoke permission for Gateway service principal")
    except lambda_client.exceptions.ResourceConflictException:
        logger.info("Lambda invoke permission already present.")
    except Exception as e:
        logger.warning("Could not add Lambda permission (may already exist): %s", e)

    # Scoped lambda invoke permission on gateway role
    append_lambda_target_permission(
        session=session,
        logger=logger,
        role_arn=gateway["roleArn"],
        function_arn=lambda_arn,
        region=REGION,
    )

    # Check if target exists
    targets = gw_client.list_gateway_targets(gateway_identifier=gateway["gatewayId"]).get("items", [])
    existing_target = next((t for t in targets if t.get("name") == TARGET_NAME), None)

    tool_schema = {
        "inlinePayload": [
            {
                "name": "lookup_order",
                "description": "Retrieve full order details, line items, card check indicators, and customer billing/shipping details.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"order_id": {"type": "string"}},
                    "required": ["order_id"],
                },
            },
            {
                "name": "get_tracking",
                "description": "Retrieve fulfillment and delivery tracking information, carrier timestamps, and signature confirmation.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "tracking_number": {"type": "string"},
                    },
                },
            },
        ]
    }

    if not existing_target:
        logger.info("Creating MCP Gateway Target: %s", TARGET_NAME)
        target = gw_client.create_mcp_gateway_target(
            gateway=gateway,
            name=TARGET_NAME,
            target_type="lambda",
            target_payload={
                "lambdaArn": lambda_arn,
                "toolSchema": tool_schema,
            },
        )
        logger.info("✓ Gateway Target ready: %s", target.get("targetId"))
    else:
        logger.info("Gateway Target already exists: %s", existing_target.get("targetId"))

    logger.info("Testing Cognito access token retrieval...")
    token = gw_client.get_access_token_for_cognito(cognito_info["client_info"])
    logger.info("✓ Successfully retrieved access token!")

    print("\n=== GATEWAY DEPLOYMENT SUMMARY ===")
    print(f"Gateway URL: {gateway['gatewayUrl']}")
    print(f"Gateway ID:  {gateway['gatewayId']}")
    print(f"Target Name: {TARGET_NAME}")
    print(f"Token acquired: {token[:15]}...")


if __name__ == "__main__":
    main()
