"""Feishu Document Tool — single tool with action-based dispatch."""

from __future__ import annotations

from typing import Any

import lark_oapi as lark

from nanobot.agent.tools.base import Tool
from nanobot_feishu_tools._api import to_json
from nanobot_feishu_tools.doc import actions


class FeishuDocTool(Tool):
    """Feishu document operations via action dispatch."""

    def __init__(self, client: lark.Client):
        self._client = client

    @property
    def name(self) -> str:
        return "feishu_doc"

    @property
    def description(self) -> str:
        return (
            "Feishu document operations. Actions: read, write, append, create, "
            "create_and_write, list_blocks, get_block, update_block, delete_block, "
            "list_comments, create_comment, get_comment, list_comment_replies. "
            'Use "create_and_write" for atomic create + content write.'
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "read", "write", "append", "create", "create_and_write",
                        "list_blocks", "get_block", "update_block", "delete_block",
                        "list_comments", "create_comment", "get_comment", "list_comment_replies",
                    ],
                    "description": "Document action",
                },
                "doc_token": {
                    "type": "string",
                    "description": "Document token (extract from URL /docx/XXX or /docs/XXX). Supports both new (docx) and legacy (doc) formats.",
                },
                "content": {
                    "type": "string",
                    "description": "Markdown content for write/append/comment/update operations",
                },
                "title": {
                    "type": "string",
                    "description": "Document title (for create/create_and_write)",
                },
                "folder_token": {
                    "type": "string",
                    "description": "Target folder token (optional)",
                },
                "block_id": {
                    "type": "string",
                    "description": "Block ID (from list_blocks)",
                },
                "comment_id": {
                    "type": "string",
                    "description": "Comment ID",
                },
                "page_token": {
                    "type": "string",
                    "description": "Page token for pagination",
                },
                "page_size": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Page size, default 50 (positive integer)",
                },
            },
            "required": ["action"],
        }

    async def execute(
        self,
        action: str,
        doc_token: str = "",
        content: str = "",
        title: str = "",
        folder_token: str = "",
        block_id: str = "",
        comment_id: str = "",
        page_token: str = "",
        page_size: int = 50,
        **kwargs: Any,
    ) -> str:
        def _req(val: str, field: str) -> str:
            if not val or not val.strip():
                raise ValueError(f"{field} is required for action '{action}'")
            return val

        try:
            if action == "read":
                result = await actions.action_read(self._client, _req(doc_token, "doc_token"))
            elif action == "write":
                result = await actions.action_write(
                    self._client, _req(doc_token, "doc_token"), _req(content, "content"),
                )
            elif action == "append":
                result = await actions.action_append(
                    self._client, _req(doc_token, "doc_token"), _req(content, "content"),
                )
            elif action == "create":
                result = await actions.action_create(
                    self._client, _req(title, "title"), folder_token or None,
                )
            elif action == "create_and_write":
                result = await actions.action_create_and_write(
                    self._client, _req(title, "title"), _req(content, "content"),
                    folder_token or None,
                )
            elif action == "list_blocks":
                result = await actions.action_list_blocks(self._client, _req(doc_token, "doc_token"))
            elif action == "get_block":
                result = await actions.action_get_block(
                    self._client, _req(doc_token, "doc_token"), _req(block_id, "block_id"),
                )
            elif action == "update_block":
                result = await actions.action_update_block(
                    self._client, _req(doc_token, "doc_token"),
                    _req(block_id, "block_id"), _req(content, "content"),
                )
            elif action == "delete_block":
                result = await actions.action_delete_block(
                    self._client, _req(doc_token, "doc_token"), _req(block_id, "block_id"),
                )
            elif action == "list_comments":
                result = await actions.action_list_comments(
                    self._client, _req(doc_token, "doc_token"), page_token or None, page_size,
                )
            elif action == "create_comment":
                result = await actions.action_create_comment(
                    self._client, _req(doc_token, "doc_token"), _req(content, "content"),
                )
            elif action == "get_comment":
                result = await actions.action_get_comment(
                    self._client, _req(doc_token, "doc_token"), _req(comment_id, "comment_id"),
                )
            elif action == "list_comment_replies":
                result = await actions.action_list_comment_replies(
                    self._client, _req(doc_token, "doc_token"), _req(comment_id, "comment_id"),
                    page_token or None, page_size,
                )
            else:
                return f"Error: Unknown action '{action}'"

            return to_json(result)
        except Exception as e:
            return f"Error: {e}"
