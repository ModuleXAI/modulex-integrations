"""Google AppSheet integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_appsheet.manifest import manifest
from modulex_integrations.tools.google_appsheet.tools import (
    add_row,
    delete_row,
    get_rows,
    update_row,
)

TOOLS = (
    add_row,
    delete_row,
    get_rows,
    update_row,
)

__all__ = [
    "TOOLS",
    "add_row",
    "delete_row",
    "get_rows",
    "manifest",
    "update_row",
]
