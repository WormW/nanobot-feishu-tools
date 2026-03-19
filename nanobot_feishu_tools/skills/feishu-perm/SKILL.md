---
name: feishu-perm
description: "Manage Feishu file/document permissions — list, add, or remove collaborators. Use when user asks to share a document, manage permissions, or check who has access. Works with docx, sheet, bitable, folder, wiki."
---

# Feishu Permission Tool (`feishu_perm`)

**IMPORTANT**: Parameter names are `token_type` (NOT `type`), `member_entity_type` (NOT `member_type` alone). All parameters below must use their exact names.

## Quick Reference

### action="list" — List collaborators
```json
feishu_perm(action="list", token="<file_token>", token_type="<docx|sheet|...>")
```

### action="add" — Add a collaborator (ALL 6 params required)
```json
feishu_perm(action="add", token="<file_token>", token_type="<docx|sheet|...>", member_entity_type="<user|chat|...>", member_type="<email|openid|...>", member_id="<actual_id>", perm="<view|edit|full_access>")
```

### action="remove" — Remove a collaborator (ALL 5 params required)
```json
feishu_perm(action="remove", token="<file_token>", token_type="<docx|sheet|...>", member_entity_type="<user|chat|...>", member_type="<email|openid|...>", member_id="<actual_id>")
```

## Parameter Details

### `token` — File/document token
Extract from URL: `https://xxx.feishu.cn/docx/ABC123` → token is `ABC123`

### `token_type` — Document type (NOT named `type`)
| Value | Description |
|-------|-------------|
| `docx` | New document |
| `doc` | Old document |
| `sheet` | Spreadsheet |
| `bitable` | Multi-dimensional table |
| `folder` | Folder |
| `file` | Uploaded file |
| `wiki` | Wiki node |
| `mindnote` | Mind map |

### `member_entity_type` — What kind of entity receives permission
| Value | When to use | Typical `member_type` |
|-------|-------------|----------------------|
| `user` | Sharing with a person | `email`, `openid`, `userid`, `unionid` |
| `chat` | Sharing with a group chat | `openchat` |
| `department` | Sharing with a department | `opendepartmentid` |
| `group` | Sharing with a user group | `openid` |

### `member_type` — How to identify the member
Choose based on the ID format:

| `member_type` | ID prefix/format | Example |
|---------------|-----------------|---------|
| `openid` | `ou_` prefix | `ou_c54e1f6b04eebb703c6effc88e207635` |
| `userid` | no standard prefix | `a]g9241` |
| `unionid` | `on_` prefix | `on_abc123def456` |
| `email` | email format | `alice@company.com` |
| `openchat` | `oc_` prefix | `oc_abc123` |
| `opendepartmentid` | `od_` prefix | `od_abc123` |

**IMPORTANT**: `ou_` prefix IDs must use `member_type="openid"`, NOT `"userid"`.

### `perm` — Permission level
`view` (read only), `edit` (can edit), `full_access` (can manage permissions)

## Complete Examples

Share a docx with a user by email:
```json
feishu_perm(action="add", token="doxcnABC123", token_type="docx", member_entity_type="user", member_type="email", member_id="alice@company.com", perm="edit")
```

Share a docx with a user by openid:
```json
feishu_perm(action="add", token="doxcnABC123", token_type="docx", member_entity_type="user", member_type="openid", member_id="ou_c54e1f6b04eebb703c6effc88e207635", perm="view")
```

Share a folder with a group chat:
```json
feishu_perm(action="add", token="fldcnXXX", token_type="folder", member_entity_type="chat", member_type="openchat", member_id="oc_xxx", perm="view")
```

List all collaborators of a document:
```json
feishu_perm(action="list", token="doxcnABC123", token_type="docx")
```

Remove a collaborator:
```json
feishu_perm(action="remove", token="doxcnABC123", token_type="docx", member_entity_type="user", member_type="email", member_id="alice@company.com")
```
