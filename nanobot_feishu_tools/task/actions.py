"""Feishu Task CRUD actions."""

from __future__ import annotations

from typing import Any

import lark_oapi as lark

from nanobot_feishu_tools._api import check_response, run_sync

TASK_UPDATE_FIELDS = {"summary", "description", "due", "start", "extra", "completed_at", "repeat_rule", "mode", "is_milestone"}
COMMENT_UPDATE_FIELDS = {"content"}
TASKLIST_UPDATE_FIELDS = {"name", "owner", "archive_tasklist"}


def _omit_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def _format_task(task: Any) -> dict | None:
    if task is None:
        return None
    return {
        "guid": getattr(task, "guid", None),
        "summary": getattr(task, "summary", None),
        "description": getattr(task, "description", None),
        "status": getattr(task, "status", None),
        "url": getattr(task, "url", None),
        "created_at": getattr(task, "created_at", None),
        "updated_at": getattr(task, "updated_at", None),
        "completed_at": getattr(task, "completed_at", None),
        "due": getattr(task, "due", None),
        "start": getattr(task, "start", None),
        "is_milestone": getattr(task, "is_milestone", None),
        "members": getattr(task, "members", None),
        "tasklists": getattr(task, "tasklists", None),
    }


def _format_tasklist(tl: Any) -> dict | None:
    if tl is None:
        return None
    return {
        "guid": getattr(tl, "guid", None),
        "name": getattr(tl, "name", None),
        "creator": getattr(tl, "creator", None),
        "owner": getattr(tl, "owner", None),
        "members": getattr(tl, "members", None),
        "url": getattr(tl, "url", None),
        "created_at": getattr(tl, "created_at", None),
        "updated_at": getattr(tl, "updated_at", None),
    }


def _format_comment(c: Any) -> dict | None:
    if c is None:
        return None
    return {
        "id": getattr(c, "id", None),
        "content": getattr(c, "content", None),
        "creator": getattr(c, "creator", None),
        "reply_to_comment_id": getattr(c, "reply_to_comment_id", None),
        "created_at": getattr(c, "created_at", None),
        "updated_at": getattr(c, "updated_at", None),
    }


def _format_attachment(a: Any) -> dict | None:
    if a is None:
        return None
    return {
        "guid": getattr(a, "guid", None),
        "file_token": getattr(a, "file_token", None),
        "name": getattr(a, "name", None),
        "size": getattr(a, "size", None),
        "uploader": getattr(a, "uploader", None),
        "uploaded_at": getattr(a, "uploaded_at", None),
    }


def _infer_fields(obj: dict, supported: set[str]) -> list[str]:
    return [k for k in obj if k in supported]


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------

async def create_task(client: lark.Client, params: dict) -> dict:
    from lark_oapi.api.task.v2 import CreateTaskRequest, InputTask

    body_data = _omit_none({
        "summary": params.get("summary"),
        "description": params.get("description"),
        "due": params.get("due"),
        "start": params.get("start"),
        "extra": params.get("extra"),
        "completed_at": params.get("completed_at"),
        "members": params.get("members"),
        "repeat_rule": params.get("repeat_rule"),
        "tasklists": params.get("tasklists"),
        "mode": params.get("mode"),
        "is_milestone": params.get("is_milestone"),
    })

    builder = CreateTaskRequest.builder().request_body(InputTask.builder().build())
    # Use raw request since builder patterns vary across versions
    import lark_oapi
    raw_req = lark_oapi.RawRequest.builder() \
        .http_method("POST") \
        .uri("/open-apis/task/v2/tasks") \
        .body(body_data) \
        .build()

    if params.get("user_id_type"):
        raw_req = lark_oapi.RawRequest.builder() \
            .http_method("POST") \
            .uri(f"/open-apis/task/v2/tasks?user_id_type={params['user_id_type']}") \
            .body(body_data) \
            .build()

    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"create_task failed: code={resp.code}, msg={resp.msg}")

    import json
    data = json.loads(resp.raw.content)
    return {"task": data.get("data", {}).get("task")}


async def get_task(client: lark.Client, task_guid: str, user_id_type: str | None = None) -> dict:
    import lark_oapi
    import json

    uri = f"/open-apis/task/v2/tasks/{task_guid}"
    if user_id_type:
        uri += f"?user_id_type={user_id_type}"

    raw_req = lark_oapi.RawRequest.builder().http_method("GET").uri(uri).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"get_task failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    return {"task": data.get("data", {}).get("task")}


async def update_task(client: lark.Client, params: dict) -> dict:
    import lark_oapi
    import json

    task_guid = params["task_guid"]
    task_body = _omit_none(params.get("task", {}))
    update_fields = params.get("update_fields") or _infer_fields(task_body, TASK_UPDATE_FIELDS)

    if not task_body:
        raise ValueError("task update payload is empty")
    if not update_fields:
        raise ValueError("no valid update_fields provided or inferred")

    body = {"task": task_body, "update_fields": update_fields}
    uri = f"/open-apis/task/v2/tasks/{task_guid}"
    if params.get("user_id_type"):
        uri += f"?user_id_type={params['user_id_type']}"

    raw_req = lark_oapi.RawRequest.builder().http_method("PATCH").uri(uri).body(body).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"update_task failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    return {"task": data.get("data", {}).get("task"), "update_fields": update_fields}


async def delete_task(client: lark.Client, task_guid: str) -> dict:
    import lark_oapi

    raw_req = lark_oapi.RawRequest.builder().http_method("DELETE").uri(f"/open-apis/task/v2/tasks/{task_guid}").build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"delete_task failed: code={resp.code}, msg={resp.msg}")

    return {"success": True, "task_guid": task_guid}


async def create_subtask(client: lark.Client, params: dict) -> dict:
    import lark_oapi
    import json

    task_guid = params.pop("task_guid")
    body_data = _omit_none({
        "summary": params.get("summary"),
        "description": params.get("description"),
        "due": params.get("due"),
        "start": params.get("start"),
        "members": params.get("members"),
    })

    uri = f"/open-apis/task/v2/tasks/{task_guid}/subtasks"
    if params.get("user_id_type"):
        uri += f"?user_id_type={params['user_id_type']}"

    raw_req = lark_oapi.RawRequest.builder().http_method("POST").uri(uri).body(body_data).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"create_subtask failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    return {"subtask": data.get("data", {}).get("subtask")}


# ---------------------------------------------------------------------------
# Task-Tasklist association
# ---------------------------------------------------------------------------

async def add_task_to_tasklist(client: lark.Client, params: dict) -> dict:
    import lark_oapi
    import json

    task_guid = params["task_guid"]
    body = _omit_none({"tasklist_guid": params["tasklist_guid"], "section_guid": params.get("section_guid")})
    uri = f"/open-apis/task/v2/tasks/{task_guid}/add_tasklist"
    if params.get("user_id_type"):
        uri += f"?user_id_type={params['user_id_type']}"

    raw_req = lark_oapi.RawRequest.builder().http_method("POST").uri(uri).body(body).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"add_task_to_tasklist failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    return {"task": data.get("data", {}).get("task")}


async def remove_task_from_tasklist(client: lark.Client, params: dict) -> dict:
    import lark_oapi
    import json

    task_guid = params["task_guid"]
    body = _omit_none({"tasklist_guid": params["tasklist_guid"]})
    uri = f"/open-apis/task/v2/tasks/{task_guid}/remove_tasklist"
    if params.get("user_id_type"):
        uri += f"?user_id_type={params['user_id_type']}"

    raw_req = lark_oapi.RawRequest.builder().http_method("POST").uri(uri).body(body).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"remove_task_from_tasklist failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    return {"task": data.get("data", {}).get("task")}


# ---------------------------------------------------------------------------
# Tasklist CRUD
# ---------------------------------------------------------------------------

async def create_tasklist(client: lark.Client, params: dict) -> dict:
    import lark_oapi
    import json

    body = _omit_none({"name": params["name"], "members": params.get("members"), "archive_tasklist": params.get("archive_tasklist")})
    uri = "/open-apis/task/v2/tasklists"
    if params.get("user_id_type"):
        uri += f"?user_id_type={params['user_id_type']}"

    raw_req = lark_oapi.RawRequest.builder().http_method("POST").uri(uri).body(body).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"create_tasklist failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    return {"tasklist": data.get("data", {}).get("tasklist")}


async def get_tasklist(client: lark.Client, tasklist_guid: str, user_id_type: str | None = None) -> dict:
    import lark_oapi
    import json

    uri = f"/open-apis/task/v2/tasklists/{tasklist_guid}"
    if user_id_type:
        uri += f"?user_id_type={user_id_type}"

    raw_req = lark_oapi.RawRequest.builder().http_method("GET").uri(uri).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"get_tasklist failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    return {"tasklist": data.get("data", {}).get("tasklist")}


async def list_tasklists(client: lark.Client, params: dict) -> dict:
    import lark_oapi
    import json

    qs_parts = []
    if params.get("page_size"):
        qs_parts.append(f"page_size={params['page_size']}")
    if params.get("page_token"):
        qs_parts.append(f"page_token={params['page_token']}")
    if params.get("user_id_type"):
        qs_parts.append(f"user_id_type={params['user_id_type']}")

    uri = "/open-apis/task/v2/tasklists"
    if qs_parts:
        uri += "?" + "&".join(qs_parts)

    raw_req = lark_oapi.RawRequest.builder().http_method("GET").uri(uri).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"list_tasklists failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    resp_data = data.get("data", {})
    return {
        "items": resp_data.get("items", []),
        "page_token": resp_data.get("page_token"),
        "has_more": resp_data.get("has_more", False),
    }


async def update_tasklist(client: lark.Client, params: dict) -> dict:
    import lark_oapi
    import json

    tasklist_guid = params["tasklist_guid"]
    tasklist_body = _omit_none(params.get("tasklist", {}))
    update_fields = params.get("update_fields") or _infer_fields(tasklist_body, TASKLIST_UPDATE_FIELDS)

    if not tasklist_body:
        raise ValueError("tasklist update payload is empty")
    if not update_fields:
        raise ValueError("no valid update_fields provided or inferred")

    body = _omit_none({
        "tasklist": tasklist_body,
        "update_fields": update_fields,
        "origin_owner_to_role": params.get("origin_owner_to_role"),
    })

    uri = f"/open-apis/task/v2/tasklists/{tasklist_guid}"
    if params.get("user_id_type"):
        uri += f"?user_id_type={params['user_id_type']}"

    raw_req = lark_oapi.RawRequest.builder().http_method("PATCH").uri(uri).body(body).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"update_tasklist failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    return {"tasklist": data.get("data", {}).get("tasklist"), "update_fields": update_fields}


async def delete_tasklist(client: lark.Client, tasklist_guid: str) -> dict:
    import lark_oapi

    raw_req = lark_oapi.RawRequest.builder().http_method("DELETE").uri(f"/open-apis/task/v2/tasklists/{tasklist_guid}").build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"delete_tasklist failed: code={resp.code}, msg={resp.msg}")

    return {"success": True, "tasklist_guid": tasklist_guid}


# ---------------------------------------------------------------------------
# Tasklist members
# ---------------------------------------------------------------------------

async def add_tasklist_members(client: lark.Client, params: dict) -> dict:
    import lark_oapi
    import json

    tasklist_guid = params["tasklist_guid"]
    body = {"members": params["members"]}
    uri = f"/open-apis/task/v2/tasklists/{tasklist_guid}/add_members"
    if params.get("user_id_type"):
        uri += f"?user_id_type={params['user_id_type']}"

    raw_req = lark_oapi.RawRequest.builder().http_method("POST").uri(uri).body(body).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"add_tasklist_members failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    return {"tasklist": data.get("data", {}).get("tasklist")}


async def remove_tasklist_members(client: lark.Client, params: dict) -> dict:
    import lark_oapi
    import json

    tasklist_guid = params["tasklist_guid"]
    body = {"members": params["members"]}
    uri = f"/open-apis/task/v2/tasklists/{tasklist_guid}/remove_members"
    if params.get("user_id_type"):
        uri += f"?user_id_type={params['user_id_type']}"

    raw_req = lark_oapi.RawRequest.builder().http_method("POST").uri(uri).body(body).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"remove_tasklist_members failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    return {"tasklist": data.get("data", {}).get("tasklist")}


# ---------------------------------------------------------------------------
# Task Comments
# ---------------------------------------------------------------------------

async def create_task_comment(client: lark.Client, params: dict) -> dict:
    import lark_oapi
    import json

    body = _omit_none({
        "content": params["content"],
        "reply_to_comment_id": params.get("reply_to_comment_id"),
        "resource_type": "task",
        "resource_id": params["task_guid"],
    })
    uri = "/open-apis/task/v2/comments"
    if params.get("user_id_type"):
        uri += f"?user_id_type={params['user_id_type']}"

    raw_req = lark_oapi.RawRequest.builder().http_method("POST").uri(uri).body(body).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"create_task_comment failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    return {"comment": data.get("data", {}).get("comment")}


async def get_task_comment(client: lark.Client, comment_id: str, user_id_type: str | None = None) -> dict:
    import lark_oapi
    import json

    uri = f"/open-apis/task/v2/comments/{comment_id}"
    if user_id_type:
        uri += f"?user_id_type={user_id_type}"

    raw_req = lark_oapi.RawRequest.builder().http_method("GET").uri(uri).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"get_task_comment failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    return {"comment": data.get("data", {}).get("comment")}


async def list_task_comments(client: lark.Client, params: dict) -> dict:
    import lark_oapi
    import json

    qs_parts = [f"resource_type=task", f"resource_id={params['task_guid']}"]
    for k in ("page_size", "page_token", "direction", "user_id_type"):
        if params.get(k):
            qs_parts.append(f"{k}={params[k]}")

    uri = "/open-apis/task/v2/comments?" + "&".join(qs_parts)
    raw_req = lark_oapi.RawRequest.builder().http_method("GET").uri(uri).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"list_task_comments failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    resp_data = data.get("data", {})
    return {
        "items": resp_data.get("items", []),
        "page_token": resp_data.get("page_token"),
        "has_more": resp_data.get("has_more", False),
    }


async def update_task_comment(client: lark.Client, params: dict) -> dict:
    import lark_oapi
    import json

    comment_id = params["comment_id"]
    comment_body = _omit_none(params.get("comment", {}))
    update_fields = params.get("update_fields") or _infer_fields(comment_body, COMMENT_UPDATE_FIELDS)

    if not comment_body:
        raise ValueError("comment update payload is empty")
    if not update_fields:
        raise ValueError("no valid update_fields provided or inferred")

    body = {"comment": comment_body, "update_fields": update_fields}
    uri = f"/open-apis/task/v2/comments/{comment_id}"
    if params.get("user_id_type"):
        uri += f"?user_id_type={params['user_id_type']}"

    raw_req = lark_oapi.RawRequest.builder().http_method("PATCH").uri(uri).body(body).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"update_task_comment failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    return {"comment": data.get("data", {}).get("comment"), "update_fields": update_fields}


async def delete_task_comment(client: lark.Client, comment_id: str) -> dict:
    import lark_oapi

    raw_req = lark_oapi.RawRequest.builder().http_method("DELETE").uri(f"/open-apis/task/v2/comments/{comment_id}").build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"delete_task_comment failed: code={resp.code}, msg={resp.msg}")

    return {"success": True, "comment_id": comment_id}


# ---------------------------------------------------------------------------
# Task Attachments
# ---------------------------------------------------------------------------

async def list_task_attachments(client: lark.Client, params: dict) -> dict:
    import lark_oapi
    import json

    qs_parts = [f"resource_type=task", f"resource_id={params['task_guid']}"]
    for k in ("page_size", "page_token", "user_id_type"):
        if params.get(k):
            qs_parts.append(f"{k}={params[k]}")

    uri = "/open-apis/task/v2/attachments?" + "&".join(qs_parts)
    raw_req = lark_oapi.RawRequest.builder().http_method("GET").uri(uri).build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"list_task_attachments failed: code={resp.code}, msg={resp.msg}")

    data = json.loads(resp.raw.content)
    resp_data = data.get("data", {})
    return {
        "items": resp_data.get("items", []),
        "page_token": resp_data.get("page_token"),
        "has_more": resp_data.get("has_more", False),
    }


async def delete_task_attachment(client: lark.Client, attachment_guid: str) -> dict:
    import lark_oapi

    raw_req = lark_oapi.RawRequest.builder().http_method("DELETE").uri(f"/open-apis/task/v2/attachments/{attachment_guid}").build()
    resp = await run_sync(client.request, raw_req)
    if not resp.success:
        raise ValueError(f"delete_task_attachment failed: code={resp.code}, msg={resp.msg}")

    return {"success": True, "attachment_guid": attachment_guid}
