"""Scrape.do integration."""
from modulex_integrations.tools.scrape_do.manifest import manifest
from modulex_integrations.tools.scrape_do.tools import (
    get_usage_stats,
    scrape,
    scrape_to_markdown,
    scrape_with_js,
    take_screenshot,
)

TOOLS = (
    scrape,
    scrape_with_js,
    take_screenshot,
    scrape_to_markdown,
    get_usage_stats,
)

__all__ = [
    "TOOLS",
    "get_usage_stats",
    "manifest",
    "scrape",
    "scrape_to_markdown",
    "scrape_with_js",
    "take_screenshot",
]
