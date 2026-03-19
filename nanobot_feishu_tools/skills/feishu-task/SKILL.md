---
name: feishu-task
description: "Manage Feishu (Lark) Tasks v2 — tasks, subtasks, tasklists, comments, and attachments. Use when user asks to create/view/manage tasks, organize tasklists, or add comments to tasks."
---

# Feishu Task Tools

21 tools for managing Feishu Tasks.

## Task CRUD
```
feishu_task_create(summary="Review report", members=[{"id":"ou_xxx","role":"assignee"}])
feishu_task_get(task_guid="guid1")
feishu_task_update(task_guid="guid1", task={"summary":"Updated title"})
feishu_task_delete(task_guid="guid1")
feishu_task_subtask_create(task_guid="parent_guid", summary="Sub-item")
```

## Tasklist Management
```
feishu_tasklist_create(name="Sprint 42")
feishu_tasklist_get(tasklist_guid="list1")
feishu_tasklist_list()
feishu_tasklist_update(tasklist_guid="list1", tasklist={"name":"Renamed"})
feishu_tasklist_delete(tasklist_guid="list1")
```

## Task-Tasklist Association
```
feishu_task_add_tasklist(task_guid="t1", tasklist_guid="list1")
feishu_task_remove_tasklist(task_guid="t1", tasklist_guid="list1")
```

## Tasklist Members
```
feishu_tasklist_add_members(tasklist_guid="list1", members=[{"id":"ou_xxx","role":"editor"}])
feishu_tasklist_remove_members(tasklist_guid="list1", members=[{"id":"ou_xxx"}])
```

## Comments
```
feishu_task_comment_create(task_guid="t1", content="LGTM")
feishu_task_comment_list(task_guid="t1")
feishu_task_comment_get(comment_id="c1")
feishu_task_comment_update(comment_id="c1", comment={"content":"Updated"})
feishu_task_comment_delete(comment_id="c1")
```

## Attachments
```
feishu_task_attachment_list(task_guid="t1")
feishu_task_attachment_delete(attachment_guid="a1")
```

## Key Types
- **due/start**: `{"timestamp": "1700000000", "is_all_day": false}`
- **members**: `[{"id": "ou_xxx", "role": "assignee"}]` (roles: assignee, follower, creator)
- **tasklist members**: `[{"id": "ou_xxx", "role": "editor"}]` (roles: owner, editor, viewer)
