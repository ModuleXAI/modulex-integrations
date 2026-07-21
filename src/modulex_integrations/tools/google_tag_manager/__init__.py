"""Google Tag Manager integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_tag_manager.manifest import manifest
from modulex_integrations.tools.google_tag_manager.tools import (
    get_tag,
    get_tags,
    list_account_id_options,
)

TOOLS = (
    get_tag,
    get_tags,
    list_account_id_options,
)

__all__ = [
    "TOOLS",
    "get_tag",
    "get_tags",
    "list_account_id_options",
    "manifest",
]
