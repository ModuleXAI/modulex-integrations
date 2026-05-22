"""Algolia integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.algolia.manifest import manifest
from modulex_integrations.tools.algolia.tools import (
    browse_records,
    delete_records,
    list_index_name_options,
    save_records,
)

TOOLS = (
    browse_records,
    delete_records,
    list_index_name_options,
    save_records,
)

__all__ = [
    "TOOLS",
    "browse_records",
    "delete_records",
    "list_index_name_options",
    "manifest",
    "save_records",
]
