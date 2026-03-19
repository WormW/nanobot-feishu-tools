"""Shared test fixtures for nanobot-feishu-tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Minimal stubs so tests don't need real nanobot/lark imports
# ---------------------------------------------------------------------------

@dataclass
class _FeishuToolsConfig:
    app_id: str = ""
    app_secret: str = ""
    domain: str = ""


@dataclass
class _ToolsConfig:
    feishu: _FeishuToolsConfig | None = None
    web: Any = None
    exec: Any = None
    restrict_to_workspace: bool = False
    mcp_servers: Any = None


@dataclass
class _ChannelsConfig:
    model_extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class _Config:
    tools: _ToolsConfig = field(default_factory=_ToolsConfig)
    channels: _ChannelsConfig = field(default_factory=_ChannelsConfig)


@pytest.fixture
def mock_config() -> _Config:
    """Return a minimal config with no Feishu credentials."""
    return _Config()


@pytest.fixture
def mock_config_tools() -> _Config:
    """Config with tools.feishu credentials."""
    return _Config(
        tools=_ToolsConfig(
            feishu=_FeishuToolsConfig(app_id="id_from_tools", app_secret="secret_from_tools", domain="lark"),
        )
    )


@pytest.fixture
def mock_config_channels() -> _Config:
    """Config with channels.feishu credentials."""
    return _Config(
        channels=_ChannelsConfig(model_extra={"feishu": {"app_id": "id_from_ch", "app_secret": "secret_from_ch"}}),
    )


@pytest.fixture
def mock_client() -> MagicMock:
    """Return a MagicMock standing in for lark.Client."""
    return MagicMock(name="FakeLarkClient")
