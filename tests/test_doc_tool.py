"""Tests for FeishuDocTool — action dispatch and parameter validation."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from nanobot_feishu_tools.doc.tool import FeishuDocTool


@pytest.fixture
def doc_tool(mock_client):
    return FeishuDocTool(mock_client)


class TestDocToolMetadata:
    def test_name(self, doc_tool):
        assert doc_tool.name == "feishu_doc"

    def test_description_contains_actions(self, doc_tool):
        desc = doc_tool.description
        for action in ["read", "write", "append", "create", "create_and_write",
                        "list_blocks", "get_block", "update_block", "delete_block",
                        "list_comments", "create_comment", "get_comment", "list_comment_replies"]:
            assert action in desc

    def test_parameters_has_action_enum(self, doc_tool):
        params = doc_tool.parameters
        assert params["properties"]["action"]["type"] == "string"
        assert "read" in params["properties"]["action"]["enum"]
        assert params["required"] == ["action"]

    def test_to_schema(self, doc_tool):
        schema = doc_tool.to_schema()
        assert schema["function"]["name"] == "feishu_doc"
        assert "parameters" in schema["function"]


class TestDocToolDispatch:
    @pytest.mark.asyncio
    async def test_read_dispatches(self, doc_tool):
        with patch("nanobot_feishu_tools.doc.actions.action_read", new_callable=AsyncMock) as mock_read:
            mock_read.return_value = {"content": "hello"}
            result = await doc_tool.execute(action="read", doc_token="doc123")
            mock_read.assert_awaited_once_with(doc_tool._client, "doc123")
            data = json.loads(result)
            assert data["content"] == "hello"

    @pytest.mark.asyncio
    async def test_write_dispatches(self, doc_tool):
        with patch("nanobot_feishu_tools.doc.actions.action_write", new_callable=AsyncMock) as mock_write:
            mock_write.return_value = {"success": True}
            result = await doc_tool.execute(action="write", doc_token="doc123", content="# Hello")
            mock_write.assert_awaited_once_with(doc_tool._client, "doc123", "# Hello")

    @pytest.mark.asyncio
    async def test_create_dispatches(self, doc_tool):
        with patch("nanobot_feishu_tools.doc.actions.action_create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"document_id": "new_id"}
            result = await doc_tool.execute(action="create", title="My Doc")
            mock_create.assert_awaited_once_with(doc_tool._client, "My Doc", None)

    @pytest.mark.asyncio
    async def test_create_and_write_dispatches(self, doc_tool):
        with patch("nanobot_feishu_tools.doc.actions.action_create_and_write", new_callable=AsyncMock) as mock:
            mock.return_value = {"document_id": "new_id"}
            result = await doc_tool.execute(
                action="create_and_write", title="My Doc", content="# Content", folder_token="fld123",
            )
            mock.assert_awaited_once_with(doc_tool._client, "My Doc", "# Content", "fld123")

    @pytest.mark.asyncio
    async def test_list_blocks_dispatches(self, doc_tool):
        with patch("nanobot_feishu_tools.doc.actions.action_list_blocks", new_callable=AsyncMock) as mock:
            mock.return_value = {"blocks": []}
            await doc_tool.execute(action="list_blocks", doc_token="doc123")
            mock.assert_awaited_once_with(doc_tool._client, "doc123")


class TestDocToolValidation:
    @pytest.mark.asyncio
    async def test_read_requires_doc_token(self, doc_tool):
        result = await doc_tool.execute(action="read")
        assert "Error" in result
        assert "doc_token" in result

    @pytest.mark.asyncio
    async def test_write_requires_content(self, doc_tool):
        result = await doc_tool.execute(action="write", doc_token="doc123")
        assert "Error" in result
        assert "content" in result

    @pytest.mark.asyncio
    async def test_create_requires_title(self, doc_tool):
        result = await doc_tool.execute(action="create")
        assert "Error" in result
        assert "title" in result

    @pytest.mark.asyncio
    async def test_unknown_action_returns_error(self, doc_tool):
        result = await doc_tool.execute(action="unknown_action")
        assert "Error" in result
        assert "Unknown action" in result

    @pytest.mark.asyncio
    async def test_get_block_requires_block_id(self, doc_tool):
        result = await doc_tool.execute(action="get_block", doc_token="doc123")
        assert "Error" in result
        assert "block_id" in result

    @pytest.mark.asyncio
    async def test_list_comments_requires_doc_token(self, doc_tool):
        result = await doc_tool.execute(action="list_comments")
        assert "Error" in result
        assert "doc_token" in result
