---
name: feishu-perm
description: "Manage Feishu file/document permissions — list, add, or remove collaborators. Use when user asks to share a document, manage permissions, or check who has access. Works with docx, sheet, bitable, folder, wiki."
---

# Feishu Permission Tool

Use the `feishu_perm` tool to manage file/document collaborators.

## Actions

| Action | Description | Required Params |
|--------|-------------|-----------------|
| `list` | List collaborators | `token`, `token_type` |
| `add` | Add a collaborator | `token`, `token_type`, `member_entity_type`, `member_type`, `member_id`, `perm` |
| `remove` | Remove a collaborator | `token`, `token_type`, `member_entity_type`, `member_type`, `member_id` |

## Token Types (`token_type`)
File/document type: `doc`, `docx`, `sheet`, `bitable`, `folder`, `file`, `wiki`, `mindnote`

## Member Entity Types (`member_entity_type`)
What kind of entity is being granted permission:

| Type | Description |
|------|-------------|
| `user` | Individual user |
| `chat` | Group chat |
| `department` | Department |
| `group` | User group |
| `wiki_space_member` | Wiki space member |
| `wiki_space_viewer` | Wiki space viewer |
| `wiki_space_editor` | Wiki space editor |

## Member ID Types (`member_type`)
How the member is identified:
`email`, `openid`, `userid`, `unionid`, `openchat`, `opendepartmentid`

## Permission Levels (`perm`)
| Level | Description |
|-------|-------------|
| `view` | View only |
| `edit` | Can edit |
| `full_access` | Full access (can manage permissions) |

## Examples

List collaborators:
```
feishu_perm(action="list", token="doxcnXXX", token_type="docx")
```

Share with a user by email:
```
feishu_perm(action="add", token="doxcnXXX", token_type="docx", member_entity_type="user", member_type="email", member_id="alice@company.com", perm="edit")
```

Share with a user by openid:
```
feishu_perm(action="add", token="doxcnXXX", token_type="docx", member_entity_type="user", member_type="openid", member_id="ou_xxx", perm="view")
```

Share folder with group chat:
```
feishu_perm(action="add", token="fldcnXXX", token_type="folder", member_entity_type="chat", member_type="openchat", member_id="oc_xxx", perm="view")
```

Remove collaborator:
```
feishu_perm(action="remove", token="doxcnXXX", token_type="docx", member_entity_type="user", member_type="email", member_id="alice@company.com")
```

## Required Permission
Feishu app scope: `drive:permission`
