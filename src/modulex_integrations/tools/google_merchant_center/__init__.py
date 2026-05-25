"""Google Merchant Center integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_merchant_center.manifest import manifest
from modulex_integrations.tools.google_merchant_center.tools import (
    create_product,
    update_product,
)

TOOLS = (
    create_product,
    update_product,
)

__all__ = [
    "TOOLS",
    "create_product",
    "manifest",
    "update_product",
]
