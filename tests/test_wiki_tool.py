"""Tests for FeishuWikiTool — action dispatch and parameter validation."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from nanobot_feishu_tools.wiki.tool import FeishuWikiTool


@pytest.fixture
def wiki_tool(mock_client):
    return FeishuWikiTool(mock_client)


class TestWikiToolMetadata:
    def test_name(self, wiki_tool):
        assert wiki_tool.name == "feishu_wiki"

    def test_description_contains_actions(self, wiki_tool):
        desc = wiki_tool.description
        for action in ["spaces", "nodes", "get", "create", "move", "rename"]:
            assert action in desc

    def test_parameters_has_action_enum(self, wiki_tool):
        params = wiki_tool.parameters
        assert "spaces" in params["properties"]["action"]["enum"]
        assert params["required"] == ["action"]


class TestWikiToolDispatch:
    @pytest.mark.asyncio
    async def test_spaces_dispatches(self, wiki_tool):
        with patch("nanobot_feishu_tools.wiki.actions.action_spaces", new_callable=AsyncMock) as mock:
            mock.return_value = {"spaces": []}
            result = await wiki_tool.execute(action="spaces")
            mock.assert_awaited_once_with(wiki_tool._client)
            data = json.loads(result)
            assert "spaces" in data

    @pytest.mark.asyncio
    async def test_nodes_dispatches(self, wiki_tool):
        with patch("nanobot_feishu_tools.wiki.actions.action_nodes", new_callable=AsyncMock) as mock:
            mock.return_value = {"nodes": []}
            result = await wiki_tool.execute(action="nodes", space_id="sp123")
            mock.assert_awaited_once_with(wiki_tool._client, "sp123", None)

    @pytest.mark.asyncio
    async def test_get_dispatches(self, wiki_tool):
        with patch("nanobot_feishu_tools.wiki.actions.action_get", new_callable=AsyncMock) as mock:
            mock.return_value = {"node": {"title": "Test"}}
            result = await wiki_tool.execute(action="get", token="wiki_abc")
            mock.assert_awaited_once_with(wiki_tool._client, "wiki_abc")

    @pytest.mark.asyncio
    async def test_create_dispatches(self, wiki_tool):
        with patch("nanobot_feishu_tools.wiki.actions.action_create", new_callable=AsyncMock) as mock:
            mock.return_value = {"node_token": "new_node"}
            await wiki_tool.execute(action="create", space_id="sp123", title="New Page")
            mock.assert_awaited_once_with(wiki_tool._client, "sp123", "New Page", "docx", None)

    @pytest.mark.asyncio
    async def test_move_dispatches(self, wiki_tool):
        with patch("nanobot_feishu_tools.wiki.actions.action_move", new_callable=AsyncMock) as mock:
            mock.return_value = {"success": True}
            await wiki_tool.execute(action="move", space_id="sp1", node_token="nt1")
            mock.assert_awaited_once_with(wiki_tool._client, "sp1", "nt1", None, None)

    @pytest.mark.asyncio
    async def test_rename_dispatches(self, wiki_tool):
        with patch("nanobot_feishu_tools.wiki.actions.action_rename", new_callable=AsyncMock) as mock:
            mock.return_value = {"success": True}
            await wiki_tool.execute(action="rename", space_id="sp1", node_token="nt1", title="Renamed")
            mock.assert_awaited_once_with(wiki_tool._client, "sp1", "nt1", "Renamed")


class TestWikiToolValidation:
    @pytest.mark.asyncio
    async def test_nodes_requires_space_id(self, wiki_tool):
        result = await wiki_tool.execute(action="nodes")
        assert "Error" in result
        assert "space_id" in result

    @pytest.mark.asyncio
    async def test_get_requires_token(self, wiki_tool):
        result = await wiki_tool.execute(action="get")
        assert "Error" in result
        assert "token" in result

    @pytest.mark.asyncio
    async def test_create_requires_space_id_and_title(self, wiki_tool):
        result = await wiki_tool.execute(action="create")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_rename_requires_title(self, wiki_tool):
        result = await wiki_tool.execute(action="rename", space_id="sp1", node_token="nt1")
        assert "Error" in result
        assert "title" in result

    @pytest.mark.asyncio
    async def test_unknown_action_returns_error(self, wiki_tool):
        result = await wiki_tool.execute(action="nope")
        assert "Error" in result
        assert "Unknown action" in result
