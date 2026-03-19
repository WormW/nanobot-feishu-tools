"""Feishu/Lark client factory with caching."""

from __future__ import annotations

import lark_oapi as lark

from nanobot_feishu_tools._config import FeishuToolsSettings

_cache: dict[str, lark.Client] = {}

_DOMAIN_MAP = {
    "feishu": lark.FEISHU_DOMAIN,
    "lark": lark.LARK_DOMAIN,
}


def get_client(settings: FeishuToolsSettings) -> lark.Client:
    """Get or create a cached Feishu client."""
    key = settings.app_id
    if key in _cache:
        return _cache[key]

    domain = _DOMAIN_MAP.get(settings.domain, settings.domain)

    client = (
        lark.Client.builder()
        .app_id(settings.app_id)
        .app_secret(settings.app_secret)
        .domain(domain)
        .build()
    )

    _cache[key] = client
    return client
