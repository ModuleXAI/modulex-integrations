"""Firecrawl integration."""
from modulex_integrations.tools.firecrawl.manifest import manifest
from modulex_integrations.tools.firecrawl.tools import (
    batch_scrape,
    check_crawl_status,
    crawl,
    extract,
    map_website,
    scrape,
    search,
)

TOOLS = (
    scrape,
    map_website,
    search,
    crawl,
    check_crawl_status,
    extract,
    batch_scrape,
)

__all__ = [
    "TOOLS",
    "batch_scrape",
    "check_crawl_status",
    "crawl",
    "extract",
    "manifest",
    "map_website",
    "scrape",
    "search",
]
