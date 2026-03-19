"""Feishu API call wrapper with error handling."""

from __future__ import annotations

import asyncio
import json
from typing import Any


class FeishuAPIError(Exception):
    """Error from Feishu API."""

    def __init__(self, context: str, code: int, msg: str, log_id: str = ""):
        self.code = code
        self.msg = msg
        self.log_id = log_id
        detail = f"{context} failed: {msg}, code={code}"
        if log_id:
            detail += f", log_id={log_id}"
        super().__init__(detail)


def check_response(response: Any, context: str) -> Any:
    """Check Feishu API response and raise on error."""
    code = getattr(response, "code", None)
    if code is None or code == 0:
        return response

    msg = getattr(response, "msg", "") or f"code {code}"
    log_id = getattr(response, "log_id", "") or ""
    raise FeishuAPIError(context, code, msg, log_id)


def to_json(data: Any) -> str:
    """Serialize data to JSON string for tool output."""
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


async def run_sync(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Run a synchronous lark-oapi call in a thread pool."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))
