"""Bitable Tool subclasses — each bitable operation is a separate tool."""

from __future__ import annotations

from typing import Any

import lark_oapi as lark

from nanobot.agent.tools.base import Tool
from nanobot_feishu_tools._api import to_json
from nanobot_feishu_tools.bitable import actions
from nanobot_feishu_tools.bitable.meta import get_bitable_meta


# ---------------------------------------------------------------------------
# Base helper
# ---------------------------------------------------------------------------

class _BitableTool(Tool):
    """Base class for bitable tools."""

    _name: str = ""
    _description: str = ""
    _parameters: dict[str, Any] = {}

    def __init__(self, client: lark.Client):
        self._client = client

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters


# ---------------------------------------------------------------------------
# Get Meta
# ---------------------------------------------------------------------------

class FeishuBitableGetMeta(_BitableTool):
    _name = "feishu_bitable_get_meta"
    _description = "Parse a Feishu Bitable URL to extract app_token and table_id. Supports /base/XXX and /wiki/XXX URLs."
    _parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Bitable URL. Supports both formats: /base/XXX?table=YYY or /wiki/XXX?table=YYY"},
        },
        "required": ["url"],
    }

    async def execute(self, url: str, **kw: Any) -> str:
        try:
            return to_json(await get_bitable_meta(self._client, url))
        except Exception as e:
            return f"Error: {e}"


# ---------------------------------------------------------------------------
# Field tools
# ---------------------------------------------------------------------------

_FIELD_BASE = {
    "app_token": {"type": "string", "description": "Bitable app token (use feishu_bitable_get_meta to get from URL)"},
    "table_id": {"type": "string", "description": "Table ID (from URL: ?table=YYY)"},
}


class FeishuBitableListFields(_BitableTool):
    _name = "feishu_bitable_list_fields"
    _description = "List all fields (columns) of a Feishu Bitable table."
    _parameters = {"type": "object", "properties": _FIELD_BASE, "required": ["app_token", "table_id"]}

    async def execute(self, app_token: str, table_id: str, **kw: Any) -> str:
        try:
            return to_json(await actions.list_fields(self._client, app_token, table_id))
        except Exception as e:
            return f"Error: {e}"


class FeishuBitableCreateField(_BitableTool):
    _name = "feishu_bitable_create_field"
    _description = "Create a new field (column) in a Feishu Bitable table."
    _parameters = {
        "type": "object",
        "properties": {
            **_FIELD_BASE,
            "field_name": {"type": "string", "description": "Field name"},
            "type": {"type": "integer", "description": "Field type ID (e.g., 1=Text, 2=Number, 3=SingleSelect, 4=MultiSelect)"},
            "property": {"type": "object", "description": "Optional field property object (e.g., select options/date format)"},
            "description": {"type": "object", "description": "Optional field description metadata"},
            "ui_type": {"type": "string", "description": "Optional UI type override"},
        },
        "required": ["app_token", "table_id", "field_name", "type"],
    }

    async def execute(self, app_token: str, table_id: str, field_name: str, type: int, **kw: Any) -> str:
        try:
            return to_json(await actions.create_field(
                self._client, app_token, table_id, field_name, type,
                kw.get("property"), kw.get("description"), kw.get("ui_type"),
            ))
        except Exception as e:
            return f"Error: {e}"


class FeishuBitableUpdateField(_BitableTool):
    _name = "feishu_bitable_update_field"
    _description = "Update an existing field (column) in a Feishu Bitable table."
    _parameters = {
        "type": "object",
        "properties": {
            **_FIELD_BASE,
            "field_id": {"type": "string", "description": "Field ID to update"},
            "field_name": {"type": "string", "description": "Updated field name"},
            "type": {"type": "integer", "description": "Updated field type ID"},
            "property": {"type": "object", "description": "Optional field property object"},
            "description": {"type": "object", "description": "Optional field description metadata"},
            "ui_type": {"type": "string", "description": "Optional UI type override"},
        },
        "required": ["app_token", "table_id", "field_id", "field_name", "type"],
    }

    async def execute(self, app_token: str, table_id: str, field_id: str, field_name: str, type: int, **kw: Any) -> str:
        try:
            return to_json(await actions.update_field(
                self._client, app_token, table_id, field_id, field_name, type,
                kw.get("property"), kw.get("description"), kw.get("ui_type"),
            ))
        except Exception as e:
            return f"Error: {e}"


class FeishuBitableDeleteField(_BitableTool):
    _name = "feishu_bitable_delete_field"
    _description = "Delete a field (column) from a Feishu Bitable table."
    _parameters = {
        "type": "object",
        "properties": {
            **_FIELD_BASE,
            "field_id": {"type": "string", "description": "Field ID to delete"},
        },
        "required": ["app_token", "table_id", "field_id"],
    }

    async def execute(self, app_token: str, table_id: str, field_id: str, **kw: Any) -> str:
        try:
            return to_json(await actions.delete_field(self._client, app_token, table_id, field_id))
        except Exception as e:
            return f"Error: {e}"


# ---------------------------------------------------------------------------
# Record tools
# ---------------------------------------------------------------------------

class FeishuBitableListRecords(_BitableTool):
    _name = "feishu_bitable_list_records"
    _description = "List records (rows) from a Feishu Bitable table."
    _parameters = {
        "type": "object",
        "properties": {
            **_FIELD_BASE,
            "page_size": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Number of records per page (1-500, default 100)"},
            "page_token": {"type": "string", "description": "Pagination token from previous response"},
        },
        "required": ["app_token", "table_id"],
    }

    async def execute(self, app_token: str, table_id: str, page_size: int = 100, page_token: str = "", **kw: Any) -> str:
        try:
            return to_json(await actions.list_records(
                self._client, app_token, table_id, page_size, page_token or None,
            ))
        except Exception as e:
            return f"Error: {e}"


class FeishuBitableGetRecord(_BitableTool):
    _name = "feishu_bitable_get_record"
    _description = "Get a single record (row) from a Feishu Bitable table."
    _parameters = {
        "type": "object",
        "properties": {
            **_FIELD_BASE,
            "record_id": {"type": "string", "description": "Record ID to retrieve"},
        },
        "required": ["app_token", "table_id", "record_id"],
    }

    async def execute(self, app_token: str, table_id: str, record_id: str, **kw: Any) -> str:
        try:
            return to_json(await actions.get_record(self._client, app_token, table_id, record_id))
        except Exception as e:
            return f"Error: {e}"


class FeishuBitableCreateRecord(_BitableTool):
    _name = "feishu_bitable_create_record"
    _description = (
        "Create a record (row) in a Feishu Bitable table. "
        "Field values keyed by field name. Format by type: Text='string', Number=123, "
        "SingleSelect='Option', MultiSelect=['A','B'], DateTime=timestamp_ms, "
        "User=[{id:'ou_xxx'}], URL={text:'Display',link:'https://...'}"
    )
    _parameters = {
        "type": "object",
        "properties": {
            **_FIELD_BASE,
            "fields": {"type": "object", "description": "Field values keyed by field name"},
        },
        "required": ["app_token", "table_id", "fields"],
    }

    async def execute(self, app_token: str, table_id: str, fields: dict, **kw: Any) -> str:
        try:
            return to_json(await actions.create_record(self._client, app_token, table_id, fields))
        except Exception as e:
            return f"Error: {e}"


class FeishuBitableUpdateRecord(_BitableTool):
    _name = "feishu_bitable_update_record"
    _description = "Update a record (row) in a Feishu Bitable table."
    _parameters = {
        "type": "object",
        "properties": {
            **_FIELD_BASE,
            "record_id": {"type": "string", "description": "Record ID to update"},
            "fields": {"type": "object", "description": "Field values to update (same format as create_record)"},
        },
        "required": ["app_token", "table_id", "record_id", "fields"],
    }

    async def execute(self, app_token: str, table_id: str, record_id: str, fields: dict, **kw: Any) -> str:
        try:
            return to_json(await actions.update_record(self._client, app_token, table_id, record_id, fields))
        except Exception as e:
            return f"Error: {e}"


class FeishuBitableDeleteRecord(_BitableTool):
    _name = "feishu_bitable_delete_record"
    _description = "Delete a record (row) from a Feishu Bitable table."
    _parameters = {
        "type": "object",
        "properties": {
            **_FIELD_BASE,
            "record_id": {"type": "string", "description": "Record ID to delete"},
        },
        "required": ["app_token", "table_id", "record_id"],
    }

    async def execute(self, app_token: str, table_id: str, record_id: str, **kw: Any) -> str:
        try:
            return to_json(await actions.delete_record(self._client, app_token, table_id, record_id))
        except Exception as e:
            return f"Error: {e}"


class FeishuBitableBatchDeleteRecords(_BitableTool):
    _name = "feishu_bitable_batch_delete_records"
    _description = "Batch delete records (rows) from a Feishu Bitable table (max 500 per request)."
    _parameters = {
        "type": "object",
        "properties": {
            **_FIELD_BASE,
            "record_ids": {"type": "array", "items": {"type": "string"}, "description": "Record ID list to delete (max 500 per request)", "minItems": 1, "maxItems": 500},
        },
        "required": ["app_token", "table_id", "record_ids"],
    }

    async def execute(self, app_token: str, table_id: str, record_ids: list[str], **kw: Any) -> str:
        try:
            return to_json(await actions.batch_delete_records(self._client, app_token, table_id, record_ids))
        except Exception as e:
            return f"Error: {e}"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_bitable_tools(client: lark.Client) -> list[Tool]:
    """Return all bitable tool instances."""
    return [
        FeishuBitableGetMeta(client),
        FeishuBitableListFields(client),
        FeishuBitableCreateField(client),
        FeishuBitableUpdateField(client),
        FeishuBitableDeleteField(client),
        FeishuBitableListRecords(client),
        FeishuBitableGetRecord(client),
        FeishuBitableCreateRecord(client),
        FeishuBitableUpdateRecord(client),
        FeishuBitableDeleteRecord(client),
        FeishuBitableBatchDeleteRecords(client),
    ]
