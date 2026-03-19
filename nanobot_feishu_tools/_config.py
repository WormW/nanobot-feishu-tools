"""Configuration resolution for Feishu tools plugin.

Priority: tools.feishu > channels.feishu > environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nanobot.config.schema import Config


@dataclass(frozen=True)
class FeishuToolsSettings:
    app_id: str
    app_secret: str
    domain: str  # "feishu", "lark", or custom URL


def resolve_settings(config: Config) -> FeishuToolsSettings | None:
    """Resolve Feishu credentials from config or environment."""
    # 1. tools.feishu (explicit tools config)
    tools_cfg = config.tools.feishu
    if tools_cfg and tools_cfg.app_id and tools_cfg.app_secret:
        return FeishuToolsSettings(
            app_id=tools_cfg.app_id,
            app_secret=tools_cfg.app_secret,
            domain=tools_cfg.domain or "feishu",
        )

    # 2. channels.feishu (reuse channel credentials)
    ch = config.channels.model_extra or {}
    feishu_ch = ch.get("feishu") or {}
    if isinstance(feishu_ch, dict):
        ch_app_id = feishu_ch.get("app_id") or feishu_ch.get("appId") or ""
        ch_app_secret = feishu_ch.get("app_secret") or feishu_ch.get("appSecret") or ""
        if ch_app_id and ch_app_secret:
            return FeishuToolsSettings(
                app_id=ch_app_id,
                app_secret=ch_app_secret,
                domain="feishu",
            )

    # 3. Environment variables
    env_id = os.environ.get("FEISHU_APP_ID", "")
    env_secret = os.environ.get("FEISHU_APP_SECRET", "")
    if env_id and env_secret:
        return FeishuToolsSettings(
            app_id=env_id,
            app_secret=env_secret,
            domain=os.environ.get("FEISHU_DOMAIN", "feishu"),
        )

    return None
