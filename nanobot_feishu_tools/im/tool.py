"""Feishu IM Tool — chat history retrieval."""

from __future__ import annotations

from typing import Any

import lark_oapi as lark

from nanobot.agent.tools.base import Tool
from nanobot_feishu_tools._api import to_json
from nanobot_feishu_tools.im import actions


class FeishuImTool(Tool):
    """Feishu IM tool for reading chat history."""

    def __init__(self, client: lark.Client):
        self._client = client

    @property
    def name(self) -> str:
        return "feishu_im"

    @property
    def description(self) -> str:
        return (
            "Feishu/Lark IM read operations: list chats the bot joined, "
            "read chat message history, get message details. "
            "Actions: list_chats, get_chat, list_messages, get_message."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "list_chats",
                        "get_chat",
                        "list_messages",
                        "get_message",
                    ],
                    "description": "IM action to perform",
                },
                "chat_id": {
                    "type": "string",
                    "description": "Chat/group ID (oc_ prefix), required for get_chat and list_messages",
                },
                "message_id": {
                    "type": "string",
                    "description": "Message ID (om_ prefix), required for get_message",
                },
                "start_time": {
                    "type": "string",
                    "description": "Start time as Unix timestamp in seconds (optional, for list_messages)",
                },
                "end_time": {
                    "type": "string",
                    "description": "End time as Unix timestamp in seconds (optional, for list_messages)",
                },
                "sort_type": {
                    "type": "string",
                    "enum": ["ByCreateTimeAsc", "ByCreateTimeDesc"],
                    "description": "Sort order for list_messages (default: ByCreateTimeAsc)",
                },
                "page_size": {
                    "type": "string",
                    "description": "Page size (default 20, max 50)",
                },
                "page_token": {
                    "type": "string",
                    "description": "Pagination token from previous response",
                },
            },
            "required": ["action"],
        }

    async def execute(
        self,
        action: str,
        chat_id: str = "",
        message_id: str = "",
        start_time: str = "",
        end_time: str = "",
        sort_type: str = "",
        page_size: str = "",
        page_token: str = "",
        **kwargs: Any,
    ) -> str:
        def _req(val: str, field: str) -> str:
            if not val or not val.strip():
                raise ValueError(f"{field} is required for action '{action}'")
            return val

        ps = int(page_size) if page_size else 20

        try:
            if action == "list_chats":
                result = await actions.list_chats(
                    self._client,
                    page_size=ps,
                    page_token=page_token,
                )
            elif action == "get_chat":
                result = await actions.get_chat(
                    self._client, _req(chat_id, "chat_id"),
                )
            elif action == "list_messages":
                result = await actions.list_messages(
                    self._client,
                    _req(chat_id, "chat_id"),
                    start_time=start_time,
                    end_time=end_time,
                    sort_type=sort_type,
                    page_size=ps,
                    page_token=page_token,
                )
            elif action == "get_message":
                result = await actions.get_message(
                    self._client, _req(message_id, "message_id"),
                )
            else:
                return f"Error: Unknown action '{action}'"

            return to_json(result)
        except Exception as e:
            return f"Error: {e}"
