"""Metaphor integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.metaphor.manifest import manifest
from modulex_integrations.tools.metaphor.tools import (
    find_similar_links,
    get_documents_content,
    search,
)

TOOLS = (
    search,
    find_similar_links,
    get_documents_content,
)

__all__ = [
    "TOOLS",
    "find_similar_links",
    "get_documents_content",
    "manifest",
    "search",
]
