---
name: feishu-wiki
description: "Manage Feishu (Lark) knowledge base spaces and wiki nodes. Use when user asks to browse wiki spaces, navigate nodes, or create/move/rename wiki pages."
---

# Feishu Wiki Tools

Use the `feishu_wiki` tool to manage Feishu knowledge bases.

## Actions

| Action | Description | Required Params |
|--------|-------------|-----------------|
| `spaces` | List all accessible knowledge spaces | (none) |
| `nodes` | List child nodes in a space/parent | `space_id` |
| `get` | Get node details (including obj_token) | `token` |
| `create` | Create a new wiki node | `space_id`, `title` |
| `move` | Move a node to another parent/space | `space_id`, `node_token` |
| `rename` | Rename a wiki node | `space_id`, `node_token`, `title` |

## Key Concepts
- **space_id**: Knowledge space ID (from `spaces` action)
- **token**: Wiki node token (from URL `/wiki/TOKEN`)
- **obj_token**: Actual document/bitable token resolved from wiki node

## Resolving Wiki URLs
When user provides `https://xxx.feishu.cn/wiki/ABC123`:
1. `feishu_wiki(action="get", token="ABC123")` → get node details
2. Check `obj_type` to determine content type
3. Use `obj_token` with `feishu_doc` or `feishu_bitable_*` tools

## Examples
```
feishu_wiki(action="spaces")
feishu_wiki(action="nodes", space_id="spaceXXX")
feishu_wiki(action="get", token="wikiXXX")
feishu_wiki(action="create", space_id="spaceXXX", title="New Page")
```
