"""
NewsMind AI - Source Registry
Loads and queries configurable news/information sources from sources.yaml.
"""

import os
from functools import lru_cache
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import yaml

from backend.utils.logging import setup_logger

logger = setup_logger("source_registry")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "sources.yaml")


@lru_cache(maxsize=1)
def load_sources_config() -> Dict[str, Any]:
    """Load and cache the sources configuration."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    logger.debug(f"Loaded {len(config.get('sources', []))} sources from config")
    return config


def reload_sources_config() -> Dict[str, Any]:
    """Force reload of sources configuration (useful in tests)."""
    load_sources_config.cache_clear()
    return load_sources_config()


def get_defaults() -> Dict[str, Any]:
    return load_sources_config().get("defaults", {})


def get_fallbacks(category: str) -> List[Dict[str, str]]:
    return load_sources_config().get("fallbacks", {}).get(category, [])


def _normalize_name(name: str) -> str:
    return name.lower().strip().replace(" ", "_").replace("-", "_")


def _matches_preferred(source: Dict[str, Any], preferred: Optional[List[str]]) -> bool:
    if not preferred:
        return True
    source_id = _normalize_name(source.get("id", ""))
    source_name = _normalize_name(source.get("name", ""))
    for pref in preferred:
        pref_norm = _normalize_name(pref)
        if pref_norm in (source_id, source_name) or pref_norm in source_id or pref_norm in source_name:
            return True
        # Partial match for user-friendly names like "Hacker News" vs id "hacker_news"
        if source_name.replace("_", " ") in pref.lower() or pref.lower() in source_name.replace("_", " "):
            return True
    return False


def get_sources_by_category(
    category: str,
    preferred: Optional[List[str]] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return enabled sources for a category, sorted by priority."""
    config = load_sources_config()
    max_sources = limit or config.get("defaults", {}).get("max_sources_per_query", 8)

    sources = [
        s for s in config.get("sources", [])
        if s.get("category") == category and s.get("enabled", True)
        and _matches_preferred(s, preferred)
    ]
    sources.sort(key=lambda s: s.get("priority", 99))
    return sources[:max_sources]


def build_source_url(source: Dict[str, Any], query: str) -> Optional[str]:
    """Build a fetch URL from a source definition and search query."""
    source_type = source.get("type", "rss")

    if source_type == "rss":
        return source.get("url")

    if source_type == "rss_search":
        template = source.get("template", "")
        if not template:
            return None
        encoded = quote_plus(query.strip())
        slug = query.strip().lower().replace(" ", "-")
        return template.format(query=encoded, slug=slug)

    return None


def list_all_source_names() -> List[str]:
    """Return display names of all enabled sources."""
    config = load_sources_config()
    return [s["name"] for s in config.get("sources", []) if s.get("enabled", True)]
