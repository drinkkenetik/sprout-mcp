"""Sprout Social MCP — FastMCP Streamable HTTP Server\n====================================================\nExposes Sprout Social API as MCP tools for Cowork.\nMatches Moe content engine architecture exactly.\n\nRun:\n  uvicorn mcp_app:app --host 0.0.0.0 --port $PORT\n"""

import json
import logging
import os
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Transport security: allow Railway hostname through DNS rebinding protection
# ---------------------------------------------------------------------------
_railway_host = os.environ.get(
    "RAILWAY_PUBLIC_DOMAIN",
    "sprout-mcp-production.up.railway.app",
)

_transport_security = TransportSecuritySettings(
    allowed_hosts=[
        _railway_host,
        "localhost",
        "127.0.0.1",
    ],
    enable_dns_rebinding_protection=True,
)

# ---------------------------------------------------------------------------
# FastMCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "sprout-social",
    instructions=(
        "Sprout Social MCP provides social media analytics, publishing, "
        "listening, and inbox management for Kenetik's social channels."
    ),
    transport_security=_transport_security,
)

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

def _cid(customer_id: str = "") -> str:
    result = customer_id or os.environ.get("SPROUT_CUSTOMER_ID", "")
    if not result:
        raise ValueError("customer_id required. Set SPROUT_CUSTOMER_ID env var.")
    return result

def _split(s: str) -> list:
    return [x.strip() for x in s.split(",") if x.strip()]

def _date(dt: str) -> str:
    return dt[:10]

def _err(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text
        return json.dumps({"error": f"HTTP {e.response.status_code}", "url": str(e.request.url), "detail": detail}, indent=2)
    return json.dumps({"error": type(e).__name__, "message": str(e)}, indent=2)


# ---------------------------------------------------------------------------
# Metadata Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_customers() -> str:
    """List all customers/accounts accessible with the current API token.\n\n    Returns customer IDs and names needed for other API calls.
    """
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{BASE_URL}/v1/metadata/client", headers=_headers(), timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def list_profiles(customer_id: str = "") -> str:
    """List all social profiles for a customer.\n\n    Args:\n        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{BASE_URL}/v1/{_cid(customer_id)}/metadata/customer", headers=_headers(), timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def list_tags(customer_id: str = "") -> str:
    """List all message tags for a customer.\n\n    Args:\n        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{BASE_URL}/v1/{_cid(customer_id)}/metadata/customer/tags", headers=_headers(), timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def list_groups(customer_id: str = "") -> str:
    """List all profile groups for a customer.\n\n    Args:\n        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{BASE_URL}/v1/{_cid(customer_id)}/metadata/customer/groups", headers=_headers(), timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def list_users(customer_id: str = "") -> str:
    """List all active users for a customer.\n\n    Args:\n        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{BASE_URL}/v1/{_cid(customer_id)}/metadata/customer/users", headers=_headers(), timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def list_teams(customer_id: str = "") -> str:
    """List all teams for a customer.\n\n    Args:\n        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{BASE_URL}/v1/{_cid(customer_id)}/metadata/customer/teams", headers=_headers(), timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


# ---------------------------------------------------------------------------
# Analytics Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_profile_analytics(
    profile_ids: str,
    start_time: str,
    end_time: str,
    metrics: str = "impressions,engagements,net_follower_growth",
    timezone: str = "UTC",
    customer_id: str = "",
) -> str:
    """Get analytics metrics aggregated by social profile.\n\n    Args:\n        profile_ids: Comma-separated Sprout profile IDs.\n        start_time: Start of period (ISO 8601, e.g. '2024-01-01T00:00:00').\n        end_time: End of period (ISO 8601, e.g. '2024-01-31T23:59:59').\n        metrics: Comma-separated metric names. Common options:\n                 impressions, engagements, net_follower_growth, engagement_rate,\n                 video_views, reactions, comments, shares, clicks.\n        timezone: Timezone for the report (e.g. 'America/Chicago'). Default: UTC.\n        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        ids = ",".join(_split(profile_ids))
        start_date = _date(start_time)
        end_date = _date(end_time)
        body = {
            "filters": [
                f"customer_profile_id.eq({ids})",
                f"reporting_period.in({start_date}...{end_date})",
            ],
            "metrics": _split(metrics),
            "timezone": timezone,
        }
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{BASE_URL}/v1/{_cid(customer_id)}/analytics/profiles", headers=_headers(), json=body, timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def get_post_analytics(
    profile_ids: str,
    start_time: str,
    end_time: str,
    metrics: str = "lifetime.impressions,lifetime.reactions,lifetime.engagements,lifetime.clicks",
    limit: int = 50,
    customer_id: str = "",
) -> str:
    """Get analytics metrics for individual published posts.\n\n    Post-level metrics require the 'lifetime.' prefix.\n    Common metrics: lifetime.impressions, lifetime.reactions, lifetime.engagements,\n                    lifetime.clicks, lifetime.shares, lifetime.comments, lifetime.video_views.\n\n    Use the count of returned posts as the post count for a profile.\n    Do NOT use get_messages with an OUTBOUND filter for post counts \u2014 that endpoint\n    only supports inbound inbox messages.\n\n    Args:\n        profile_ids: Comma-separated Sprout profile IDs.\n        start_time: Start of period (ISO 8601, e.g. '2024-01-01T00:00:00').\n        end_time: End of period (ISO 8601, e.g. '2024-01-31T23:59:59').\n        metrics: Comma-separated metric names with lifetime. prefix.\n        limit: Number of posts to return (default 50, max 100).\n        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        ids = ",".join(_split(profile_ids))
        body = {
            "filters": [
                f"customer_profile_id.eq({ids})",
                f"created_time.in({start_time}..{end_time})",
            ],
            "fields": ["created_time", "text", "perma_link"],
            "metrics": _split(metrics),
            "limit": limit,
            "sort": ["created_time:desc"],
        }
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{BASE_URL}/v1/{_cid(customer_id)}/analytics/posts", headers=_headers(), json=body, timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


# ---------------------------------------------------------------------------
# Listening Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_listening_topics(customer_id: str = "") -> str:
    """List all Listening topics configured for a customer.\n\n    Returns topic IDs and names needed for get_listening_messages.\n\n    Args:\n        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{BASE_URL}/v1/{_cid(customer_id)}/listening/topics", headers=_headers(), timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def get_listening_messages(
    topic_id: str,
    start_time: str,
    end_time: str,
    networks: str = "",
    limit: int = 100,
    cursor: str = "",
    customer_id: str = "",
) -> str:
    """Fetch messages from a Sprout Social Listening topic.\n\n    Use list_listening_topics first to get topic IDs.\n\n    Args:\n        topic_id: The listening topic ID (UUID).\n        start_time: Start datetime (ISO 8601, e.g. '2024-01-01T00:00:00').\n        end_time: End datetime (ISO 8601, e.g. '2024-01-31T23:59:59').\n        networks: Comma-separated networks to filter by. Options: REDDIT, TWITTER,\n                  FACEBOOK, INSTAGRAM, YOUTUBE, NEWS, BLOG. Leave empty for all.\n        limit: Number of messages to return per page (default 100, max 100).\n        cursor: Pagination cursor from a previous response (optional).\n        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        filters = [f"created_time.in({start_time}..{end_time})"]
        if networks:
            for network in _split(networks):
                filters.append(f"network.eq({network.upper()})")
        body = {
            "filters": filters,
            "fields": ["created_time", "text", "network", "perma_link", "language"],
            "limit": limit,
            "sort": ["created_time:desc"],
        }
        if cursor:
            body["cursor"] = cursor
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{BASE_URL}/v1/{_cid(customer_id)}/listening/topics/{topic_id}/messages", headers=_headers(), json=body, timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


# ---------------------------------------------------------------------------
# Messages Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_messages(
    profile_ids: str,
    start_time: str,
    end_time: str,
    tag_ids: str = "",
    limit: int = 50,
    page_cursor: str = "",
    customer_id: str = "",
) -> str:
    """Retrieve inbound inbox messages (Smart Inbox) with optional filtering.\n\n    This endpoint returns INBOUND messages only (mentions, DMs, comments).\n    For published post counts and performance metrics, use get_post_analytics instead.\n    For social listening data (Reddit, news, etc.), use get_listening_messages instead.\n\n    Args:\n        profile_ids: Comma-separated Sprout profile IDs.\n        start_time: Start datetime (ISO 8601, e.g. '2024-01-01T00:00:00').\n        end_time: End datetime (ISO 8601).\n        tag_ids: Comma-separated tag IDs to filter by (optional).\n        limit: Number of messages to return (default 50).\n        page_cursor: Pagination cursor from a previous response (optional).\n        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        ids = ",".join(_split(profile_ids))
        filters = [
            f"customer_profile_id.eq({ids})",
            f"created_time.in({start_time}..{end_time})",
        ]
        if tag_ids:
            tag_list = ",".join(_split(tag_ids))
            filters.append(f"tag_id.eq({tag_list})")
        body = {"filters": filters, "limit": limit}
        if page_cursor:
            body["page_cursor"] = page_cursor
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{BASE_URL}/v1/{_cid(customer_id)}/messages", headers=_headers(), json=body, timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


# ---------------------------------------------------------------------------
# Publishing Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_publishing_posts(
    profile_ids: str,
    start_time: str,
    end_time: str,
    status: str = "",
    limit: int = 50,
    customer_id: str = "",
) -> str:
    """List published, scheduled, or draft posts in Sprout Social.\n\n    Args:\n        profile_ids: Comma-separated Sprout profile IDs.\n        start_time: Start datetime (ISO 8601, e.g. '2024-01-01T00:00:00').\n        end_time: End datetime (ISO 8601).\n        status: Filter by post status: PUBLISHED, SCHEDULED, DRAFT. Leave empty for all.\n        limit: Number of posts to return (default 50).\n        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        ids = ",".join(_split(profile_ids))
        filters = [
            f"customer_profile_id.eq({ids})",
            f"created_time.in({start_time}..{end_time})",
        ]
        if status:
            filters.append(f"status.eq({status.upper()})")
        body = {
            "filters": filters,
            "limit": limit,
            "sort": ["created_time:desc"],
        }
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{BASE_URL}/v1/{_cid(customer_id)}/publishing/posts", headers=_headers(), json=body, timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def create_post(
    profile_ids: str,
    text: str,
    scheduled_send_time: str = "",
    customer_id: str = "",
) -> str:
    """Create a draft or scheduled post in Sprout Social.\n\n    Args:\n        profile_ids: Comma-separated Sprout profile IDs to publish to.\n        text: Post content/body text.\n        scheduled_send_time: When to publish (ISO 8601). Leave empty to save as draft.\n        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        body = {
            "post_type": "OUTBOUND",
            "profile_ids": _split(profile_ids),
            "fields": {"text": text},
        }
        if scheduled_send_time:
            body["scheduled_send_time"] = scheduled_send_time
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{BASE_URL}/v1/{_cid(customer_id)}/publishing/posts", headers=_headers(), json=body, timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


@mcp.tool()
async def get_publishing_post(
    post_id: str,
    customer_id: str = "",
) -> str:
    """Retrieve a specific publishing post by ID.\n\n    Args:\n        post_id: The publishing post ID to retrieve.\n        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{BASE_URL}/v1/{_cid(customer_id)}/publishing/posts/{post_id}", headers=_headers(), timeout=30)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return _err(e)


# ---------------------------------------------------------------------------
# ASGI app for uvicorn (Streamable HTTP transport)
# ---------------------------------------------------------------------------
app = mcp.streamable_http_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Sprout Social MCP server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
