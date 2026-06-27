"""Tests for the configurable source registry."""

from backend.mcp.source_registry import (
    load_sources_config,
    get_sources_by_category,
    build_source_url,
    list_all_source_names,
)


def test_sources_config_loads():
    config = load_sources_config()
    assert "sources" in config
    assert len(config["sources"]) >= 5


def test_get_news_sources():
    sources = get_sources_by_category("news")
    assert len(sources) > 0
    assert all(s.get("enabled", True) for s in sources)


def test_build_search_url():
    source = {"type": "rss_search", "template": "https://hnrss.org/newest?q={query}"}
    url = build_source_url(source, "quantum computing")
    assert "quantum" in url.lower()


def test_preferred_source_filter():
    sources = get_sources_by_category("news", preferred=["Hacker News"])
    assert len(sources) > 0
    assert any("Hacker" in s["name"] for s in sources)


def test_list_source_names():
    names = list_all_source_names()
    assert "Hacker News" in names
