"""Tests for configuration resolution (3-tier priority)."""

from __future__ import annotations

import os
from unittest.mock import patch

from nanobot_feishu_tools._config import resolve_settings


def test_no_credentials(mock_config):
    """Returns None when no credentials are configured anywhere."""
    result = resolve_settings(mock_config)
    assert result is None


def test_tools_feishu_priority(mock_config_tools):
    """tools.feishu takes highest priority."""
    settings = resolve_settings(mock_config_tools)
    assert settings is not None
    assert settings.app_id == "id_from_tools"
    assert settings.app_secret == "secret_from_tools"
    assert settings.domain == "lark"


def test_channels_feishu_fallback(mock_config_channels):
    """channels.feishu used when tools.feishu is empty."""
    settings = resolve_settings(mock_config_channels)
    assert settings is not None
    assert settings.app_id == "id_from_ch"
    assert settings.app_secret == "secret_from_ch"
    assert settings.domain == "feishu"


def test_env_var_fallback(mock_config):
    """Environment variables used as last resort."""
    with patch.dict(os.environ, {"FEISHU_APP_ID": "id_env", "FEISHU_APP_SECRET": "secret_env"}):
        settings = resolve_settings(mock_config)
        assert settings is not None
        assert settings.app_id == "id_env"
        assert settings.app_secret == "secret_env"
        assert settings.domain == "feishu"


def test_env_var_custom_domain(mock_config):
    """FEISHU_DOMAIN env var sets custom domain."""
    with patch.dict(os.environ, {
        "FEISHU_APP_ID": "id_env",
        "FEISHU_APP_SECRET": "secret_env",
        "FEISHU_DOMAIN": "https://custom.example.com",
    }):
        settings = resolve_settings(mock_config)
        assert settings is not None
        assert settings.domain == "https://custom.example.com"


def test_tools_feishu_over_channels(mock_config_tools, mock_config_channels):
    """tools.feishu wins over channels.feishu when both are present."""
    # Merge channels info into the tools config
    mock_config_tools.channels = mock_config_channels.channels
    settings = resolve_settings(mock_config_tools)
    assert settings is not None
    assert settings.app_id == "id_from_tools"


def test_channels_camelcase_keys(mock_config):
    """channels.feishu supports camelCase keys (appId/appSecret)."""
    mock_config.channels.model_extra = {"feishu": {"appId": "id_camel", "appSecret": "secret_camel"}}
    settings = resolve_settings(mock_config)
    assert settings is not None
    assert settings.app_id == "id_camel"
    assert settings.app_secret == "secret_camel"
