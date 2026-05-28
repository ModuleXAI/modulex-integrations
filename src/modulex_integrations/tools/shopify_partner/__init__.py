"""Shopify Partner integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.shopify_partner.manifest import manifest
from modulex_integrations.tools.shopify_partner.tools import (
    verify_webhook,
)

TOOLS = (verify_webhook,)

__all__ = [
    "TOOLS",
    "manifest",
    "verify_webhook",
]
