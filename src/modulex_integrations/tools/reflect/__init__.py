"""Reflect integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.reflect.manifest import manifest
from modulex_integrations.tools.reflect.tools import (
    append_daily_note,
    create_link,
    get_user,
    list_graph_id_options,
    list_links,
)

TOOLS = (
    append_daily_note,
    create_link,
    get_user,
    list_graph_id_options,
    list_links,
)

__all__ = [
    "TOOLS",
    "append_daily_note",
    "create_link",
    "get_user",
    "list_graph_id_options",
    "list_links",
    "manifest",
]
