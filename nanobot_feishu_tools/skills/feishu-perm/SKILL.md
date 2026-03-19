---
name: feishu-perm
description: "Manage Feishu file/document permissions — list, add, or remove collaborators. Use when user asks to share a document, manage permissions, or check who has access. Works with docx, sheet, bitable, folder, wiki."
---

# Feishu Permission Tool

Use the `feishu_perm` tool to manage file/document collaborators.

## Actions

| Action | Description | Required Params |
|--------|-------------|-----------------|
| `list` | List collaborators | `token`, `type` |
| `add` | Add a collaborator | `token`, `type`, `member_type`, `member_id`, `perm` |
| `remove` | Remove a collaborator | `token`, `type`, `member_type`, `member_id` |

## Token Types
`doc`, `docx`, `sheet`, `bitable`, `folder`, `file`, `wiki`, `mindnote`

## Member Types
`email`, `openid`, `userid`, `unionid`, `openchat`, `opendepartmentid`

## Permission Levels
| Level | Description |
|-------|-------------|
| `view` | View only |
| `edit` | Can edit |
| `full_access` | Full access (can manage permissions) |

## Examples

List collaborators:
```
feishu_perm(action="list", token="doxcnXXX", type="docx")
```

Share with email:
```
feishu_perm(action="add", token="doxcnXXX", type="docx", member_type="email", member_id="alice@company.com", perm="edit")
```

Share folder with group chat:
```
feishu_perm(action="add", token="fldcnXXX", type="folder", member_type="openchat", member_id="oc_xxx", perm="view")
```

Remove collaborator:
```
feishu_perm(action="remove", token="doxcnXXX", type="docx", member_type="email", member_id="alice@company.com")
```

## Required Permission
Feishu app scope: `drive:permission`
