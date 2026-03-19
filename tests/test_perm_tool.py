"""Tests for FeishuPermTool — action dispatch and parameter validation."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from nanobot_feishu_tools.perm.tool import FeishuPermTool


@pytest.fixture
def perm_tool(mock_client):
    return FeishuPermTool(mock_client)


class TestPermToolMetadata:
    def test_name(self, perm_tool):
        assert perm_tool.name == "feishu_perm"

    def test_description_mentions_permissions(self, perm_tool):
        desc = perm_tool.description
        assert "permission" in desc.lower()

    def test_parameters_has_action_enum(self, perm_tool):
        params = perm_tool.parameters
        assert params["properties"]["action"]["type"] == "string"
        assert set(params["properties"]["action"]["enum"]) == {"list", "add", "remove"}
        assert "action" in params["required"]
        assert "token" in params["required"]
        assert "type" in params["required"]

    def test_to_schema(self, perm_tool):
        schema = perm_tool.to_schema()
        assert schema["function"]["name"] == "feishu_perm"
        assert "parameters" in schema["function"]


class TestPermToolDispatch:
    @pytest.mark.asyncio
    async def test_list_dispatches(self, perm_tool):
        with patch("nanobot_feishu_tools.perm.actions.list_members", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = {"members": []}
            result = await perm_tool.execute(action="list", token="doxcn123", type="docx")
            mock_list.assert_awaited_once_with(perm_tool._client, "doxcn123", "docx")
            data = json.loads(result)
            assert data["members"] == []

    @pytest.mark.asyncio
    async def test_add_dispatches(self, perm_tool):
        with patch("nanobot_feishu_tools.perm.actions.add_member", new_callable=AsyncMock) as mock_add:
            mock_add.return_value = {"success": True, "member": None}
            result = await perm_tool.execute(
                action="add", token="doxcn123", type="docx",
                member_type="email", member_id="alice@example.com", perm="edit",
            )
            mock_add.assert_awaited_once_with(
                perm_tool._client, "doxcn123", "docx", "email", "alice@example.com", "edit",
            )
            data = json.loads(result)
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_remove_dispatches(self, perm_tool):
        with patch("nanobot_feishu_tools.perm.actions.remove_member", new_callable=AsyncMock) as mock_rm:
            mock_rm.return_value = {"success": True}
            result = await perm_tool.execute(
                action="remove", token="doxcn123", type="docx",
                member_type="email", member_id="alice@example.com",
            )
            mock_rm.assert_awaited_once_with(
                perm_tool._client, "doxcn123", "docx", "email", "alice@example.com",
            )
            data = json.loads(result)
            assert data["success"] is True


class TestPermToolValidation:
    @pytest.mark.asyncio
    async def test_unknown_action_returns_error(self, perm_tool):
        result = await perm_tool.execute(action="unknown", token="t", type="docx")
        assert "Error" in result
        assert "Unknown action" in result

    @pytest.mark.asyncio
    async def test_list_requires_token(self, perm_tool):
        result = await perm_tool.execute(action="list", token="", type="docx")
        assert "Error" in result
        assert "token" in result

    @pytest.mark.asyncio
    async def test_list_requires_type(self, perm_tool):
        result = await perm_tool.execute(action="list", token="doxcn123", type="")
        assert "Error" in result
        assert "type" in result

    @pytest.mark.asyncio
    async def test_add_requires_member_type(self, perm_tool):
        result = await perm_tool.execute(
            action="add", token="doxcn123", type="docx",
            member_type="", member_id="alice@example.com", perm="edit",
        )
        assert "Error" in result
        assert "member_type" in result

    @pytest.mark.asyncio
    async def test_add_requires_member_id(self, perm_tool):
        result = await perm_tool.execute(
            action="add", token="doxcn123", type="docx",
            member_type="email", member_id="", perm="edit",
        )
        assert "Error" in result
        assert "member_id" in result

    @pytest.mark.asyncio
    async def test_add_requires_perm(self, perm_tool):
        result = await perm_tool.execute(
            action="add", token="doxcn123", type="docx",
            member_type="email", member_id="alice@example.com", perm="",
        )
        assert "Error" in result
        assert "perm" in result

    @pytest.mark.asyncio
    async def test_remove_requires_member_type(self, perm_tool):
        result = await perm_tool.execute(
            action="remove", token="doxcn123", type="docx",
            member_type="", member_id="alice@example.com",
        )
        assert "Error" in result
        assert "member_type" in result

    @pytest.mark.asyncio
    async def test_remove_requires_member_id(self, perm_tool):
        result = await perm_tool.execute(
            action="remove", token="doxcn123", type="docx",
            member_type="email", member_id="",
        )
        assert "Error" in result
        assert "member_id" in result
