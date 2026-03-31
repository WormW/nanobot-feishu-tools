"""Feishu document actions."""

from __future__ import annotations

import re
from typing import Any

import lark_oapi as lark

from nanobot_feishu_tools._api import check_response, run_sync, to_json

BLOCK_TYPE_NAMES: dict[int, str] = {
    1: "Page", 2: "Text", 3: "Heading1", 4: "Heading2", 5: "Heading3",
    12: "Bullet", 13: "Ordered", 14: "Code", 15: "Quote", 17: "Todo",
    18: "Bitable", 21: "Diagram", 22: "Divider", 23: "File",
    27: "Image", 30: "Sheet", 31: "Table", 32: "TableCell",
}

STRUCTURED_BLOCK_TYPES = {14, 18, 21, 23, 27, 30, 31, 32}

MAX_CONTENT_LENGTH = 50000
MAX_BLOCKS_PER_INSERT = 50


def _detect_doc_format(token: str) -> str:
    """Detect legacy doc vs docx format from token."""
    if re.match(r"^doccn[a-zA-Z0-9]+$", token.strip()):
        return "doc"
    return "docx"


def _require(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value


def _build_comment_content(content: str) -> dict:
    return {
        "elements": [{"text_run": {"text": content}, "type": "text_run"}],
    }


def _clean_blocks_for_insert(blocks: list[dict]) -> tuple[list[dict], list[str]]:
    """Remove unsupported types and read-only fields from blocks."""
    skipped: list[str] = []
    cleaned: list[dict] = []
    for block in blocks:
        bt = block.get("block_type", 0)
        if bt == 32:  # TableCell - unsupported for create
            skipped.append(BLOCK_TYPE_NAMES.get(bt, f"type_{bt}"))
            continue
        b = dict(block)
        b.pop("block_id", None)
        b.pop("parent_id", None)
        b.pop("children", None)
        if bt == 31 and "table" in b:
            prop = (b["table"].get("property") or {}).copy()
            prop.pop("merge_info", None)
            b["table"] = {"property": prop}
        cleaned.append(b)
    return cleaned, skipped


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

async def action_read(client: lark.Client, doc_token: str) -> dict:
    fmt = _detect_doc_format(doc_token)
    if fmt == "doc":
        # Legacy doc format - use raw content API
        from lark_oapi.api.docx.v1 import RawContentDocumentRequest
        req = RawContentDocumentRequest.builder().document_id(doc_token).build()
        resp = await run_sync(client.docx.v1.document.raw_content, req)
        check_response(resp, "docx.v1.document.raw_content")
        return {
            "content": resp.data.content if resp.data else None,
            "format": "doc",
            "hint": "Legacy document format. Only plain text content available.",
        }

    # New docx format - get content, info, and blocks in parallel
    from lark_oapi.api.docx.v1 import (
        RawContentDocumentRequest,
        GetDocumentRequest,
        ListDocumentBlockRequest,
    )

    content_req = RawContentDocumentRequest.builder().document_id(doc_token).build()
    info_req = GetDocumentRequest.builder().document_id(doc_token).build()
    blocks_req = ListDocumentBlockRequest.builder().document_id(doc_token).build()

    content_resp = await run_sync(client.docx.v1.document.raw_content, content_req)
    check_response(content_resp, "docx.v1.document.raw_content")

    info_resp = await run_sync(client.docx.v1.document.get, info_req)
    check_response(info_resp, "docx.v1.document.get")

    blocks_resp = await run_sync(client.docx.v1.document_block.list, blocks_req)
    check_response(blocks_resp, "docx.v1.document_block.list")

    blocks = blocks_resp.data.items or [] if blocks_resp.data else []
    block_counts: dict[str, int] = {}
    structured: list[str] = []

    for b in blocks:
        bt = b.block_type or 0
        name = BLOCK_TYPE_NAMES.get(bt, f"type_{bt}")
        block_counts[name] = block_counts.get(name, 0) + 1
        if bt in STRUCTURED_BLOCK_TYPES and name not in structured:
            structured.append(name)

    result: dict[str, Any] = {
        "title": info_resp.data.document.title if info_resp.data and info_resp.data.document else None,
        "content": content_resp.data.content if content_resp.data else None,
        "revision_id": info_resp.data.document.revision_id if info_resp.data and info_resp.data.document else None,
        "block_count": len(blocks),
        "block_types": block_counts,
    }

    if structured:
        result["hint"] = (
            f"This document contains {', '.join(structured)} which are NOT included "
            f'in the plain text above. Use feishu_doc with action: "list_blocks" to get full content.'
        )

    return result


async def action_create(client: lark.Client, title: str, folder_token: str | None = None) -> dict:
    from lark_oapi.api.docx.v1 import CreateDocumentRequest, CreateDocumentRequestBody

    body = CreateDocumentRequestBody.builder().title(title)
    if folder_token:
        body = body.folder_token(folder_token)

    req = CreateDocumentRequest.builder().request_body(body.build()).build()
    resp = await run_sync(client.docx.v1.document.create, req)
    check_response(resp, "docx.v1.document.create")

    doc = resp.data.document if resp.data else None
    doc_id = doc.document_id if doc else None

    return {
        "document_id": doc_id,
        "title": doc.title if doc else None,
        "url": f"https://feishu.cn/docx/{doc_id}" if doc_id else None,
    }


async def action_write(client: lark.Client, doc_token: str, content: str) -> dict:
    """Write (overwrite) document content using markdown convert + block create."""
    from lark_oapi.api.docx.v1 import (
        ListDocumentBlockRequest,
        BatchDeleteDocumentBlockChildrenRequest,
        BatchDeleteDocumentBlockChildrenRequestBody,
    )

    # 1. Clear existing content
    list_req = ListDocumentBlockRequest.builder().document_id(doc_token).build()
    list_resp = await run_sync(client.docx.v1.document_block.list, list_req)
    check_response(list_resp, "docx.v1.document_block.list")

    existing = list_resp.data.items or [] if list_resp.data else []
    child_blocks = [b for b in existing if getattr(b, "parent_id", None) == doc_token and b.block_type != 1]
    deleted = 0

    if child_blocks:
        del_body = (
            BatchDeleteDocumentBlockChildrenRequestBody.builder()
            .start_index(0)
            .end_index(len(child_blocks))
            .build()
        )
        del_req = (
            BatchDeleteDocumentBlockChildrenRequest.builder()
            .document_id(doc_token)
            .block_id(doc_token)
            .request_body(del_body)
            .build()
        )
        del_resp = await run_sync(client.docx.v1.document_block_children.batch_delete, del_req)
        check_response(del_resp, "docx.v1.document_block_children.batch_delete")
        deleted = len(child_blocks)

    # 2. Convert markdown and insert
    blocks_added = await _convert_and_insert(client, doc_token, content)

    return {
        "success": True,
        "blocks_deleted": deleted,
        "blocks_added": blocks_added,
    }


async def action_append(client: lark.Client, doc_token: str, content: str) -> dict:
    """Append content to document."""
    blocks_added = await _convert_and_insert(client, doc_token, content)
    return {"success": True, "blocks_added": blocks_added}


async def _convert_and_insert(client: lark.Client, doc_token: str, markdown: str) -> int:
    """Convert markdown to blocks and insert into document.

    Tries the Feishu convert API first (requires docx:document.block:convert
    permission). Falls back to local markdown-to-blocks conversion.
    """
    from lark_oapi.api.docx.v1 import (
        CreateDocumentBlockChildrenRequest,
        CreateDocumentBlockChildrenRequestBody,
    )

    blocks = await _convert_markdown_to_blocks(client, markdown)
    if not blocks:
        return 0

    # Clean and insert in batches
    cleaned, _skipped = _clean_blocks_for_insert(blocks)
    if not cleaned:
        return 0

    total_inserted = 0
    for i in range(0, len(cleaned), MAX_BLOCKS_PER_INSERT):
        batch = cleaned[i:i + MAX_BLOCKS_PER_INSERT]

        body = CreateDocumentBlockChildrenRequestBody.builder().children(batch).build()
        req = (
            CreateDocumentBlockChildrenRequest.builder()
            .document_id(doc_token)
            .block_id(doc_token)
            .request_body(body)
            .build()
        )
        resp = await run_sync(client.docx.v1.document_block_children.create, req)
        check_response(resp, "docx.v1.document_block_children.create")
        children = resp.data.children if resp.data else []
        total_inserted += len(children) if children else len(batch)

    return total_inserted


async def _convert_markdown_to_blocks(client: lark.Client, markdown: str) -> list[dict]:
    """Convert markdown to Feishu blocks. Try API first, fall back to local."""
    # Try the SDK convert API
    try:
        from lark_oapi.api.docx.v1 import (
            ConvertDocumentRequest,
            ConvertDocumentRequestBody,
        )
        body = (
            ConvertDocumentRequestBody.builder()
            .content_type("markdown")
            .content(markdown)
            .build()
        )
        req = ConvertDocumentRequest.builder().request_body(body).build()
        resp = await run_sync(client.docx.v1.document.convert, req)

        if resp.success() and resp.data and resp.data.blocks:
            blocks = [to_json(b) for b in resp.data.blocks]
            first_ids = resp.data.first_level_block_ids or []
            if first_ids:
                block_map = {b.get("block_id"): b for b in blocks if b.get("block_id")}
                ordered = [block_map[bid] for bid in first_ids if bid in block_map]
                if ordered:
                    return ordered
            return blocks
    except Exception:
        pass

    # Fallback: local markdown to blocks conversion
    return _parse_markdown_to_blocks(markdown)


# ---------------------------------------------------------------------------
# Local markdown → Feishu blocks converter
# ---------------------------------------------------------------------------

_BLOCK_TYPE_MAP = {
    "text": 2, "heading1": 3, "heading2": 4, "heading3": 5,
    "bullet": 12, "ordered": 13, "code": 14, "quote": 15,
    "todo": 17, "divider": 22,
}

_CODE_LANG_MAP = {
    "python": 49, "py": 49, "go": 18, "golang": 18, "java": 25,
    "javascript": 26, "js": 26, "typescript": 67, "ts": 67,
    "bash": 3, "sh": 3, "shell": 3, "zsh": 3, "sql": 59,
    "json": 28, "yaml": 73, "yml": 73, "html": 22, "css": 9,
    "c": 6, "cpp": 7, "c++": 7, "rust": 55, "ruby": 54,
    "php": 46, "swift": 62, "kotlin": 30, "lua": 33,
    "markdown": 35, "md": 35, "xml": 72, "toml": 65,
    "dockerfile": 13, "makefile": 34, "protobuf": 52, "proto": 52,
}


def _make_text_element(text: str, style: dict | None = None) -> dict:
    """Create a single text_run element."""
    elem: dict[str, Any] = {"text_run": {"content": text}}
    if style:
        elem["text_run"]["text_element_style"] = style
    return elem


def _parse_inline(text: str) -> list[dict]:
    """Parse inline markdown (bold, italic, code, links) into text_run elements."""
    elements: list[dict] = []
    # Pattern: **bold**, *italic*, `code`, [text](url)
    pattern = re.compile(
        r'(\*\*(.+?)\*\*)'        # bold
        r'|(\*(.+?)\*)'           # italic
        r'|(`(.+?)`)'             # inline code
        r'|(\[([^\]]+)\]\(([^)]+)\))'  # link
    )
    pos = 0
    for m in pattern.finditer(text):
        # Add plain text before match
        if m.start() > pos:
            elements.append(_make_text_element(text[pos:m.start()]))

        if m.group(2):  # bold
            elements.append(_make_text_element(m.group(2), {"bold": True}))
        elif m.group(4):  # italic
            elements.append(_make_text_element(m.group(4), {"italic": True}))
        elif m.group(6):  # inline code
            elements.append(_make_text_element(m.group(6), {"inline_code": True}))
        elif m.group(8):  # link
            link_text = m.group(8) if m.group(8) else m.group(9)
            elements.append({
                "text_run": {
                    "content": link_text,
                    "text_element_style": {
                        "link": {"url": m.group(9)},
                    },
                }
            })
        pos = m.end()

    # Remaining text
    if pos < len(text):
        elements.append(_make_text_element(text[pos:]))

    return elements if elements else [_make_text_element(text)]


def _make_block(type_key: str, elements: list[dict], extra_style: dict | None = None) -> dict:
    """Create a Feishu block dict."""
    bt = _BLOCK_TYPE_MAP[type_key]
    style = extra_style or {}
    block: dict[str, Any] = {"block_type": bt}
    if type_key == "divider":
        block["divider"] = {}
    else:
        block[type_key] = {"elements": elements, "style": style}
    return block


def _parse_markdown_to_blocks(markdown: str) -> list[dict]:
    """Parse markdown text into a list of Feishu-compatible block dicts."""
    lines = markdown.split("\n")
    blocks: list[dict] = []
    i = 0

    # Skip YAML frontmatter
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            i += 1
        i += 1  # skip closing ---

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty line → skip
        if not stripped:
            i += 1
            continue

        # Divider: --- or *** or ___
        if re.match(r'^[-*_]{3,}\s*$', stripped):
            blocks.append(_make_block("divider", []))
            i += 1
            continue

        # Headings
        heading_match = re.match(r'^(#{1,3})\s+(.+)$', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            type_key = f"heading{level}"
            elements = _parse_inline(heading_match.group(2).strip())
            blocks.append(_make_block(type_key, elements))
            i += 1
            continue

        # Code block
        if stripped.startswith("```"):
            lang_str = stripped[3:].strip().lower()
            lang_code = _CODE_LANG_MAP.get(lang_str, 0)
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            code_content = "\n".join(code_lines)
            style = {"language": lang_code} if lang_code else {}
            blocks.append(_make_block("code", [_make_text_element(code_content)], style))
            continue

        # Blockquote
        if stripped.startswith("> "):
            quote_text = stripped[2:]
            elements = _parse_inline(quote_text)
            blocks.append(_make_block("quote", elements))
            i += 1
            continue

        # Bullet list
        bullet_match = re.match(r'^[-*+]\s+(.+)$', stripped)
        if bullet_match:
            elements = _parse_inline(bullet_match.group(1))
            blocks.append(_make_block("bullet", elements))
            i += 1
            continue

        # Ordered list
        ordered_match = re.match(r'^\d+[.)]\s+(.+)$', stripped)
        if ordered_match:
            elements = _parse_inline(ordered_match.group(1))
            blocks.append(_make_block("ordered", elements))
            i += 1
            continue

        # Todo list
        todo_match = re.match(r'^[-*+]\s+\[([ xX])\]\s+(.+)$', stripped)
        if todo_match:
            done = todo_match.group(1).lower() == "x"
            elements = _parse_inline(todo_match.group(2))
            style = {"done": done}
            blocks.append(_make_block("todo", elements, style))
            i += 1
            continue

        # Table → convert to text blocks (tables are complex in Feishu block API)
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = lines[i].strip()
                # Skip separator rows like |---|---|
                if not re.match(r'^\|[\s\-:|]+\|$', row):
                    table_lines.append(row)
                i += 1
            for tl in table_lines:
                cells = [c.strip() for c in tl.strip("|").split("|")]
                row_text = " | ".join(cells)
                elements = _parse_inline(row_text)
                blocks.append(_make_block("text", elements))
            continue

        # Regular paragraph
        elements = _parse_inline(stripped)
        blocks.append(_make_block("text", elements))
        i += 1

    return blocks


async def action_create_and_write(
    client: lark.Client, title: str, content: str, folder_token: str | None = None
) -> dict:
    result = await action_create(client, title, folder_token)
    doc_id = result.get("document_id")
    if not doc_id:
        raise ValueError("Document created but no document_id returned")

    write_result = await action_write(client, doc_id, content)
    return {
        "success": True,
        "document_id": doc_id,
        "title": result.get("title") or title,
        "url": result.get("url"),
        "blocks_added": write_result.get("blocks_added", 0),
    }


async def action_list_blocks(client: lark.Client, doc_token: str) -> dict:
    from lark_oapi.api.docx.v1 import ListDocumentBlockRequest

    req = ListDocumentBlockRequest.builder().document_id(doc_token).build()
    resp = await run_sync(client.docx.v1.document_block.list, req)
    check_response(resp, "docx.v1.document_block.list")

    items = resp.data.items or [] if resp.data else []
    blocks = []
    for b in items:
        blocks.append({
            "block_id": b.block_id,
            "block_type": b.block_type,
            "parent_id": b.parent_id,
        })

    return {"blocks": blocks}


async def action_get_block(client: lark.Client, doc_token: str, block_id: str) -> dict:
    from lark_oapi.api.docx.v1 import GetDocumentBlockRequest

    req = (
        GetDocumentBlockRequest.builder()
        .document_id(doc_token)
        .block_id(block_id)
        .build()
    )
    resp = await run_sync(client.docx.v1.document_block.get, req)
    check_response(resp, "docx.v1.document_block.get")

    return {"block": resp.data.block if resp.data else None}


async def action_update_block(client: lark.Client, doc_token: str, block_id: str, content: str) -> dict:
    from lark_oapi.api.docx.v1 import PatchDocumentBlockRequest, PatchDocumentBlockRequestBody

    body = (
        PatchDocumentBlockRequestBody.builder()
        .update_text_elements({"elements": [{"text_run": {"content": content}}]})
        .build()
    )
    req = (
        PatchDocumentBlockRequest.builder()
        .document_id(doc_token)
        .block_id(block_id)
        .request_body(body)
        .build()
    )
    resp = await run_sync(client.docx.v1.document_block.patch, req)
    check_response(resp, "docx.v1.document_block.patch")

    return {"success": True, "block_id": block_id}


async def action_delete_block(client: lark.Client, doc_token: str, block_id: str) -> dict:
    from lark_oapi.api.docx.v1 import (
        GetDocumentBlockRequest,
        GetDocumentBlockChildrenRequest,
        BatchDeleteDocumentBlockChildrenRequest,
        BatchDeleteDocumentBlockChildrenRequestBody,
    )

    # Get block to find parent
    get_req = (
        GetDocumentBlockRequest.builder()
        .document_id(doc_token)
        .block_id(block_id)
        .build()
    )
    get_resp = await run_sync(client.docx.v1.document_block.get, get_req)
    check_response(get_resp, "docx.v1.document_block.get")

    parent_id = (get_resp.data.block.parent_id if get_resp.data and get_resp.data.block else None) or doc_token

    # Get parent's children to find index
    children_req = (
        GetDocumentBlockChildrenRequest.builder()
        .document_id(doc_token)
        .block_id(parent_id)
        .build()
    )
    children_resp = await run_sync(client.docx.v1.document_block_children.get, children_req)
    check_response(children_resp, "docx.v1.document_block_children.get")

    items = children_resp.data.items or [] if children_resp.data else []
    index = -1
    for i, item in enumerate(items):
        if item.block_id == block_id:
            index = i
            break

    if index == -1:
        raise ValueError("Block not found in parent's children")

    del_body = (
        BatchDeleteDocumentBlockChildrenRequestBody.builder()
        .start_index(index)
        .end_index(index + 1)
        .build()
    )
    del_req = (
        BatchDeleteDocumentBlockChildrenRequest.builder()
        .document_id(doc_token)
        .block_id(parent_id)
        .request_body(del_body)
        .build()
    )
    del_resp = await run_sync(client.docx.v1.document_block_children.batch_delete, del_req)
    check_response(del_resp, "docx.v1.document_block_children.batch_delete")

    return {"success": True, "deleted_block_id": block_id}


async def action_list_comments(
    client: lark.Client, doc_token: str, page_token: str | None = None, page_size: int = 50
) -> dict:
    from lark_oapi.api.drive.v1 import ListFileCommentRequest

    builder = (
        ListFileCommentRequest.builder()
        .file_token(doc_token)
        .file_type("docx")
        .page_size(page_size)
    )
    if page_token:
        builder = builder.page_token(page_token)

    resp = await run_sync(client.drive.v1.file_comment.list, builder.build())
    check_response(resp, "drive.v1.file_comment.list")

    return {
        "comments": resp.data.items or [] if resp.data else [],
        "page_token": resp.data.page_token if resp.data else None,
        "has_more": bool(resp.data.has_more) if resp.data else False,
    }


async def action_create_comment(client: lark.Client, doc_token: str, content: str) -> dict:
    from lark_oapi.api.drive.v1 import CreateFileCommentRequest, FileComment, FileCommentReply

    reply = FileCommentReply.builder().content(_build_comment_content(content)).build()
    comment = FileComment.builder().reply_list({"replies": [reply]}).build()

    req = (
        CreateFileCommentRequest.builder()
        .file_token(doc_token)
        .file_type("docx")
        .request_body(comment)
        .build()
    )
    resp = await run_sync(client.drive.v1.file_comment.create, req)
    check_response(resp, "drive.v1.file_comment.create")

    return {
        "comment_id": resp.data.comment_id if resp.data else None,
        "comment": resp.data if resp.data else None,
    }


async def action_get_comment(client: lark.Client, doc_token: str, comment_id: str) -> dict:
    from lark_oapi.api.drive.v1 import GetFileCommentRequest

    req = (
        GetFileCommentRequest.builder()
        .file_token(doc_token)
        .comment_id(comment_id)
        .file_type("docx")
        .build()
    )
    resp = await run_sync(client.drive.v1.file_comment.get, req)
    check_response(resp, "drive.v1.file_comment.get")

    return {"comment": resp.data if resp.data else None}


async def action_list_comment_replies(
    client: lark.Client, doc_token: str, comment_id: str,
    page_token: str | None = None, page_size: int = 50,
) -> dict:
    from lark_oapi.api.drive.v1 import ListFileCommentReplyRequest

    builder = (
        ListFileCommentReplyRequest.builder()
        .file_token(doc_token)
        .comment_id(comment_id)
        .file_type("docx")
        .page_size(page_size)
    )
    if page_token:
        builder = builder.page_token(page_token)

    resp = await run_sync(client.drive.v1.file_comment_reply.list, builder.build())
    check_response(resp, "drive.v1.file_comment_reply.list")

    return {
        "replies": resp.data.items or [] if resp.data else [],
        "page_token": resp.data.page_token if resp.data else None,
        "has_more": bool(resp.data.has_more) if resp.data else False,
    }
