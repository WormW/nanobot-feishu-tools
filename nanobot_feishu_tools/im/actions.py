"""Feishu IM actions — chat and message read operations."""

from __future__ import annotations

import json
from typing import Any

import lark_oapi as lark

from nanobot_feishu_tools._api import check_response, run_sync


async def list_chats(
    client: lark.Client,
    page_size: int = 20,
    page_token: str = "",
) -> dict:
    """List chats the bot has joined."""
    from lark_oapi.api.im.v1 import ListChatRequest

    builder = ListChatRequest.builder().page_size(page_size)
    if page_token:
        builder = builder.page_token(page_token)
    req = builder.build()

    resp = await run_sync(client.im.v1.chat.list, req)
    check_response(resp, "im.v1.chat.list")

    data = resp.data
    items = data.items or [] if data else []
    return {
        "has_more": getattr(data, "has_more", False),
        "page_token": getattr(data, "page_token", None),
        "chats": [
            {
                "chat_id": getattr(c, "chat_id", None),
                "name": getattr(c, "name", None),
                "description": getattr(c, "description", None),
                "owner_id": getattr(c, "owner_id", None),
                "chat_mode": getattr(c, "chat_mode", None),
            }
            for c in items
        ],
    }


async def get_chat(client: lark.Client, chat_id: str) -> dict:
    """Get chat details by chat_id."""
    from lark_oapi.api.im.v1 import GetChatRequest

    req = GetChatRequest.builder().chat_id(chat_id).build()
    resp = await run_sync(client.im.v1.chat.get, req)
    check_response(resp, "im.v1.chat.get")

    d = resp.data
    return {
        "chat_id": getattr(d, "chat_id", None),
        "name": getattr(d, "name", None),
        "description": getattr(d, "description", None),
        "owner_id": getattr(d, "owner_id", None),
        "chat_mode": getattr(d, "chat_mode", None),
        "member_count": getattr(d, "user_count", None),
    }


def _parse_message_content(msg: Any) -> str | None:
    """Try to extract readable text from message body content JSON."""
    body = getattr(msg, "body", None)
    if not body:
        return None
    content_str = getattr(body, "content", None)
    if not content_str:
        return None
    try:
        parsed = json.loads(content_str)
        if isinstance(parsed, dict):
            return parsed.get("text", content_str)
        return content_str
    except (json.JSONDecodeError, TypeError):
        return content_str


async def list_messages(
    client: lark.Client,
    chat_id: str,
    start_time: str = "",
    end_time: str = "",
    sort_type: str = "",
    page_size: int = 20,
    page_token: str = "",
) -> dict:
    """List messages in a chat container."""
    from lark_oapi.api.im.v1 import ListMessageRequest

    builder = (
        ListMessageRequest.builder()
        .container_id_type("chat")
        .container_id(chat_id)
        .page_size(page_size)
    )
    if start_time:
        builder = builder.start_time(start_time)
    if end_time:
        builder = builder.end_time(end_time)
    if sort_type:
        builder = builder.sort_type(sort_type)
    if page_token:
        builder = builder.page_token(page_token)
    req = builder.build()

    resp = await run_sync(client.im.v1.message.list, req)
    check_response(resp, "im.v1.message.list")

    data = resp.data
    items = data.items or [] if data else []
    messages = []
    for m in items:
        sender = getattr(m, "sender", None)
        messages.append({
            "message_id": getattr(m, "message_id", None),
            "msg_type": getattr(m, "msg_type", None),
            "create_time": getattr(m, "create_time", None),
            "update_time": getattr(m, "update_time", None),
            "sender_id": getattr(sender, "id", None) if sender else None,
            "sender_type": getattr(sender, "sender_type", None) if sender else None,
            "content": _parse_message_content(m),
        })
    return {
        "has_more": getattr(data, "has_more", False),
        "page_token": getattr(data, "page_token", None),
        "messages": messages,
    }


async def get_message(client: lark.Client, message_id: str) -> dict:
    """Get a single message by message_id."""
    from lark_oapi.api.im.v1 import GetMessageRequest

    req = GetMessageRequest.builder().message_id(message_id).build()
    resp = await run_sync(client.im.v1.message.get, req)
    check_response(resp, "im.v1.message.get")

    data = resp.data
    items = data.items or [] if data else []
    if not items:
        return {"message": None}
    m = items[0]
    sender = getattr(m, "sender", None)
    return {
        "message": {
            "message_id": getattr(m, "message_id", None),
            "msg_type": getattr(m, "msg_type", None),
            "create_time": getattr(m, "create_time", None),
            "update_time": getattr(m, "update_time", None),
            "sender_id": getattr(sender, "id", None) if sender else None,
            "sender_type": getattr(sender, "sender_type", None) if sender else None,
            "content": _parse_message_content(m),
            "chat_id": getattr(m, "chat_id", None),
        },
    }


