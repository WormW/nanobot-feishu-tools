"""Feishu wiki actions."""

from __future__ import annotations

from typing import Any

import lark_oapi as lark

from nanobot_feishu_tools._api import check_response, run_sync

WIKI_ACCESS_HINT = (
    "To grant wiki access: Open wiki space -> Settings -> Members -> Add the bot. "
    "See: https://open.feishu.cn/document/server-docs/docs/wiki-v2/wiki-qa#a40ad4ca"
)


def _require(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value


async def action_spaces(client: lark.Client) -> dict:
    from lark_oapi.api.wiki.v2 import ListSpaceRequest

    req = ListSpaceRequest.builder().build()
    resp = await run_sync(client.wiki.v2.space.list, req)
    check_response(resp, "wiki.v2.space.list")

    items = resp.data.items or [] if resp.data else []
    spaces = [
        {
            "space_id": s.space_id,
            "name": s.name,
            "description": s.description,
            "visibility": s.visibility,
        }
        for s in items
    ]

    result: dict[str, Any] = {"spaces": spaces}
    if not spaces:
        result["hint"] = WIKI_ACCESS_HINT
    return result


async def action_nodes(client: lark.Client, space_id: str, parent_node_token: str | None = None) -> dict:
    from lark_oapi.api.wiki.v2 import ListSpaceNodeRequest

    builder = ListSpaceNodeRequest.builder().space_id(space_id)
    if parent_node_token:
        builder = builder.parent_node_token(parent_node_token)

    resp = await run_sync(client.wiki.v2.space_node.list, builder.build())
    check_response(resp, "wiki.v2.space_node.list")

    items = resp.data.items or [] if resp.data else []
    return {
        "nodes": [
            {
                "node_token": n.node_token,
                "obj_token": n.obj_token,
                "obj_type": n.obj_type,
                "title": n.title,
                "has_child": n.has_child,
            }
            for n in items
        ],
    }


async def action_get(client: lark.Client, token: str) -> dict:
    from lark_oapi.api.wiki.v2 import GetNodeSpaceRequest

    req = GetNodeSpaceRequest.builder().token(token).build()
    resp = await run_sync(client.wiki.v2.space.get_node, req)
    check_response(resp, "wiki.v2.space.get_node")

    node = resp.data.node if resp.data else None
    if not node:
        return {"error": "Node not found"}

    return {
        "node_token": node.node_token,
        "space_id": node.space_id,
        "obj_token": node.obj_token,
        "obj_type": node.obj_type,
        "title": node.title,
        "parent_node_token": node.parent_node_token,
        "has_child": node.has_child,
        "creator": node.creator,
        "create_time": node.node_create_time,
    }


async def action_create(
    client: lark.Client, space_id: str, title: str,
    obj_type: str = "docx", parent_node_token: str | None = None,
) -> dict:
    from lark_oapi.api.wiki.v2 import CreateSpaceNodeRequest, Node

    node_builder = (
        Node.builder()
        .obj_type(obj_type)
        .node_type("origin")
        .title(title)
    )
    if parent_node_token:
        node_builder = node_builder.parent_node_token(parent_node_token)

    req = (
        CreateSpaceNodeRequest.builder()
        .space_id(space_id)
        .request_body(node_builder.build())
        .build()
    )
    resp = await run_sync(client.wiki.v2.space_node.create, req)
    check_response(resp, "wiki.v2.space_node.create")

    node = resp.data.node if resp.data else None
    return {
        "node_token": node.node_token if node else None,
        "obj_token": node.obj_token if node else None,
        "obj_type": node.obj_type if node else None,
        "title": node.title if node else None,
    }


async def action_move(
    client: lark.Client, space_id: str, node_token: str,
    target_space_id: str | None = None, target_parent_token: str | None = None,
) -> dict:
    from lark_oapi.api.wiki.v2 import MoveSpaceNodeRequest, MoveSpaceNodeRequestBody

    body_builder = MoveSpaceNodeRequestBody.builder().target_space_id(target_space_id or space_id)
    if target_parent_token:
        body_builder = body_builder.target_parent_token(target_parent_token)

    req = (
        MoveSpaceNodeRequest.builder()
        .space_id(space_id)
        .node_token(node_token)
        .request_body(body_builder.build())
        .build()
    )
    resp = await run_sync(client.wiki.v2.space_node.move, req)
    check_response(resp, "wiki.v2.space_node.move")

    node = resp.data.node if resp.data else None
    return {"success": True, "node_token": node.node_token if node else node_token}


async def action_rename(client: lark.Client, space_id: str, node_token: str, title: str) -> dict:
    from lark_oapi.api.wiki.v2 import UpdateTitleSpaceNodeRequest, UpdateTitleSpaceNodeRequestBody

    body = UpdateTitleSpaceNodeRequestBody.builder().title(title).build()
    req = (
        UpdateTitleSpaceNodeRequest.builder()
        .space_id(space_id)
        .node_token(node_token)
        .request_body(body)
        .build()
    )
    resp = await run_sync(client.wiki.v2.space_node.update_title, req)
    check_response(resp, "wiki.v2.space_node.update_title")

    return {"success": True, "node_token": node_token, "title": title}
