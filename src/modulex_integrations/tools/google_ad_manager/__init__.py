"""Google Ad Manager integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_ad_manager.manifest import manifest
from modulex_integrations.tools.google_ad_manager.tools import (
    create_report,
    list_network_options,
)

TOOLS = (
    create_report,
    list_network_options,
)

__all__ = [
    "TOOLS",
    "create_report",
    "list_network_options",
    "manifest",
]
