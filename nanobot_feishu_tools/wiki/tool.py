"""Feishu Wiki Tool — single tool with action-based dispatch."""

from __future__ import annotations

from typing import Any

import lark_oapi as lark

from nanobot.agent.tools.base import Tool
from nanobot_feishu_tools._api import to_json
from nanobot_feishu_tools.wiki import actions


class FeishuWikiTool(Tool):
    """Feishu wiki knowledge space operations via action dispatch."""

    def __init__(self, client: lark.Client):
        self._client = client

    @property
    def name(self) -> str:
        return "feishu_wiki"

    @property
    def description(self) -> str:
        return (
            "Feishu wiki knowledge space operations. "
            "Actions: spaces, nodes, get, create, move, rename."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["spaces", "nodes", "get", "create", "move", "rename"],
                    "description": "Wiki action",
                },
                "space_id": {
                    "type": "string",
                    "description": "Knowledge space ID",
                },
                "parent_node_token": {
                    "type": "string",
                    "description": "Parent node token (optional, omit for root)",
                },
                "token": {
                    "type": "string",
                    "description": "Wiki node token (from URL /wiki/XXX)",
                },
                "title": {
                    "type": "string",
                    "description": "Node title / new title",
                },
                "obj_type": {
                    "type": "string",
                    "enum": ["docx", "sheet", "bitable"],
                    "description": "Object type for create action (default: docx)",
                },
                "node_token": {
                    "type": "string",
                    "description": "Node token",
                },
                "target_space_id": {
                    "type": "string",
                    "description": "Target space ID (optional, same space if omitted)",
                },
                "target_parent_token": {
                    "type": "string",
                    "description": "Target parent node token (optional, root if omitted)",
                },
            },
            "required": ["action"],
        }

    async def execute(
        self,
        action: str,
        space_id: str = "",
        parent_node_token: str = "",
        token: str = "",
        title: str = "",
        obj_type: str = "docx",
        node_token: str = "",
        target_space_id: str = "",
        target_parent_token: str = "",
        **kwargs: Any,
    ) -> str:
        def _req(val: str, field: str) -> str:
            if not val or not val.strip():
                raise ValueError(f"{field} is required for action '{action}'")
            return val

        try:
            if action == "spaces":
                result = await actions.action_spaces(self._client)
            elif action == "nodes":
                result = await actions.action_nodes(
                    self._client, _req(space_id, "space_id"),
                    parent_node_token or None,
                )
            elif action == "get":
                result = await actions.action_get(self._client, _req(token, "token"))
            elif action == "create":
                result = await actions.action_create(
                    self._client, _req(space_id, "space_id"), _req(title, "title"),
                    obj_type, parent_node_token or None,
                )
            elif action == "move":
                result = await actions.action_move(
                    self._client, _req(space_id, "space_id"), _req(node_token, "node_token"),
                    target_space_id or None, target_parent_token or None,
                )
            elif action == "rename":
                result = await actions.action_rename(
                    self._client, _req(space_id, "space_id"),
                    _req(node_token, "node_token"), _req(title, "title"),
                )
            else:
                return f"Error: Unknown action '{action}'"

            return to_json(result)
        except Exception as e:
            return f"Error: {e}"
