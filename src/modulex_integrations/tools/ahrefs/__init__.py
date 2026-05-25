"""Ahrefs integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.ahrefs.manifest import manifest
from modulex_integrations.tools.ahrefs.tools import (
    get_backlinks,
    get_backlinks_one_per_domain,
    get_referring_domains,
)

TOOLS = (
    get_backlinks,
    get_backlinks_one_per_domain,
    get_referring_domains,
)

__all__ = [
    "TOOLS",
    "get_backlinks",
    "get_backlinks_one_per_domain",
    "get_referring_domains",
    "manifest",
]
