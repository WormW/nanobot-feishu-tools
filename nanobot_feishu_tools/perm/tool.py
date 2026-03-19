"""Feishu Permission Tool — single tool with action-based dispatch."""

from __future__ import annotations

from typing import Any

import lark_oapi as lark

from nanobot.agent.tools.base import Tool
from nanobot_feishu_tools._api import to_json
from nanobot_feishu_tools.perm import actions


_TOKEN_TYPES = ["doc", "docx", "sheet", "bitable", "folder", "file", "wiki", "mindnote"]
_MEMBER_TYPES = ["email", "openid", "userid", "unionid", "openchat", "opendepartmentid"]
_PERM_LEVELS = ["view", "edit", "full_access"]


class FeishuPermTool(Tool):
    """Feishu file/document permission management via action dispatch."""

    def __init__(self, client: lark.Client):
        self._client = client

    @property
    def name(self) -> str:
        return "feishu_perm"

    @property
    def description(self) -> str:
        return (
            "Manage Feishu file/document permissions (collaborators). "
            "Actions: list (list collaborators), add (add collaborator), remove (remove collaborator). "
            "Works with docx, sheet, bitable, folder, wiki, and other file types."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "add", "remove"],
                    "description": "Permission action",
                },
                "token": {
                    "type": "string",
                    "description": "File/document token",
                },
                "type": {
                    "type": "string",
                    "enum": _TOKEN_TYPES,
                    "description": "File token type (docx, sheet, bitable, folder, wiki, etc.)",
                },
                "member_type": {
                    "type": "string",
                    "enum": _MEMBER_TYPES,
                    "description": "Member ID type (email, openid, userid, unionid, openchat, opendepartmentid)",
                },
                "member_id": {
                    "type": "string",
                    "description": "Member ID value (e.g. email address, open_id)",
                },
                "perm": {
                    "type": "string",
                    "enum": _PERM_LEVELS,
                    "description": "Permission level: view, edit, or full_access",
                },
            },
            "required": ["action", "token", "type"],
        }

    async def execute(
        self,
        action: str,
        token: str = "",
        type: str = "",
        member_type: str = "",
        member_id: str = "",
        perm: str = "",
        **kwargs: Any,
    ) -> str:
        def _req(val: str, field: str) -> str:
            if not val or not val.strip():
                raise ValueError(f"{field} is required for action '{action}'")
            return val

        try:
            if action == "list":
                result = await actions.list_members(
                    self._client, _req(token, "token"), _req(type, "type"),
                )
            elif action == "add":
                result = await actions.add_member(
                    self._client,
                    _req(token, "token"),
                    _req(type, "type"),
                    _req(member_type, "member_type"),
                    _req(member_id, "member_id"),
                    _req(perm, "perm"),
                )
            elif action == "remove":
                result = await actions.remove_member(
                    self._client,
                    _req(token, "token"),
                    _req(type, "type"),
                    _req(member_type, "member_type"),
                    _req(member_id, "member_id"),
                )
            else:
                return f"Error: Unknown action '{action}'"

            return to_json(result)
        except Exception as e:
            return f"Error: {e}"
