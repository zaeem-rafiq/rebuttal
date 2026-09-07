"""
agent/tools/gateway_client.py

Client helper to interact with Bedrock AgentCore Gateway over streamable HTTP using Strands MCPClient.
Provides authentication via Cognito client credentials and retrieves MCP tools (lookup_order, get_tracking).
"""

import json
import logging
import os
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from strands.tools.mcp import MCPClient

load_dotenv()

logger = logging.getLogger("rebuttal.gateway_client")

_cached_token: Optional[str] = None
_cached_token_expires_at: float = 0.0


def load_gateway_config() -> Optional[Dict[str, Any]]:
    """Load Gateway configuration from data/gateway_config.json or environment variables."""
    config_file = os.path.join(os.path.dirname(__file__), "..", "..", "data", "gateway_config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load gateway_config.json: %s", e)

    gw_url = os.getenv("GATEWAY_URL")
    if gw_url:
        return {
            "gateway_url": gw_url,
            "client_info": {
                "client_id": os.getenv("GATEWAY_CLIENT_ID"),
                "client_secret": os.getenv("GATEWAY_CLIENT_SECRET"),
                "token_endpoint": os.getenv("GATEWAY_TOKEN_ENDPOINT"),
                "scope": os.getenv("GATEWAY_SCOPE", "rebuttal-mcp-gateway/invoke"),
            },
        }
    return None


def get_gateway_token(force_refresh: bool = False) -> Optional[str]:
    """Retrieve an OAuth 2.0 access token using client credentials flow from Cognito."""
    global _cached_token, _cached_token_expires_at
    now = time.time()
    if _cached_token and now < _cached_token_expires_at and not force_refresh:
        return _cached_token

    cfg = load_gateway_config()
    if not cfg or "client_info" not in cfg:
        return None

    ci = cfg["client_info"]
    token_url = ci.get("token_endpoint")
    client_id = ci.get("client_id")
    client_secret = ci.get("client_secret")
    scope = ci.get("scope", "rebuttal-mcp-gateway/invoke")

    if not (token_url and client_id and client_secret):
        return None

    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
    }).encode("utf-8")

    req = urllib.request.Request(
        token_url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            _cached_token = res.get("access_token")
            expires_in = res.get("expires_in", 3600)
            _cached_token_expires_at = now + float(expires_in) - 60.0
            return _cached_token
    except Exception as e:
        logger.error("Failed to fetch Gateway OAuth token: %s", e)
        return None


def create_gateway_mcp_client(startup_timeout: int = 30) -> Optional[MCPClient]:
    """Create an instance of Strands MCPClient configured for the AgentCore Gateway."""
    cfg = load_gateway_config()
    if not cfg:
        return None

    url = cfg.get("gateway_url")
    token = get_gateway_token()
    if not url or not token:
        return None

    return MCPClient(
        url=url,
        headers={"Authorization": f"Bearer {token}"},
        startup_timeout=startup_timeout,
        continue_on_error=True,
    )


def get_gateway_tools(startup_timeout: int = 30) -> List[Any]:
    """Connect to the Bedrock AgentCore Gateway and retrieve the exposed MCP tools."""
    from strands.tools.mcp.mcp_agent_tool import MCPAgentTool

    client = create_gateway_mcp_client(startup_timeout=startup_timeout)
    if not client:
        return []
    try:
        client.start()
        raw_tools = client.list_tools_sync()
        adapted_tools = []
        for t in raw_tools:
            mcp_name = getattr(t.mcp_tool, "name", t.tool_name)
            if "___" in mcp_name:
                clean_name = mcp_name.split("___")[-1]
            else:
                clean_name = mcp_name
            if clean_name in ("lookup_order", "get_tracking"):
                adapted = MCPAgentTool(t.mcp_tool, client, name_override=clean_name)
                adapted_tools.append(adapted)

        logger.info("Retrieved %d tools from AgentCore Gateway: %s", len(adapted_tools), [t.tool_name for t in adapted_tools])
        return adapted_tools
    except Exception as e:
        logger.error("Failed to retrieve tools from Gateway: %s", e)
        return []
