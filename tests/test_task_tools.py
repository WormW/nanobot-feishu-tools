"""Tests for task tools — metadata, factory, and dispatch."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from nanobot_feishu_tools.task.tools import (
    FeishuTaskCreate,
    FeishuTaskGet,
    FeishuTaskDelete,
    FeishuTasklistCreate,
    FeishuTasklistList,
    FeishuTaskCommentCreate,
    FeishuTaskCommentDelete,
    FeishuTaskAttachmentList,
    FeishuTaskAttachmentDelete,
    get_task_tools,
)


class TestTaskToolFactory:
    def test_tool_count(self, mock_client):
        tools = get_task_tools(mock_client)
        assert len(tools) == 21

    def test_unique_names(self, mock_client):
        tools = get_task_tools(mock_client)
        names = [t.name for t in tools]
        assert len(names) == len(set(names)), f"Duplicate names: {[n for n in names if names.count(n) > 1]}"

    def test_all_tools_have_descriptions(self, mock_client):
        for tool in get_task_tools(mock_client):
            assert tool.description, f"{tool.name} has empty description"
            assert len(tool.description) > 5

    def test_all_tools_have_parameters(self, mock_client):
        for tool in get_task_tools(mock_client):
            params = tool.parameters
            assert params["type"] == "object"
            assert "properties" in params


class TestTaskToolMetadata:
    def test_task_create_requires_summary(self, mock_client):
        tool = FeishuTaskCreate(mock_client)
        assert tool.name == "feishu_task_create"
        assert "summary" in tool.parameters["required"]

    def test_task_get_requires_task_guid(self, mock_client):
        tool = FeishuTaskGet(mock_client)
        assert "task_guid" in tool.parameters["required"]

    def test_task_delete_requires_task_guid(self, mock_client):
        tool = FeishuTaskDelete(mock_client)
        assert "task_guid" in tool.parameters["required"]

    def test_tasklist_create_requires_name(self, mock_client):
        tool = FeishuTasklistCreate(mock_client)
        assert "name" in tool.parameters["required"]

    def test_comment_create_requires_task_guid_and_content(self, mock_client):
        tool = FeishuTaskCommentCreate(mock_client)
        required = set(tool.parameters["required"])
        assert "task_guid" in required
        assert "content" in required

    def test_comment_delete_requires_comment_id(self, mock_client):
        tool = FeishuTaskCommentDelete(mock_client)
        assert "comment_id" in tool.parameters["required"]

    def test_attachment_list_requires_task_guid(self, mock_client):
        tool = FeishuTaskAttachmentList(mock_client)
        assert "task_guid" in tool.parameters["required"]

    def test_attachment_delete_requires_attachment_guid(self, mock_client):
        tool = FeishuTaskAttachmentDelete(mock_client)
        assert "attachment_guid" in tool.parameters["required"]


class TestTaskToolDispatch:
    @pytest.mark.asyncio
    async def test_create_task_dispatches(self, mock_client):
        tool = FeishuTaskCreate(mock_client)
        with patch("nanobot_feishu_tools.task.actions.create_task", new_callable=AsyncMock) as mock:
            mock.return_value = {"task": {"guid": "t1"}}
            result = await tool.execute(summary="Test task")
            mock.assert_awaited_once()
            data = json.loads(result)
            assert data["task"]["guid"] == "t1"

    @pytest.mark.asyncio
    async def test_get_task_dispatches(self, mock_client):
        tool = FeishuTaskGet(mock_client)
        with patch("nanobot_feishu_tools.task.actions.get_task", new_callable=AsyncMock) as mock:
            mock.return_value = {"task": {"guid": "t1", "summary": "Test"}}
            result = await tool.execute(task_guid="t1")
            mock.assert_awaited_once_with(mock_client, "t1", None)

    @pytest.mark.asyncio
    async def test_delete_task_dispatches(self, mock_client):
        tool = FeishuTaskDelete(mock_client)
        with patch("nanobot_feishu_tools.task.actions.delete_task", new_callable=AsyncMock) as mock:
            mock.return_value = {"success": True}
            result = await tool.execute(task_guid="t1")
            mock.assert_awaited_once_with(mock_client, "t1")

    @pytest.mark.asyncio
    async def test_tasklist_list_dispatches(self, mock_client):
        tool = FeishuTasklistList(mock_client)
        with patch("nanobot_feishu_tools.task.actions.list_tasklists", new_callable=AsyncMock) as mock:
            mock.return_value = {"items": [], "has_more": False}
            result = await tool.execute()
            mock.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_comment_delete_dispatches(self, mock_client):
        tool = FeishuTaskCommentDelete(mock_client)
        with patch("nanobot_feishu_tools.task.actions.delete_task_comment", new_callable=AsyncMock) as mock:
            mock.return_value = {"success": True}
            result = await tool.execute(comment_id="c1")
            mock.assert_awaited_once_with(mock_client, "c1")

    @pytest.mark.asyncio
    async def test_attachment_delete_dispatches(self, mock_client):
        tool = FeishuTaskAttachmentDelete(mock_client)
        with patch("nanobot_feishu_tools.task.actions.delete_task_attachment", new_callable=AsyncMock) as mock:
            mock.return_value = {"success": True}
            result = await tool.execute(attachment_guid="a1")
            mock.assert_awaited_once_with(mock_client, "a1")

    @pytest.mark.asyncio
    async def test_error_returns_error_string(self, mock_client):
        tool = FeishuTaskCreate(mock_client)
        with patch("nanobot_feishu_tools.task.actions.create_task", new_callable=AsyncMock) as mock:
            mock.side_effect = RuntimeError("connection refused")
            result = await tool.execute(summary="Test")
            assert "Error" in result
            assert "connection refused" in result
