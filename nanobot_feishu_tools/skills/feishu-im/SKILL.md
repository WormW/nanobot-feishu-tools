---
name: feishu-im
description: "Feishu IM tool — read chat history and list groups. Use when user asks to summarize chat conversations, pull group history, or review recent discussions in Feishu."
---

# Feishu IM Tool (`feishu_im`)

## Quick Reference

### action="list_chats" — List bot's groups
```
feishu_im(action="list_chats")
feishu_im(action="list_chats", page_size="50", page_token="<token>")
```

### action="get_chat" — Get group details
```
feishu_im(action="get_chat", chat_id="oc_xxx")
```

### action="list_messages" — Pull chat history
```
feishu_im(action="list_messages", chat_id="oc_xxx")
feishu_im(action="list_messages", chat_id="oc_xxx", start_time="1700000000", end_time="1700086400", sort_type="ByCreateTimeDesc", page_size="50")
```

### action="get_message" — Get single message detail
```
feishu_im(action="get_message", message_id="om_xxx")
```

## ID Format

| ID Type | Prefix | Example |
|---------|--------|---------|
| chat_id | `oc_` | `oc_a1b2c3d4e5f6` |
| message_id | `om_` | `om_a1b2c3d4e5f6` |

## Time Parameters

- `start_time` / `end_time`: Unix timestamp **in seconds** (not milliseconds)
- Example: `"1700000000"` = 2023-11-15 00:53:20 UTC
- Omit both to get the latest messages

## Typical Scenarios

### Summarize recent group chat
1. `list_chats` → find the target group's `chat_id`
2. `list_messages(chat_id="oc_xxx", sort_type="ByCreateTimeDesc", page_size="50")` → pull recent messages
3. Summarize the returned messages

### Pull messages in a time range
```
feishu_im(action="list_messages", chat_id="oc_xxx", start_time="1700000000", end_time="1700086400")
```

### Paginate through all messages
1. First call: `list_messages(chat_id="oc_xxx", page_size="50")`
2. If `has_more=true`, use returned `page_token` for next page
3. Repeat until `has_more=false`

## Sort Options

| Value | Description |
|-------|-------------|
| `ByCreateTimeAsc` | Oldest first (default) |
| `ByCreateTimeDesc` | Newest first |
