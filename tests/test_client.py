"""Tests for Feishu client factory and caching."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from nanobot_feishu_tools._config import FeishuToolsSettings


def test_client_caching():
    """Same app_id returns the same cached client instance."""
    from nanobot_feishu_tools import _client

    # Clear cache for isolation
    _client._cache.clear()

    settings = FeishuToolsSettings(app_id="test_id", app_secret="test_secret", domain="feishu")

    with patch("nanobot_feishu_tools._client.lark") as mock_lark:
        mock_builder = MagicMock()
        mock_builder.app_id.return_value = mock_builder
        mock_builder.app_secret.return_value = mock_builder
        mock_builder.domain.return_value = mock_builder
        fake_client = MagicMock(name="FakeClient")
        mock_builder.build.return_value = fake_client
        mock_lark.Client.builder.return_value = mock_builder
        mock_lark.FEISHU_DOMAIN = "https://open.feishu.cn"
        mock_lark.LARK_DOMAIN = "https://open.larksuite.com"

        c1 = _client.get_client(settings)
        c2 = _client.get_client(settings)

        assert c1 is c2
        # builder().build() called only once
        assert mock_builder.build.call_count == 1

    _client._cache.clear()


def test_client_different_app_ids():
    """Different app_id creates separate client instances."""
    from nanobot_feishu_tools import _client

    _client._cache.clear()

    s1 = FeishuToolsSettings(app_id="id1", app_secret="s1", domain="feishu")
    s2 = FeishuToolsSettings(app_id="id2", app_secret="s2", domain="feishu")

    with patch("nanobot_feishu_tools._client.lark") as mock_lark:
        mock_builder = MagicMock()
        mock_builder.app_id.return_value = mock_builder
        mock_builder.app_secret.return_value = mock_builder
        mock_builder.domain.return_value = mock_builder
        mock_builder.build.side_effect = [MagicMock(name="c1"), MagicMock(name="c2")]
        mock_lark.Client.builder.return_value = mock_builder
        mock_lark.FEISHU_DOMAIN = "https://open.feishu.cn"
        mock_lark.LARK_DOMAIN = "https://open.larksuite.com"

        c1 = _client.get_client(s1)
        c2 = _client.get_client(s2)

        assert c1 is not c2
        assert mock_builder.build.call_count == 2

    _client._cache.clear()


def test_domain_mapping():
    """Domain mapping resolves 'feishu'/'lark' to SDK constants."""
    from nanobot_feishu_tools import _client

    _client._cache.clear()

    settings = FeishuToolsSettings(app_id="dm_test", app_secret="s", domain="lark")

    with patch("nanobot_feishu_tools._client.lark") as mock_lark:
        mock_builder = MagicMock()
        mock_builder.app_id.return_value = mock_builder
        mock_builder.app_secret.return_value = mock_builder
        mock_builder.domain.return_value = mock_builder
        mock_builder.build.return_value = MagicMock()
        mock_lark.Client.builder.return_value = mock_builder
        mock_lark.FEISHU_DOMAIN = "https://open.feishu.cn"
        mock_lark.LARK_DOMAIN = "https://open.larksuite.com"

        _client.get_client(settings)
        mock_builder.domain.assert_called_once_with("https://open.larksuite.com")

    _client._cache.clear()


def test_custom_domain():
    """Custom domain URL passed through directly."""
    from nanobot_feishu_tools import _client

    _client._cache.clear()

    settings = FeishuToolsSettings(app_id="cd_test", app_secret="s", domain="https://custom.example.com")

    with patch("nanobot_feishu_tools._client.lark") as mock_lark:
        mock_builder = MagicMock()
        mock_builder.app_id.return_value = mock_builder
        mock_builder.app_secret.return_value = mock_builder
        mock_builder.domain.return_value = mock_builder
        mock_builder.build.return_value = MagicMock()
        mock_lark.Client.builder.return_value = mock_builder
        mock_lark.FEISHU_DOMAIN = "https://open.feishu.cn"
        mock_lark.LARK_DOMAIN = "https://open.larksuite.com"

        _client.get_client(settings)
        mock_builder.domain.assert_called_once_with("https://custom.example.com")

    _client._cache.clear()
