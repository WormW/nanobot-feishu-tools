"""Tests for bitable tools — URL parsing and tool metadata."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nanobot_feishu_tools.bitable.meta import parse_bitable_url
from nanobot_feishu_tools.bitable.tools import (
    FeishuBitableGetMeta,
    FeishuBitableListFields,
    FeishuBitableListRecords,
    FeishuBitableCreateRecord,
    FeishuBitableUpdateRecord,
    FeishuBitableDeleteRecord,
    FeishuBitableBatchDeleteRecords,
    get_bitable_tools,
)


# ---------------------------------------------------------------------------
# URL parsing tests
# ---------------------------------------------------------------------------

class TestParseBitableUrl:
    def test_base_url_with_table(self):
        url = "https://example.feishu.cn/base/ABC123?table=tblXYZ"
        result = parse_bitable_url(url)
        assert result is not None
        assert result["token"] == "ABC123"
        assert result["table_id"] == "tblXYZ"
        assert result["is_wiki"] is False

    def test_wiki_url_with_table(self):
        url = "https://example.feishu.cn/wiki/WikiToken123?table=tbl456"
        result = parse_bitable_url(url)
        assert result is not None
        assert result["token"] == "WikiToken123"
        assert result["table_id"] == "tbl456"
        assert result["is_wiki"] is True

    def test_base_url_without_table(self):
        url = "https://example.feishu.cn/base/ABC123"
        result = parse_bitable_url(url)
        assert result is not None
        assert result["token"] == "ABC123"
        assert result["table_id"] is None
        assert result["is_wiki"] is False

    def test_wiki_url_without_table(self):
        url = "https://example.feishu.cn/wiki/WikiToken123"
        result = parse_bitable_url(url)
        assert result is not None
        assert result["table_id"] is None
        assert result["is_wiki"] is True

    def test_invalid_url_returns_none(self):
        assert parse_bitable_url("https://example.com/other/path") is None

    def test_empty_url_returns_none(self):
        assert parse_bitable_url("") is None

    def test_malformed_url_returns_none(self):
        assert parse_bitable_url("not a url at all") is None

    def test_wiki_takes_priority_over_base(self):
        # Wiki pattern is checked first
        url = "https://example.feishu.cn/wiki/W123?table=tbl1"
        result = parse_bitable_url(url)
        assert result["is_wiki"] is True
        assert result["token"] == "W123"


# ---------------------------------------------------------------------------
# Tool metadata tests
# ---------------------------------------------------------------------------

class TestBitableToolMetadata:
    def test_tool_count(self, mock_client):
        tools = get_bitable_tools(mock_client)
        assert len(tools) == 11

    def test_unique_names(self, mock_client):
        tools = get_bitable_tools(mock_client)
        names = [t.name for t in tools]
        assert len(names) == len(set(names))

    def test_all_tools_have_descriptions(self, mock_client):
        for tool in get_bitable_tools(mock_client):
            assert tool.description
            assert len(tool.description) > 10

    def test_all_tools_have_parameters(self, mock_client):
        for tool in get_bitable_tools(mock_client):
            params = tool.parameters
            assert params["type"] == "object"
            assert "properties" in params

    def test_list_fields_params(self, mock_client):
        tool = FeishuBitableListFields(mock_client)
        assert tool.name == "feishu_bitable_list_fields"
        assert set(tool.parameters["required"]) == {"app_token", "table_id"}

    def test_create_record_params(self, mock_client):
        tool = FeishuBitableCreateRecord(mock_client)
        assert "fields" in tool.parameters["properties"]
        assert "fields" in tool.parameters["required"]


# ---------------------------------------------------------------------------
# Tool dispatch tests
# ---------------------------------------------------------------------------

class TestBitableToolDispatch:
    @pytest.mark.asyncio
    async def test_list_records_dispatches(self, mock_client):
        tool = FeishuBitableListRecords(mock_client)
        with patch("nanobot_feishu_tools.bitable.actions.list_records", new_callable=AsyncMock) as mock:
            mock.return_value = {"records": [], "has_more": False, "page_token": None, "total": 0}
            result = await tool.execute(app_token="app1", table_id="tbl1")
            mock.assert_awaited_once_with(mock_client, "app1", "tbl1", 100, None)
            data = json.loads(result)
            assert data["records"] == []

    @pytest.mark.asyncio
    async def test_create_record_dispatches(self, mock_client):
        tool = FeishuBitableCreateRecord(mock_client)
        with patch("nanobot_feishu_tools.bitable.actions.create_record", new_callable=AsyncMock) as mock:
            mock.return_value = {"record": {"record_id": "rec1"}}
            fields = {"Name": "Alice", "Score": 100}
            result = await tool.execute(app_token="app1", table_id="tbl1", fields=fields)
            mock.assert_awaited_once_with(mock_client, "app1", "tbl1", fields)

    @pytest.mark.asyncio
    async def test_update_record_dispatches(self, mock_client):
        tool = FeishuBitableUpdateRecord(mock_client)
        with patch("nanobot_feishu_tools.bitable.actions.update_record", new_callable=AsyncMock) as mock:
            mock.return_value = {"record": {"record_id": "rec1"}}
            fields = {"Score": 200}
            await tool.execute(app_token="app1", table_id="tbl1", record_id="rec1", fields=fields)
            mock.assert_awaited_once_with(mock_client, "app1", "tbl1", "rec1", fields)

    @pytest.mark.asyncio
    async def test_delete_record_dispatches(self, mock_client):
        tool = FeishuBitableDeleteRecord(mock_client)
        with patch("nanobot_feishu_tools.bitable.actions.delete_record", new_callable=AsyncMock) as mock:
            mock.return_value = {"success": True, "record_id": "rec1"}
            await tool.execute(app_token="app1", table_id="tbl1", record_id="rec1")
            mock.assert_awaited_once_with(mock_client, "app1", "tbl1", "rec1")

    @pytest.mark.asyncio
    async def test_batch_delete_dispatches(self, mock_client):
        tool = FeishuBitableBatchDeleteRecords(mock_client)
        with patch("nanobot_feishu_tools.bitable.actions.batch_delete_records", new_callable=AsyncMock) as mock:
            mock.return_value = {"results": [], "requested": 2, "deleted": 2}
            ids = ["rec1", "rec2"]
            await tool.execute(app_token="app1", table_id="tbl1", record_ids=ids)
            mock.assert_awaited_once_with(mock_client, "app1", "tbl1", ids)

    @pytest.mark.asyncio
    async def test_error_returns_error_string(self, mock_client):
        tool = FeishuBitableListRecords(mock_client)
        with patch("nanobot_feishu_tools.bitable.actions.list_records", new_callable=AsyncMock) as mock:
            mock.side_effect = RuntimeError("API timeout")
            result = await tool.execute(app_token="app1", table_id="tbl1")
            assert "Error" in result
            assert "API timeout" in result
