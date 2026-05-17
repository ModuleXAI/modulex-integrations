"""Instacart integration."""
from modulex_integrations.tools.instacart.manifest import manifest
from modulex_integrations.tools.instacart.tools import (
    create_recipe_page,
    create_shopping_list_page,
    get_nearby_retailers,
)

TOOLS = (create_recipe_page, create_shopping_list_page, get_nearby_retailers)

__all__ = [
    "TOOLS",
    "create_recipe_page",
    "create_shopping_list_page",
    "get_nearby_retailers",
    "manifest",
]
