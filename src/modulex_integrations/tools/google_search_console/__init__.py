"""Google Search Console integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_search_console.manifest import manifest
from modulex_integrations.tools.google_search_console.tools import (
    retrieve_site_performance_data,
    submit_url_for_indexing,
)

TOOLS = (
    retrieve_site_performance_data,
    submit_url_for_indexing,
)

__all__ = [
    "TOOLS",
    "manifest",
    "retrieve_site_performance_data",
    "submit_url_for_indexing",
]
