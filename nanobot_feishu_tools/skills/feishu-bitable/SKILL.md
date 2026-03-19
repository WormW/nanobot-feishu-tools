---
name: feishu-bitable
description: "Manage Feishu (Lark) Bitable multi-dimensional tables — fields and records CRUD. Use when user provides a /base/ or bitable URL, or asks to read/add/update/delete table rows or columns."
---

# Feishu Bitable Tools

11 tools for managing Feishu Bitable tables.

## Workflow

### Step 1: Parse URL
```
feishu_bitable_get_meta(url="https://xxx.feishu.cn/base/APP?table=tbl1")
→ { app_token, table_id }
```

### Step 2: Understand structure
```
feishu_bitable_list_fields(app_token="APP", table_id="tbl1")
```

### Step 3: Read/modify records
```
feishu_bitable_list_records(app_token="APP", table_id="tbl1")
feishu_bitable_create_record(app_token="APP", table_id="tbl1", fields={"Name": "Alice"})
feishu_bitable_update_record(app_token="APP", table_id="tbl1", record_id="rec1", fields={"Score": 100})
feishu_bitable_delete_record(app_token="APP", table_id="tbl1", record_id="rec1")
```

## Field Value Formats
| Type | Format | Example |
|------|--------|---------|
| Text | string | `"Hello"` |
| Number | number | `123` |
| SingleSelect | string | `"Option A"` |
| MultiSelect | array | `["A", "B"]` |
| DateTime | timestamp ms | `1700000000000` |
| User | array | `[{"id": "ou_xxx"}]` |
| URL | object | `{"text": "Google", "link": "https://..."}` |

## Tools
- `feishu_bitable_get_meta` — Parse URL
- `feishu_bitable_list_fields` / `create_field` / `update_field` / `delete_field` — Column ops
- `feishu_bitable_list_records` / `get_record` / `create_record` / `update_record` / `delete_record` / `batch_delete_records` — Row ops

## Pagination
`list_records`: `page_size` (1-500), `page_token` from previous response when `has_more=true`.
