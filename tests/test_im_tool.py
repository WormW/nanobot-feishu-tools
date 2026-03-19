"""Tests for FeishuImTool — action dispatch and parameter validation."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from nanobot_feishu_tools.im.tool import FeishuImTool


@pytest.fixture
def im_tool(mock_client):
    return FeishuImTool(mock_client)


class TestImToolMetadata:
    def test_name(self, im_tool):
        assert im_tool.name == "feishu_im"

    def test_description_mentions_im(self, im_tool):
        desc = im_tool.description
        assert "chat" in desc.lower() or "im" in desc.lower()

    def test_parameters_has_action_enum(self, im_tool):
        params = im_tool.parameters
        assert params["properties"]["action"]["type"] == "string"
        assert set(params["properties"]["action"]["enum"]) == {
            "list_chats", "get_chat", "list_messages", "get_message",
        }
        assert params["required"] == ["action"]

    def test_parameters_has_chat_id(self, im_tool):
        params = im_tool.parameters
        assert "chat_id" in params["properties"]

    def test_parameters_has_message_id(self, im_tool):
        params = im_tool.parameters
        assert "message_id" in params["properties"]

    def test_to_schema(self, im_tool):
        schema = im_tool.to_schema()
        assert schema["function"]["name"] == "feishu_im"
        assert "parameters" in schema["function"]


class TestImToolDispatch:
    @pytest.mark.asyncio
    async def test_list_chats_dispatches(self, im_tool):
        with patch("nanobot_feishu_tools.im.actions.list_chats", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"chats": [], "has_more": False, "page_token": None}
            result = await im_tool.execute(action="list_chats")
            mock_fn.assert_awaited_once_with(im_tool._client, page_size=20, page_token="")
            data = json.loads(result)
            assert data["chats"] == []

    @pytest.mark.asyncio
    async def test_get_chat_dispatches(self, im_tool):
        with patch("nanobot_feishu_tools.im.actions.get_chat", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"chat_id": "oc_123", "name": "Test"}
            result = await im_tool.execute(action="get_chat", chat_id="oc_123")
            mock_fn.assert_awaited_once_with(im_tool._client, "oc_123")
            data = json.loads(result)
            assert data["chat_id"] == "oc_123"

    @pytest.mark.asyncio
    async def test_list_messages_dispatches(self, im_tool):
        with patch("nanobot_feishu_tools.im.actions.list_messages", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"messages": [], "has_more": False, "page_token": None}
            result = await im_tool.execute(
                action="list_messages", chat_id="oc_123",
                start_time="1700000000", end_time="1700086400",
                sort_type="ByCreateTimeDesc", page_size="30",
            )
            mock_fn.assert_awaited_once_with(
                im_tool._client, "oc_123",
                start_time="1700000000", end_time="1700086400",
                sort_type="ByCreateTimeDesc", page_size=30, page_token="",
            )
            data = json.loads(result)
            assert data["messages"] == []

    @pytest.mark.asyncio
    async def test_get_message_dispatches(self, im_tool):
        with patch("nanobot_feishu_tools.im.actions.get_message", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"message": {"message_id": "om_abc"}}
            result = await im_tool.execute(action="get_message", message_id="om_abc")
            mock_fn.assert_awaited_once_with(im_tool._client, "om_abc")
            data = json.loads(result)
            assert data["message"]["message_id"] == "om_abc"



class TestImToolValidation:
    @pytest.mark.asyncio
    async def test_unknown_action_returns_error(self, im_tool):
        result = await im_tool.execute(action="unknown")
        assert "Error" in result
        assert "Unknown action" in result

    @pytest.mark.asyncio
    async def test_get_chat_requires_chat_id(self, im_tool):
        result = await im_tool.execute(action="get_chat", chat_id="")
        assert "Error" in result
        assert "chat_id" in result

    @pytest.mark.asyncio
    async def test_list_messages_requires_chat_id(self, im_tool):
        result = await im_tool.execute(action="list_messages", chat_id="")
        assert "Error" in result
        assert "chat_id" in result

    @pytest.mark.asyncio
    async def test_get_message_requires_message_id(self, im_tool):
        result = await im_tool.execute(action="get_message", message_id="")
        assert "Error" in result
        assert "message_id" in result
