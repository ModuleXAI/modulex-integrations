"""Mercury integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.mercury.manifest import manifest
from modulex_integrations.tools.mercury.tools import get_account_info

TOOLS = (get_account_info,)

__all__ = [
    "TOOLS",
    "get_account_info",
    "manifest",
]
