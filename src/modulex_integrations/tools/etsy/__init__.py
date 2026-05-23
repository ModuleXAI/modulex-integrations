"""Etsy integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.etsy.manifest import manifest
from modulex_integrations.tools.etsy.tools import (
    create_draft_listing_product,
    delete_listing,
    get_listing,
    get_listing_inventory,
    update_listing_inventory,
    update_listing_property,
)

TOOLS = (
    create_draft_listing_product,
    delete_listing,
    get_listing,
    get_listing_inventory,
    update_listing_inventory,
    update_listing_property,
)

__all__ = [
    "TOOLS",
    "create_draft_listing_product",
    "delete_listing",
    "get_listing",
    "get_listing_inventory",
    "manifest",
    "update_listing_inventory",
    "update_listing_property",
]
