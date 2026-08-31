"""Esup-Pod - Tests for search configuration."""

from src.apps.search.conf import SearchConfig


def test_search_config_defaults():
    """Verify default search settings."""
    config = SearchConfig()
    assert config.search_engine == "redis"
    assert config.search_index_name == "pod_videos"
    assert config.search_max_retries == 3
    assert config.search_enable_facets is True
    assert config.search_enable_auto_index is True


def test_search_config_is_redis():
    """Verify is_redis property logic."""
    config = SearchConfig(search_engine="redis")
    assert config.is_redis is True
    assert config.is_disabled is False


def test_search_config_is_disabled():
    """Verify is_disabled property logic."""
    config = SearchConfig(search_engine="disabled")
    assert config.is_redis is False
    assert config.is_disabled is True
