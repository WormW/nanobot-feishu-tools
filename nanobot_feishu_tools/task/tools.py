"""Feishu Task Tool subclasses — each task operation is a separate tool."""

from __future__ import annotations

from typing import Any

import lark_oapi as lark

from nanobot.agent.tools.base import Tool
from nanobot_feishu_tools._api import to_json
from nanobot_feishu_tools.task import actions


class _TaskTool(Tool):
    """Base class for task tools."""

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


_UID_TYPE = {"type": "string", "description": "User ID type (open_id/user_id/union_id)"}

_TASK_DATE = {
    "type": "object",
    "properties": {
        "timestamp": {"type": "string", "description": "Unix timestamp in ms (13-digit string)"},
        "is_all_day": {"type": "boolean", "description": "Whether all-day"},
    },
}

_TASK_MEMBER = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "Member ID"},
        "type": {"type": "string", "description": "Member type (usually 'user')"},
        "role": {"type": "string", "description": "Member role (e.g. 'assignee')"},
    },
    "required": ["id", "role"],
}


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------

class FeishuTaskCreate(_TaskTool):
    _name = "feishu_task_create"
    _description = "Create a Feishu task (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "Task title/summary"},
            "description": {"type": "string", "description": "Task description"},
            "due": _TASK_DATE,
            "start": _TASK_DATE,
            "extra": {"type": "string", "description": "Custom opaque metadata string"},
            "completed_at": {"type": "string", "description": "Completion time (ms timestamp string)"},
            "members": {"type": "array", "items": _TASK_MEMBER, "description": "Initial task members"},
            "repeat_rule": {"type": "string", "description": "Task repeat rule"},
            "tasklists": {"type": "array", "items": {"type": "object", "properties": {"tasklist_guid": {"type": "string"}, "section_guid": {"type": "string"}}}, "description": "Attach to tasklists"},
            "mode": {"type": "integer", "description": "Task mode value"},
            "is_milestone": {"type": "boolean", "description": "Whether milestone"},
            "user_id_type": _UID_TYPE,
        },
        "required": ["summary"],
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.create_task(self._client, kw))
        except Exception as e:
            return f"Error: {e}"


class FeishuTaskGet(_TaskTool):
    _name = "feishu_task_get"
    _description = "Get Feishu task details by task_guid (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "task_guid": {"type": "string", "description": "Task GUID to retrieve"},
            "user_id_type": _UID_TYPE,
        },
        "required": ["task_guid"],
    }

    async def execute(self, task_guid: str, user_id_type: str = "", **kw: Any) -> str:
        try:
            return to_json(await actions.get_task(self._client, task_guid, user_id_type or None))
        except Exception as e:
            return f"Error: {e}"


class FeishuTaskUpdate(_TaskTool):
    _name = "feishu_task_update"
    _description = "Update a Feishu task by task_guid (task v2 patch)"
    _parameters = {
        "type": "object",
        "properties": {
            "task_guid": {"type": "string", "description": "Task GUID to update"},
            "task": {"type": "object", "description": "Task fields to update (summary, description, due, start, etc.)"},
            "update_fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to update (auto-inferred if omitted)"},
            "user_id_type": _UID_TYPE,
        },
        "required": ["task_guid", "task"],
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.update_task(self._client, kw))
        except Exception as e:
            return f"Error: {e}"


class FeishuTaskDelete(_TaskTool):
    _name = "feishu_task_delete"
    _description = "Delete a Feishu task by task_guid (task v2)"
    _parameters = {
        "type": "object",
        "properties": {"task_guid": {"type": "string", "description": "Task GUID to delete"}},
        "required": ["task_guid"],
    }

    async def execute(self, task_guid: str, **kw: Any) -> str:
        try:
            return to_json(await actions.delete_task(self._client, task_guid))
        except Exception as e:
            return f"Error: {e}"


class FeishuTaskCreateSubtask(_TaskTool):
    _name = "feishu_task_subtask_create"
    _description = "Create a Feishu subtask under a parent task (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "task_guid": {"type": "string", "description": "Parent task GUID"},
            "summary": {"type": "string", "description": "Subtask title/summary"},
            "description": {"type": "string", "description": "Subtask description"},
            "due": _TASK_DATE,
            "start": _TASK_DATE,
            "members": {"type": "array", "items": _TASK_MEMBER},
            "user_id_type": _UID_TYPE,
        },
        "required": ["task_guid", "summary"],
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.create_subtask(self._client, dict(kw)))
        except Exception as e:
            return f"Error: {e}"


# ---------------------------------------------------------------------------
# Task-Tasklist association
# ---------------------------------------------------------------------------

class FeishuTaskAddTasklist(_TaskTool):
    _name = "feishu_task_add_tasklist"
    _description = "Add a task into a tasklist (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "task_guid": {"type": "string", "description": "Task GUID"},
            "tasklist_guid": {"type": "string", "description": "Tasklist GUID"},
            "section_guid": {"type": "string", "description": "Section GUID (optional)"},
            "user_id_type": _UID_TYPE,
        },
        "required": ["task_guid", "tasklist_guid"],
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.add_task_to_tasklist(self._client, kw))
        except Exception as e:
            return f"Error: {e}"


class FeishuTaskRemoveTasklist(_TaskTool):
    _name = "feishu_task_remove_tasklist"
    _description = "Remove a task from a tasklist (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "task_guid": {"type": "string", "description": "Task GUID"},
            "tasklist_guid": {"type": "string", "description": "Tasklist GUID"},
            "user_id_type": _UID_TYPE,
        },
        "required": ["task_guid", "tasklist_guid"],
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.remove_task_from_tasklist(self._client, kw))
        except Exception as e:
            return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tasklist CRUD
# ---------------------------------------------------------------------------

_TASKLIST_MEMBER = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "Member ID"},
        "type": {"type": "string", "description": "Member type (user/chat/app)"},
        "role": {"type": "string", "enum": ["owner", "editor", "viewer"], "description": "Member role"},
    },
    "required": ["id"],
}


class FeishuTasklistCreate(_TaskTool):
    _name = "feishu_tasklist_create"
    _description = "Create a Feishu tasklist (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Tasklist name"},
            "members": {"type": "array", "items": _TASKLIST_MEMBER, "description": "Initial members"},
            "archive_tasklist": {"type": "boolean", "description": "Whether to create as archived"},
            "user_id_type": _UID_TYPE,
        },
        "required": ["name"],
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.create_tasklist(self._client, kw))
        except Exception as e:
            return f"Error: {e}"


class FeishuTasklistGet(_TaskTool):
    _name = "feishu_tasklist_get"
    _description = "Get a Feishu tasklist by tasklist_guid (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "tasklist_guid": {"type": "string", "description": "Tasklist GUID"},
            "user_id_type": _UID_TYPE,
        },
        "required": ["tasklist_guid"],
    }

    async def execute(self, tasklist_guid: str, user_id_type: str = "", **kw: Any) -> str:
        try:
            return to_json(await actions.get_tasklist(self._client, tasklist_guid, user_id_type or None))
        except Exception as e:
            return f"Error: {e}"


class FeishuTasklistList(_TaskTool):
    _name = "feishu_tasklist_list"
    _description = "List Feishu tasklists (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Page size (1-100)"},
            "page_token": {"type": "string", "description": "Pagination token"},
            "user_id_type": _UID_TYPE,
        },
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.list_tasklists(self._client, kw))
        except Exception as e:
            return f"Error: {e}"


class FeishuTasklistUpdate(_TaskTool):
    _name = "feishu_tasklist_update"
    _description = "Update a Feishu tasklist by tasklist_guid (task v2 patch)"
    _parameters = {
        "type": "object",
        "properties": {
            "tasklist_guid": {"type": "string", "description": "Tasklist GUID to update"},
            "tasklist": {"type": "object", "description": "Tasklist fields to update (name, owner, archive_tasklist)"},
            "update_fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to update (auto-inferred if omitted)"},
            "origin_owner_to_role": {"type": "string", "enum": ["editor", "viewer", "none"], "description": "Role for original owner after transfer"},
            "user_id_type": _UID_TYPE,
        },
        "required": ["tasklist_guid", "tasklist"],
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.update_tasklist(self._client, kw))
        except Exception as e:
            return f"Error: {e}"


class FeishuTasklistDelete(_TaskTool):
    _name = "feishu_tasklist_delete"
    _description = "Delete a Feishu tasklist by tasklist_guid (task v2)"
    _parameters = {
        "type": "object",
        "properties": {"tasklist_guid": {"type": "string", "description": "Tasklist GUID to delete"}},
        "required": ["tasklist_guid"],
    }

    async def execute(self, tasklist_guid: str, **kw: Any) -> str:
        try:
            return to_json(await actions.delete_tasklist(self._client, tasklist_guid))
        except Exception as e:
            return f"Error: {e}"


class FeishuTasklistAddMembers(_TaskTool):
    _name = "feishu_tasklist_add_members"
    _description = "Add members to a Feishu tasklist (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "tasklist_guid": {"type": "string", "description": "Tasklist GUID"},
            "members": {"type": "array", "items": _TASKLIST_MEMBER, "description": "Members to add", "minItems": 1},
            "user_id_type": _UID_TYPE,
        },
        "required": ["tasklist_guid", "members"],
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.add_tasklist_members(self._client, kw))
        except Exception as e:
            return f"Error: {e}"


class FeishuTasklistRemoveMembers(_TaskTool):
    _name = "feishu_tasklist_remove_members"
    _description = "Remove members from a Feishu tasklist (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "tasklist_guid": {"type": "string", "description": "Tasklist GUID"},
            "members": {"type": "array", "items": _TASKLIST_MEMBER, "description": "Members to remove", "minItems": 1},
            "user_id_type": _UID_TYPE,
        },
        "required": ["tasklist_guid", "members"],
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.remove_tasklist_members(self._client, kw))
        except Exception as e:
            return f"Error: {e}"


# ---------------------------------------------------------------------------
# Task Comments
# ---------------------------------------------------------------------------

class FeishuTaskCommentCreate(_TaskTool):
    _name = "feishu_task_comment_create"
    _description = "Create a comment on a Feishu task (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "task_guid": {"type": "string", "description": "Task GUID"},
            "content": {"type": "string", "description": "Comment content"},
            "reply_to_comment_id": {"type": "string", "description": "Reply to comment ID (optional)"},
            "user_id_type": _UID_TYPE,
        },
        "required": ["task_guid", "content"],
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.create_task_comment(self._client, kw))
        except Exception as e:
            return f"Error: {e}"


class FeishuTaskCommentGet(_TaskTool):
    _name = "feishu_task_comment_get"
    _description = "Get a Feishu task comment by comment_id (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "comment_id": {"type": "string", "description": "Comment ID"},
            "user_id_type": _UID_TYPE,
        },
        "required": ["comment_id"],
    }

    async def execute(self, comment_id: str, user_id_type: str = "", **kw: Any) -> str:
        try:
            return to_json(await actions.get_task_comment(self._client, comment_id, user_id_type or None))
        except Exception as e:
            return f"Error: {e}"


class FeishuTaskCommentList(_TaskTool):
    _name = "feishu_task_comment_list"
    _description = "List comments for a Feishu task (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "task_guid": {"type": "string", "description": "Task GUID"},
            "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Page size (1-100)"},
            "page_token": {"type": "string", "description": "Pagination token"},
            "direction": {"type": "string", "enum": ["asc", "desc"], "description": "Sort direction"},
            "user_id_type": _UID_TYPE,
        },
        "required": ["task_guid"],
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.list_task_comments(self._client, kw))
        except Exception as e:
            return f"Error: {e}"


class FeishuTaskCommentUpdate(_TaskTool):
    _name = "feishu_task_comment_update"
    _description = "Update a Feishu task comment by comment_id (task v2 patch)"
    _parameters = {
        "type": "object",
        "properties": {
            "comment_id": {"type": "string", "description": "Comment ID to update"},
            "comment": {"type": "object", "description": "Comment fields to update (content)"},
            "update_fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to update"},
            "user_id_type": _UID_TYPE,
        },
        "required": ["comment_id", "comment"],
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.update_task_comment(self._client, kw))
        except Exception as e:
            return f"Error: {e}"


class FeishuTaskCommentDelete(_TaskTool):
    _name = "feishu_task_comment_delete"
    _description = "Delete a Feishu task comment by comment_id (task v2)"
    _parameters = {
        "type": "object",
        "properties": {"comment_id": {"type": "string", "description": "Comment ID to delete"}},
        "required": ["comment_id"],
    }

    async def execute(self, comment_id: str, **kw: Any) -> str:
        try:
            return to_json(await actions.delete_task_comment(self._client, comment_id))
        except Exception as e:
            return f"Error: {e}"


# ---------------------------------------------------------------------------
# Task Attachments
# ---------------------------------------------------------------------------

class FeishuTaskAttachmentList(_TaskTool):
    _name = "feishu_task_attachment_list"
    _description = "List attachments for a Feishu task (task v2)"
    _parameters = {
        "type": "object",
        "properties": {
            "task_guid": {"type": "string", "description": "Task GUID"},
            "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Page size (1-100)"},
            "page_token": {"type": "string", "description": "Pagination token"},
            "user_id_type": _UID_TYPE,
        },
        "required": ["task_guid"],
    }

    async def execute(self, **kw: Any) -> str:
        try:
            return to_json(await actions.list_task_attachments(self._client, kw))
        except Exception as e:
            return f"Error: {e}"


class FeishuTaskAttachmentDelete(_TaskTool):
    _name = "feishu_task_attachment_delete"
    _description = "Delete a Feishu task attachment by attachment_guid (task v2)"
    _parameters = {
        "type": "object",
        "properties": {"attachment_guid": {"type": "string", "description": "Attachment GUID to delete"}},
        "required": ["attachment_guid"],
    }

    async def execute(self, attachment_guid: str, **kw: Any) -> str:
        try:
            return to_json(await actions.delete_task_attachment(self._client, attachment_guid))
        except Exception as e:
            return f"Error: {e}"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_task_tools(client: lark.Client) -> list[Tool]:
    """Return all task tool instances."""
    return [
        FeishuTaskCreate(client),
        FeishuTaskGet(client),
        FeishuTaskUpdate(client),
        FeishuTaskDelete(client),
        FeishuTaskCreateSubtask(client),
        FeishuTaskAddTasklist(client),
        FeishuTaskRemoveTasklist(client),
        FeishuTasklistCreate(client),
        FeishuTasklistGet(client),
        FeishuTasklistList(client),
        FeishuTasklistUpdate(client),
        FeishuTasklistDelete(client),
        FeishuTasklistAddMembers(client),
        FeishuTasklistRemoveMembers(client),
        FeishuTaskCommentCreate(client),
        FeishuTaskCommentGet(client),
        FeishuTaskCommentList(client),
        FeishuTaskCommentUpdate(client),
        FeishuTaskCommentDelete(client),
        FeishuTaskAttachmentList(client),
        FeishuTaskAttachmentDelete(client),
    ]
