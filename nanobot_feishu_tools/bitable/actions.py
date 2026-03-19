"""Bitable field and record CRUD actions."""

from __future__ import annotations

from typing import Any

import lark_oapi as lark

from nanobot_feishu_tools._api import check_response, run_sync


# ---------------------------------------------------------------------------
# Field operations
# ---------------------------------------------------------------------------

async def list_fields(client: lark.Client, app_token: str, table_id: str) -> dict:
    from lark_oapi.api.bitable.v1 import ListAppTableFieldRequest

    req = (
        ListAppTableFieldRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .build()
    )
    resp = await run_sync(client.bitable.v1.app_table_field.list, req)
    check_response(resp, "bitable.v1.app_table_field.list")

    items = resp.data.items or [] if resp.data else []
    return {"fields": [_format_field(f) for f in items], "total": len(items)}


async def create_field(
    client: lark.Client, app_token: str, table_id: str,
    field_name: str, field_type: int,
    property: dict | None = None, description: dict | None = None, ui_type: str | None = None,
) -> dict:
    from lark_oapi.api.bitable.v1 import CreateAppTableFieldRequest, AppTableField

    field_builder = AppTableField.builder().field_name(field_name).type(field_type)
    if property:
        field_builder = field_builder.property(property)
    if description:
        field_builder = field_builder.description(description)
    if ui_type:
        field_builder = field_builder.ui_type(ui_type)

    req = (
        CreateAppTableFieldRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .request_body(field_builder.build())
        .build()
    )
    resp = await run_sync(client.bitable.v1.app_table_field.create, req)
    check_response(resp, "bitable.v1.app_table_field.create")

    return {"field": _format_field(resp.data.field) if resp.data and resp.data.field else None}


async def update_field(
    client: lark.Client, app_token: str, table_id: str, field_id: str,
    field_name: str, field_type: int,
    property: dict | None = None, description: dict | None = None, ui_type: str | None = None,
) -> dict:
    from lark_oapi.api.bitable.v1 import UpdateAppTableFieldRequest, AppTableField

    field_builder = AppTableField.builder().field_name(field_name).type(field_type)
    if property:
        field_builder = field_builder.property(property)
    if description:
        field_builder = field_builder.description(description)
    if ui_type:
        field_builder = field_builder.ui_type(ui_type)

    req = (
        UpdateAppTableFieldRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .field_id(field_id)
        .request_body(field_builder.build())
        .build()
    )
    resp = await run_sync(client.bitable.v1.app_table_field.update, req)
    check_response(resp, "bitable.v1.app_table_field.update")

    return {"field": _format_field(resp.data.field) if resp.data and resp.data.field else None}


async def delete_field(client: lark.Client, app_token: str, table_id: str, field_id: str) -> dict:
    from lark_oapi.api.bitable.v1 import DeleteAppTableFieldRequest

    req = (
        DeleteAppTableFieldRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .field_id(field_id)
        .build()
    )
    resp = await run_sync(client.bitable.v1.app_table_field.delete, req)
    check_response(resp, "bitable.v1.app_table_field.delete")

    return {"success": True, "field_id": field_id}


# ---------------------------------------------------------------------------
# Record operations
# ---------------------------------------------------------------------------

async def list_records(
    client: lark.Client, app_token: str, table_id: str,
    page_size: int = 100, page_token: str | None = None,
) -> dict:
    from lark_oapi.api.bitable.v1 import ListAppTableRecordRequest

    builder = (
        ListAppTableRecordRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .page_size(page_size)
    )
    if page_token:
        builder = builder.page_token(page_token)

    resp = await run_sync(client.bitable.v1.app_table_record.list, builder.build())
    check_response(resp, "bitable.v1.app_table_record.list")

    items = resp.data.items or [] if resp.data else []
    return {
        "records": [_format_record(r) for r in items],
        "has_more": bool(resp.data.has_more) if resp.data else False,
        "page_token": resp.data.page_token if resp.data else None,
        "total": resp.data.total if resp.data else 0,
    }


async def get_record(client: lark.Client, app_token: str, table_id: str, record_id: str) -> dict:
    from lark_oapi.api.bitable.v1 import GetAppTableRecordRequest

    req = (
        GetAppTableRecordRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .record_id(record_id)
        .build()
    )
    resp = await run_sync(client.bitable.v1.app_table_record.get, req)
    check_response(resp, "bitable.v1.app_table_record.get")

    return {"record": _format_record(resp.data.record) if resp.data and resp.data.record else None}


async def create_record(
    client: lark.Client, app_token: str, table_id: str, fields: dict,
) -> dict:
    from lark_oapi.api.bitable.v1 import CreateAppTableRecordRequest, AppTableRecord

    record = AppTableRecord.builder().fields(fields).build()
    req = (
        CreateAppTableRecordRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .request_body(record)
        .build()
    )
    resp = await run_sync(client.bitable.v1.app_table_record.create, req)
    check_response(resp, "bitable.v1.app_table_record.create")

    return {"record": _format_record(resp.data.record) if resp.data and resp.data.record else None}


async def update_record(
    client: lark.Client, app_token: str, table_id: str,
    record_id: str, fields: dict,
) -> dict:
    from lark_oapi.api.bitable.v1 import UpdateAppTableRecordRequest, AppTableRecord

    record = AppTableRecord.builder().fields(fields).build()
    req = (
        UpdateAppTableRecordRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .record_id(record_id)
        .request_body(record)
        .build()
    )
    resp = await run_sync(client.bitable.v1.app_table_record.update, req)
    check_response(resp, "bitable.v1.app_table_record.update")

    return {"record": _format_record(resp.data.record) if resp.data and resp.data.record else None}


async def delete_record(client: lark.Client, app_token: str, table_id: str, record_id: str) -> dict:
    from lark_oapi.api.bitable.v1 import DeleteAppTableRecordRequest

    req = (
        DeleteAppTableRecordRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .record_id(record_id)
        .build()
    )
    resp = await run_sync(client.bitable.v1.app_table_record.delete, req)
    check_response(resp, "bitable.v1.app_table_record.delete")

    return {"success": True, "record_id": record_id}


async def batch_delete_records(
    client: lark.Client, app_token: str, table_id: str, record_ids: list[str],
) -> dict:
    from lark_oapi.api.bitable.v1 import BatchDeleteAppTableRecordRequest, BatchDeleteAppTableRecordRequestBody

    body = BatchDeleteAppTableRecordRequestBody.builder().records(record_ids).build()
    req = (
        BatchDeleteAppTableRecordRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .request_body(body)
        .build()
    )
    resp = await run_sync(client.bitable.v1.app_table_record.batch_delete, req)
    check_response(resp, "bitable.v1.app_table_record.batch_delete")

    records = resp.data.records or [] if resp.data else []
    return {
        "results": records,
        "requested": len(record_ids),
        "deleted": sum(1 for r in records if getattr(r, "deleted", True)),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_field(f: Any) -> dict | None:
    if f is None:
        return None
    return {
        "field_id": getattr(f, "field_id", None),
        "field_name": getattr(f, "field_name", None),
        "type": getattr(f, "type", None),
        "property": getattr(f, "property", None),
        "description": getattr(f, "description", None),
        "ui_type": getattr(f, "ui_type", None),
    }


def _format_record(r: Any) -> dict | None:
    if r is None:
        return None
    return {
        "record_id": getattr(r, "record_id", None),
        "fields": getattr(r, "fields", None),
        "created_by": getattr(r, "created_by", None),
        "created_time": getattr(r, "created_time", None),
        "last_modified_by": getattr(r, "last_modified_by", None),
        "last_modified_time": getattr(r, "last_modified_time", None),
    }
