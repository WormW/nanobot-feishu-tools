# nanobot-feishu-tools

Feishu/Lark tools plugin for [nanobot](https://github.com/HKUDS/nanobot) — provides native document, wiki, bitable, and task tools.

## Features

- **feishu_doc** — Read, write, append, create documents; manage blocks and comments (13 actions)
- **feishu_wiki** — Browse knowledge spaces, navigate/create/move/rename wiki nodes (6 actions)
- **feishu_bitable_\*** — 11 tools for Bitable field and record CRUD
- **feishu_task_\*** — 21 tools for Task/Tasklist/Comment/Attachment management
- **feishu_perm** — Manage file/document permissions: list, add, or remove collaborators (3 actions)

## Installation

```bash
pip install nanobot-feishu-tools
```

Or for development:

```bash
git clone https://github.com/WormW/nanobot-feishu-tools.git
cd nanobot-feishu-tools
pip install -e ".[test]"
```

## Configuration

Three methods (in priority order):

### 1. tools.feishu in nanobot config

```json
{
  "tools": {
    "feishu": {
      "app_id": "cli_xxx",
      "app_secret": "xxx",
      "domain": "feishu"
    }
  }
}
```

### 2. Reuse Feishu channel config

If `channels.feishu` is already configured, credentials are reused automatically.

### 3. Environment variables

```bash
export FEISHU_APP_ID=cli_xxx
export FEISHU_APP_SECRET=xxx
export FEISHU_DOMAIN=feishu  # optional, default "feishu"; use "lark" for Lark
```

## Usage

After installation, restart nanobot. The plugin is auto-discovered via entry points:

```
nanobot gateway
# Log: feishu-tools: Registered doc, wiki, bitable, task, perm tools
```

Then interact naturally:

- "读取飞书文档 https://xxx.feishu.cn/docx/ABC123"
- "列出这个多维表格的记录 https://xxx.feishu.cn/base/APP?table=tbl1"
- "创建一个任务：Review Q4 report"

## Feishu App Permissions

Enable these scopes in [Feishu Open Platform](https://open.feishu.cn):

| Tool Suite | Required Scopes |
|-----------|----------------|
| Doc | `docx:document`, `drive:file` |
| Wiki | `wiki:wiki` |
| Bitable | `bitable:app` |
| Task | `task:task` |
| Perm | `drive:permission` |

## Development

```bash
pip install -e ".[test]"
pytest tests/ -v
```

## License

MIT
