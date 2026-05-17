"""Monday.com integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.monday.manifest import manifest
from modulex_integrations.tools.monday.tools import (
    create_board,
    create_column,
    create_group,
    create_item,
    create_subitem,
    create_update,
    get_board_items_page,
    get_column_values,
    get_items_by_column_value,
    list_boards,
    list_workspaces,
    update_column_values,
    update_item_name,
)

TOOLS = (
    create_board,
    create_column,
    create_group,
    create_item,
    create_subitem,
    create_update,
    get_board_items_page,
    get_column_values,
    get_items_by_column_value,
    list_boards,
    list_workspaces,
    update_column_values,
    update_item_name,
)

__all__ = [
    "TOOLS",
    "create_board",
    "create_column",
    "create_group",
    "create_item",
    "create_subitem",
    "create_update",
    "get_board_items_page",
    "get_column_values",
    "get_items_by_column_value",
    "list_boards",
    "list_workspaces",
    "manifest",
    "update_column_values",
    "update_item_name",
]
