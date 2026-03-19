"""Bitable URL parsing and metadata resolution."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse, parse_qs

import lark_oapi as lark

from nanobot_feishu_tools._api import check_response, run_sync


def parse_bitable_url(url: str) -> dict[str, Any] | None:
    """Parse a bitable URL to extract token and table_id."""
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        table_id = qs.get("table", [None])[0]

        wiki_match = re.search(r"/wiki/([A-Za-z0-9]+)", parsed.path)
        if wiki_match:
            return {"token": wiki_match.group(1), "table_id": table_id, "is_wiki": True}

        base_match = re.search(r"/base/([A-Za-z0-9]+)", parsed.path)
        if base_match:
            return {"token": base_match.group(1), "table_id": table_id, "is_wiki": False}

        return None
    except Exception:
        return None


async def get_app_token_from_wiki(client: lark.Client, node_token: str) -> str:
    """Resolve wiki node token to bitable app_token."""
    from lark_oapi.api.wiki.v2 import GetNodeSpaceRequest

    req = GetNodeSpaceRequest.builder().token(node_token).build()
    resp = await run_sync(client.wiki.v2.space.get_node, req)
    check_response(resp, "wiki.v2.space.get_node")

    node = resp.data.node if resp.data else None
    if not node:
        raise ValueError("Node not found")
    if node.obj_type != "bitable":
        raise ValueError(f"Node is not a bitable (type: {node.obj_type})")

    return node.obj_token


async def get_bitable_meta(client: lark.Client, url: str) -> dict:
    """Parse bitable URL and get metadata."""
    parsed = parse_bitable_url(url)
    if not parsed:
        raise ValueError("Invalid URL format. Expected /base/XXX or /wiki/XXX URL")

    if parsed["is_wiki"]:
        app_token = await get_app_token_from_wiki(client, parsed["token"])
    else:
        app_token = parsed["token"]

    table_id = parsed["table_id"]

    # Get app info
    from lark_oapi.api.bitable.v1 import GetAppRequest

    app_req = GetAppRequest.builder().app_token(app_token).build()
    app_resp = await run_sync(client.bitable.v1.app.get, app_req)
    check_response(app_resp, "bitable.v1.app.get")

    result: dict[str, Any] = {
        "app_token": app_token,
        "table_id": table_id,
        "name": app_resp.data.app.name if app_resp.data and app_resp.data.app else None,
        "url_type": "wiki" if parsed["is_wiki"] else "base",
    }

    # If no table specified, list available tables
    if not table_id:
        from lark_oapi.api.bitable.v1 import ListAppTableRequest

        tables_req = ListAppTableRequest.builder().app_token(app_token).build()
        tables_resp = await run_sync(client.bitable.v1.app_table.list, tables_req)
        check_response(tables_resp, "bitable.v1.app_table.list")

        items = tables_resp.data.items or [] if tables_resp.data else []
        tables = [{"table_id": t.table_id, "name": t.name} for t in items]
        if tables:
            result["tables"] = tables

    result["hint"] = (
        f'Use app_token="{app_token}" and table_id="{table_id}" for other bitable tools'
        if table_id else
        f'Use app_token="{app_token}" for other bitable tools. Select a table_id from the tables list.'
    )

    return result
