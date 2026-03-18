"""Sprout Social MCP — HTTP Transport for Railway\n\nWraps the sprout-mcp STDIO server as an HTTP JSON-RPC 2.0 endpoint\nso Cowork plugins can reach it over the network.\n"""

import json
import logging
import os
from functools import wraps

from flask import Flask, request, jsonify
import httpx

app = Flask(__name__)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Sprout Social API Client
# ---------------------------------------------------------------------------

BASE_URL = "https://api.sproutsocial.com"

def _headers():
    token = os.environ.get("SPROUT_API_TOKEN", "")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def _cid(customer_id=""):
    return customer_id or os.environ.get("SPROUT_CUSTOMER_ID", "")

def _split(s):
    return [x.strip() for x in s.split(",") if x.strip()]

def _date(dt):
    return dt[:10]


# ---------------------------------------------------------------------------
# MCP Tool Registry
# ---------------------------------------------------------------------------

MCP_TOOLS = {}

def mcp_tool(name, description, input_schema):
    def decorator(func):
        MCP_TOOLS[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
            "handler": func,
        }
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def verify_auth():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    token = auth_header[7:]
    expected = os.environ.get("MCP_API_KEY", "")
    if not expected:
        return True  # No key set = dev mode
    return token == expected


# ---------------------------------------------------------------------------
# Tool Implementations
# ---------------------------------------------------------------------------

@mcp_tool(
    name="list_customers",
    description="List all customers/accounts accessible with the current API token. Returns customer IDs and names needed for other API calls.",
    input_schema={"type": "object", "properties": {}},
)
def handle_list_customers(params):
    try:
        r = httpx.get(f"{BASE_URL}/v1/metadata/client", headers=_headers(), timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp_tool(
    name="list_profiles",
    description="List all social profiles for a customer.",
    input_schema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "default": "", "description": "Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var."},
        },
    },
)
def handle_list_profiles(params):
    try:
        cid = _cid(params.get("customer_id", ""))
        r = httpx.get(f"{BASE_URL}/v1/{cid}/metadata/customer", headers=_headers(), timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp_tool(
    name="list_tags",
    description="List all message tags for a customer.",
    input_schema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "default": "", "description": "Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var."},
        },
    },
)
def handle_list_tags(params):
    try:
        cid = _cid(params.get("customer_id", ""))
        r = httpx.get(f"{BASE_URL}/v1/{cid}/metadata/customer/tags", headers=_headers(), timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp_tool(
    name="list_groups",
    description="List all profile groups for a customer.",
    input_schema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "default": "", "description": "Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var."},
        },
    },
)
def handle_list_groups(params):
    try:
        cid = _cid(params.get("customer_id", ""))
        r = httpx.get(f"{BASE_URL}/v1/{cid}/metadata/customer/groups", headers=_headers(), timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp_tool(
    name="list_users",
    description="List all active users for a customer.",
    input_schema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "default": "", "description": "Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var."},
        },
    },
)
def handle_list_users(params):
    try:
        cid = _cid(params.get("customer_id", ""))
        r = httpx.get(f"{BASE_URL}/v1/{cid}/metadata/customer/users", headers=_headers(), timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp_tool(
    name="list_teams",
    description="List all teams for a customer.",
    input_schema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "default": "", "description": "Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var."},
        },
    },
)
def handle_list_teams(params):
    try:
        cid = _cid(params.get("customer_id", ""))
        r = httpx.get(f"{BASE_URL}/v1/{cid}/metadata/customer/teams", headers=_headers(), timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp_tool(
    name="get_profile_analytics",
    description="Get analytics metrics aggregated by social profile.",
    input_schema={
        "type": "object",
        "properties": {
            "profile_ids": {"type": "string", "description": "Comma-separated Sprout profile IDs."},
            "start_time": {"type": "string", "description": "Start of period (ISO 8601)."},
            "end_time": {"type": "string", "description": "End of period (ISO 8601)."},
            "metrics": {"type": "string", "default": "impressions,engagements,net_follower_growth", "description": "Comma-separated metric names."},
            "timezone": {"type": "string", "default": "UTC", "description": "Timezone for the report."},
            "customer_id": {"type": "string", "default": ""},
        },
        "required": ["profile_ids", "start_time", "end_time"],
    },
)
def handle_get_profile_analytics(params):
    try:
        cid = _cid(params.get("customer_id", ""))
        ids = ",".join(_split(params["profile_ids"]))
        start_date = _date(params["start_time"])
        end_date = _date(params["end_time"])
        body = {
            "filters": [
                f"customer_profile_id.eq({ids})",
                f"reporting_period.in({start_date}...{end_date})",
            ],
            "metrics": _split(params.get("metrics", "impressions,engagements,net_follower_growth")),
            "timezone": params.get("timezone", "UTC"),
        }
        r = httpx.post(f"{BASE_URL}/v1/{cid}/analytics/profiles", headers=_headers(), json=body, timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp_tool(
    name="get_post_analytics",
    description="Get analytics metrics for individual published posts. Post-level metrics require the 'lifetime.' prefix.",
    input_schema={
        "type": "object",
        "properties": {
            "profile_ids": {"type": "string", "description": "Comma-separated Sprout profile IDs."},
            "start_time": {"type": "string", "description": "Start of period (ISO 8601)."},
            "end_time": {"type": "string", "description": "End of period (ISO 8601)."},
            "metrics": {"type": "string", "default": "lifetime.impressions,lifetime.reactions,lifetime.engagements,lifetime.clicks"},
            "limit": {"type": "number", "default": 50},
            "customer_id": {"type": "string", "default": ""},
        },
        "required": ["profile_ids", "start_time", "end_time"],
    },
)
def handle_get_post_analytics(params):
    try:
        cid = _cid(params.get("customer_id", ""))
        ids = ",".join(_split(params["profile_ids"]))
        body = {
            "filters": [
                f"customer_profile_id.eq({ids})",
                f"created_time.in({params['start_time']}..{params['end_time']})",
            ],
            "fields": ["created_time", "text", "perma_link"],
            "metrics": _split(params.get("metrics", "lifetime.impressions,lifetime.reactions,lifetime.engagements,lifetime.clicks")),
            "limit": params.get("limit", 50),
            "sort": ["created_time:desc"],
        }
        r = httpx.post(f"{BASE_URL}/v1/{cid}/analytics/posts", headers=_headers(), json=body, timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp_tool(
    name="list_listening_topics",
    description="List all Listening topics configured for a customer.",
    input_schema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "default": ""},
        },
    },
)
def handle_list_listening_topics(params):
    try:
        cid = _cid(params.get("customer_id", ""))
        r = httpx.get(f"{BASE_URL}/v1/{cid}/listening/topics", headers=_headers(), timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp_tool(
    name="get_listening_messages",
    description="Fetch messages from a Sprout Social Listening topic.",
    input_schema={
        "type": "object",
        "properties": {
            "topic_id": {"type": "string", "description": "The listening topic ID (UUID)."},
            "start_time": {"type": "string", "description": "Start datetime (ISO 8601)."},
            "end_time": {"type": "string", "description": "End datetime (ISO 8601)."},
            "networks": {"type": "string", "default": "", "description": "Comma-separated networks to filter by."},
            "limit": {"type": "number", "default": 100},
            "cursor": {"type": "string", "default": ""},
            "customer_id": {"type": "string", "default": ""},
        },
        "required": ["topic_id", "start_time", "end_time"],
    },
)
def handle_get_listening_messages(params):
    try:
        cid = _cid(params.get("customer_id", ""))
        filters = [f"created_time.in({params['start_time']}..{params['end_time']})"]
        networks = params.get("networks", "")
        if networks:
            for network in _split(networks):
                filters.append(f"network.eq({network.upper()})")
        body = {
            "filters": filters,
            "fields": ["created_time", "text", "network", "perma_link", "language"],
            "limit": params.get("limit", 100),
            "sort": ["created_time:desc"],
        }
        cursor = params.get("cursor", "")
        if cursor:
            body["cursor"] = cursor
        r = httpx.post(f"{BASE_URL}/v1/{cid}/listening/topics/{params['topic_id']}/messages", headers=_headers(), json=body, timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp_tool(
    name="get_messages",
    description="Retrieve inbound inbox messages (Smart Inbox) with optional filtering. Returns INBOUND messages only.",
    input_schema={
        "type": "object",
        "properties": {
            "profile_ids": {"type": "string", "description": "Comma-separated Sprout profile IDs."},
            "start_time": {"type": "string", "description": "Start datetime (ISO 8601)."},
            "end_time": {"type": "string", "description": "End datetime (ISO 8601)."},
            "tag_ids": {"type": "string", "default": ""},
            "limit": {"type": "number", "default": 50},
            "page_cursor": {"type": "string", "default": ""},
            "customer_id": {"type": "string", "default": ""},
        },
        "required": ["profile_ids", "start_time", "end_time"],
    },
)
def handle_get_messages(params):
    try:
        cid = _cid(params.get("customer_id", ""))
        ids = ",".join(_split(params["profile_ids"]))
        filters = [
            f"customer_profile_id.eq({ids})",
            f"created_time.in({params['start_time']}..{params['end_time']})",
        ]
        tag_ids = params.get("tag_ids", "")
        if tag_ids:
            tag_list = ",".join(_split(tag_ids))
            filters.append(f"tag_id.eq({tag_list})")
        body = {"filters": filters, "limit": params.get("limit", 50)}
        page_cursor = params.get("page_cursor", "")
        if page_cursor:
            body["page_cursor"] = page_cursor
        r = httpx.post(f"{BASE_URL}/v1/{cid}/messages", headers=_headers(), json=body, timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp_tool(
    name="list_publishing_posts",
    description="List published, scheduled, or draft posts in Sprout Social.",
    input_schema={
        "type": "object",
        "properties": {
            "profile_ids": {"type": "string", "description": "Comma-separated Sprout profile IDs."},
            "start_time": {"type": "string", "description": "Start datetime (ISO 8601)."},
            "end_time": {"type": "string", "description": "End datetime (ISO 8601)."},
            "status": {"type": "string", "default": "", "description": "Filter by post status: PUBLISHED, SCHEDULED, DRAFT."},
            "limit": {"type": "number", "default": 50},
            "customer_id": {"type": "string", "default": ""},
        },
        "required": ["profile_ids", "start_time", "end_time"],
    },
)
def handle_list_publishing_posts(params):
    try:
        cid = _cid(params.get("customer_id", ""))
        ids = ",".join(_split(params["profile_ids"]))
        filters = [
            f"customer_profile_id.eq({ids})",
            f"created_time.in({params['start_time']}..{params['end_time']})",
        ]
        status = params.get("status", "")
        if status:
            filters.append(f"status.eq({status.upper()})")
        body = {
            "filters": filters,
            "limit": params.get("limit", 50),
            "sort": ["created_time:desc"],
        }
        r = httpx.post(f"{BASE_URL}/v1/{cid}/publishing/posts", headers=_headers(), json=body, timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp_tool(
    name="create_post",
    description="Create a draft or scheduled post in Sprout Social.",
    input_schema={
        "type": "object",
        "properties": {
            "profile_ids": {"type": "string", "description": "Comma-separated Sprout profile IDs to publish to."},
            "text": {"type": "string", "description": "Post content/body text."},
            "scheduled_send_time": {"type": "string", "default": "", "description": "When to publish (ISO 8601). Leave empty for draft."},
            "customer_id": {"type": "string", "default": ""},
        },
        "required": ["profile_ids", "text"],
    },
)
def handle_create_post(params):
    try:
        cid = _cid(params.get("customer_id", ""))
        body = {
            "post_type": "OUTBOUND",
            "profile_ids": _split(params["profile_ids"]),
            "fields": {"text": params["text"]},
        }
        sst = params.get("scheduled_send_time", "")
        if sst:
            body["scheduled_send_time"] = sst
        r = httpx.post(f"{BASE_URL}/v1/{cid}/publishing/posts", headers=_headers(), json=body, timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp_tool(
    name="get_publishing_post",
    description="Retrieve a specific publishing post by ID.",
    input_schema={
        "type": "object",
        "properties": {
            "post_id": {"type": "string", "description": "The publishing post ID."},
            "customer_id": {"type": "string", "default": ""},
        },
        "required": ["post_id"],
    },
)
def handle_get_publishing_post(params):
    try:
        cid = _cid(params.get("customer_id", ""))
        r = httpx.get(f"{BASE_URL}/v1/{cid}/publishing/posts/{params['post_id']}", headers=_headers(), timeout=30)
        r.raise_for_status()
        return {"result": json.dumps(r.json(), indent=2)}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


# ---------------------------------------------------------------------------
# MCP JSON-RPC 2.0 Handler
# ---------------------------------------------------------------------------

def handle_mcp_request(data):
    method = data.get("method", "")
    params = data.get("params", {})
    request_id = data.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "sprout-social-mcp", "version": "1.0.0"},
            },
        }

    if method == "tools/list":
        tools = []
        for name, tool_def in MCP_TOOLS.items():
            tools.append({
                "name": tool_def["name"],
                "description": tool_def["description"],
                "inputSchema": tool_def["inputSchema"],
            })
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        if tool_name not in MCP_TOOLS:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }
        try:
            handler = MCP_TOOLS[tool_name]["handler"]
            result = handler(tool_args)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}],
                    "isError": "error" in result and result.get("status") == "failed",
                },
            }
        except Exception as e:
            logger.error(f"Tool {tool_name} error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps({"error": str(e), "status": "failed"})}],
                    "isError": True,
                },
            }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


@app.route("/mcp", methods=["POST"])
def mcp_endpoint():
    if not verify_auth():
        return jsonify({"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": "Unauthorized"}}), 401

    content_type = request.content_type or ""
    if "json" not in content_type:
        return jsonify({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Content-Type must be application/json"}}), 400

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}), 400

    if not data:
        return jsonify({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request"}}), 400

    if isinstance(data, list):
        responses = [handle_mcp_request(req) for req in data]
        return jsonify(responses)

    return jsonify(handle_mcp_request(data))


@app.route("/mcp/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "server": "sprout-social-mcp",
        "version": "1.0.0",
        "tools": list(MCP_TOOLS.keys()),
        "tool_count": len(MCP_TOOLS),
    })


@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "ok", "service": "sprout-social-mcp"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
