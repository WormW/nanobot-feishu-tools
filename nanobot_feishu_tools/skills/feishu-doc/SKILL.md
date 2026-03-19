---
name: feishu-doc
description: "Read, write, and manage Feishu (Lark) documents. Use when user asks to read/create/edit a Feishu doc, provides a /docx/ or /wiki/ URL, or needs to manage document blocks, comments, and replies."
---

# Feishu Doc Tools

Use the `feishu_doc` tool to interact with Feishu documents.

## Actions

| Action | Description | Required Params |
|--------|-------------|-----------------|
| `read` | Read document content (markdown) | `doc_token` |
| `write` | Overwrite document content | `doc_token`, `content` |
| `append` | Append content to end of document | `doc_token`, `content` |
| `create` | Create a new empty document | `title` |
| `create_and_write` | Create and write content | `title`, `content` |
| `list_blocks` | List all blocks in a document | `doc_token` |
| `get_block` | Get a specific block | `doc_token`, `block_id` |
| `update_block` | Update a block's content | `doc_token`, `block_id`, `content` |
| `delete_block` | Delete a block | `doc_token`, `block_id` |
| `list_comments` | List comments on a document | `doc_token` |
| `create_comment` | Add a comment | `doc_token`, `content` |
| `get_comment` | Get a specific comment | `doc_token`, `comment_id` |
| `list_comment_replies` | List replies to a comment | `doc_token`, `comment_id` |

## Extracting doc_token
- From URL `https://xxx.feishu.cn/docx/ABC123`: `doc_token` = `ABC123`
- From URL `https://xxx.feishu.cn/wiki/ABC123`: use `feishu_wiki` tool to resolve first

## Content Format
- `read` returns markdown by default
- `write` and `append` accept markdown content
- Block operations use Feishu block JSON format

## Examples
```
feishu_doc(action="read", doc_token="ABC123")
feishu_doc(action="append", doc_token="ABC123", content="## New Section\n\nContent here")
feishu_doc(action="create_and_write", title="Meeting Notes", content="# Notes\n\n...")
```
