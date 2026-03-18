"""Sprout Social MCP — FastMCP Streamable HTTP Server
====================================================
Exposes Sprout Social API as MCP tools via Streamable HTTP transport.
Deployed on Railway, consumed by KGS plugin in Cowork.

Tools:
1.  list_customers         — List accessible accounts
2.  list_profiles           — List social profiles
3.  list_tags               — List message tags
4.  list_groups             — List profile groups
5.  list_users              — List active users
6.  list_teams              — List teams
7.  get_profile_analytics   — Profile-level metrics
8.  get_post_analytics      — Post-level metrics
9.  list_listening_topics   — Listening topics
10. get_listening_messages  — Listening topic messages
11. get_messages            — Smart Inbox messages
12. list_publishing_posts   — Published/scheduled/draft posts
13. create_post             — Create draft or scheduled post
14. get_publishing_post     — Get single post by ID

Run:
  uvicorn app:app --host 0.0.0.0 --port $PORT
"""

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
# Transport security: allow Railway hostname
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
        "listening, and inbox management for Kenetik's 5 social profiles."
    ),
    transport_security=_transport_security,
)

# ---------------------------------------------------------------------------
# Sprout Social API helpers
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
# Tool 1: list_customers
# ---------------------------------------------------------------------------
@mcp.tool()
def list_customers() -> str:
    """List all customers/accounts accessible with the current API token.
    Returns customer IDs and names needed for other API calls."""
    try:
        r = httpx.get(f"{BASE_URL}/v1/metadata/client", headers=_headers(), timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# Tool 2: list_profiles
# ---------------------------------------------------------------------------
@mcp.tool()
def list_profiles(customer_id: str = "") -> str:
    """List all social profiles for a customer.

    Args:
        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        cid = _cid(customer_id)
        r = httpx.get(f"{BASE_URL}/v1/{cid}/metadata/customer", headers=_headers(), timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# Tool 3: list_tags
# ---------------------------------------------------------------------------
@mcp.tool()
def list_tags(customer_id: str = "") -> str:
    """List all message tags for a customer.

    Args:
        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        cid = _cid(customer_id)
        r = httpx.get(f"{BASE_URL}/v1/{cid}/metadata/customer/tags", headers=_headers(), timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# Tool 4: list_groups
# ---------------------------------------------------------------------------
@mcp.tool()
def list_groups(customer_id: str = "") -> str:
    """List all profile groups for a customer.

    Args:
        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        cid = _cid(customer_id)
        r = httpx.get(f"{BASE_URL}/v1/{cid}/metadata/customer/groups", headers=_headers(), timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# Tool 5: list_users
# ---------------------------------------------------------------------------
@mcp.tool()
def list_users(customer_id: str = "") -> str:
    """List all active users for a customer.

    Args:
        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        cid = _cid(customer_id)
        r = httpx.get(f"{BASE_URL}/v1/{cid}/metadata/customer/users", headers=_headers(), timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# Tool 6: list_teams
# ---------------------------------------------------------------------------
@mcp.tool()
def list_teams(customer_id: str = "") -> str:
    """List all teams for a customer.

    Args:
        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        cid = _cid(customer_id)
        r = httpx.get(f"{BASE_URL}/v1/{cid}/metadata/customer/teams", headers=_headers(), timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# Tool 7: get_profile_analytics
# ---------------------------------------------------------------------------
@mcp.tool()
def get_profile_analytics(
    profile_ids: str,
    start_time: str,
    end_time: str,
    metrics: str = "impressions,engagements,net_follower_growth",
    timezone: str = "America/New_York",
    customer_id: str = "",
) -> str:
    """Get analytics metrics aggregated by social profile.

    Args:
        profile_ids: Comma-separated Sprout profile IDs.
        start_time: Start of period (ISO 8601, e.g. 2026-03-10).
        end_time: End of period (ISO 8601, e.g. 2026-03-17).
        metrics: Comma-separated metric names (impressions, engagements, net_follower_growth, engagement_rate, video_views, reactions, comments, shares).
        timezone: Timezone for the report.
        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        cid = _cid(customer_id)
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
        r = httpx.post(f"{BASE_URL}/v1/{cid}/analytics/profiles", headers=_headers(), json=body, timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# Tool 8: get_post_analytics
# ---------------------------------------------------------------------------
@mcp.tool()
def get_post_analytics(
    profile_ids: str,
    start_time: str,
    end_time: str,
    metrics: str = "lifetime.impressions,lifetime.reactions,lifetime.engagements,lifetime.clicks",
    limit: int = 50,
    customer_id: str = "",
) -> str:
    """Get analytics metrics for individual published posts.

    Args:
        profile_ids: Comma-separated Sprout profile IDs.
        start_time: Start of period (ISO 8601).
        end_time: End of period (ISO 8601).
        metrics: Comma-separated metric names. Post-level metrics require 'lifetime.' prefix.
        limit: Maximum number of posts to return.
        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        cid = _cid(customer_id)
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
        r = httpx.post(f"{BASE_URL}/v1/{cid}/analytics/posts", headers=_headers(), json=body, timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# Tool 9: list_listening_topics
# ---------------------------------------------------------------------------
@mcp.tool()
def list_listening_topics(customer_id: str = "") -> str:
    """List all Listening topics configured for a customer.

    Args:
        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        cid = _cid(customer_id)
        r = httpx.get(f"{BASE_URL}/v1/{cid}/listening/topics", headers=_headers(), timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# Tool 10: get_listening_messages
# ---------------------------------------------------------------------------
@mcp.tool()
def get_listening_messages(
    topic_id: str,
    start_time: str,
    end_time: str,
    networks: str = "",
    limit: int = 100,
    cursor: str = "",
    customer_id: str = "",
) -> str:
    """Fetch messages from a Sprout Social Listening topic.

    Args:
        topic_id: The listening topic ID (UUID).
        start_time: Start datetime (ISO 8601).
        end_time: End datetime (ISO 8601).
        networks: Comma-separated networks to filter by.
        limit: Maximum messages to return.
        cursor: Pagination cursor from previous response.
        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        cid = _cid(customer_id)
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
        r = httpx.post(
            f"{BASE_URL}/v1/{cid}/listening/topics/{topic_id}/messages",
            headers=_headers(), json=body, timeout=30,
        )
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# Tool 11: get_messages
# ---------------------------------------------------------------------------
@mcp.tool()
def get_messages(
    profile_ids: str,
    start_time: str,
    end_time: str,
    tag_ids: str = "",
    limit: int = 50,
    page_cursor: str = "",
    customer_id: str = "",
) -> str:
    """Retrieve inbound inbox messages (Smart Inbox) with optional filtering.

    Args:
        profile_ids: Comma-separated Sprout profile IDs.
        start_time: Start datetime (ISO 8601).
        end_time: End datetime (ISO 8601).
        tag_ids: Comma-separated tag IDs to filter by.
        limit: Maximum messages to return.
        page_cursor: Pagination cursor from previous response.
        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        cid = _cid(customer_id)
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
        r = httpx.post(f"{BASE_URL}/v1/{cid}/messages", headers=_headers(), json=body, timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# Tool 12: list_publishing_posts
# ---------------------------------------------------------------------------
@mcp.tool()
def list_publishing_posts(
    profile_ids: str,
    start_time: str,
    end_time: str,
    status: str = "",
    limit: int = 50,
    customer_id: str = "",
) -> str:
    """List published, scheduled, or draft posts in Sprout Social.

    Args:
        profile_ids: Comma-separated Sprout profile IDs.
        start_time: Start datetime (ISO 8601).
        end_time: End datetime (ISO 8601).
        status: Filter by post status: PUBLISHED, SCHEDULED, DRAFT. Leave empty for all.
        limit: Maximum posts to return.
        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        cid = _cid(customer_id)
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
        r = httpx.post(f"{BASE_URL}/v1/{cid}/publishing/posts", headers=_headers(), json=body, timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# Tool 13: create_post
# ---------------------------------------------------------------------------
@mcp.tool()
def create_post(
    profile_ids: str,
    text: str,
    scheduled_send_time: str = "",
    customer_id: str = "",
) -> str:
    """Create a draft or scheduled post in Sprout Social.

    Args:
        profile_ids: Comma-separated Sprout profile IDs to publish to.
        text: Post content/body text.
        scheduled_send_time: When to publish (ISO 8601). Leave empty for draft.
        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        cid = _cid(customer_id)
        body = {
            "post_type": "OUTBOUND",
            "profile_ids": _split(profile_ids),
            "fields": {"text": text},
        }
        if scheduled_send_time:
            body["scheduled_send_time"] = scheduled_send_time
        r = httpx.post(f"{BASE_URL}/v1/{cid}/publishing/posts", headers=_headers(), json=body, timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# Tool 14: get_publishing_post
# ---------------------------------------------------------------------------
@mcp.tool()
def get_publishing_post(
    post_id: str,
    customer_id: str = "",
) -> str:
    """Retrieve a specific publishing post by ID.

    Args:
        post_id: The publishing post ID.
        customer_id: Sprout customer ID. Defaults to SPROUT_CUSTOMER_ID env var.
    """
    try:
        cid = _cid(customer_id)
        r = httpx.get(f"{BASE_URL}/v1/{cid}/publishing/posts/{post_id}", headers=_headers(), timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# ---------------------------------------------------------------------------
# ASGI app for uvicorn (Streamable HTTP transport)
# ---------------------------------------------------------------------------
app = mcp.streamable_http_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Sprout Social MCP server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
