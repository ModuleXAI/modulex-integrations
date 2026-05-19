"""Google Tag Manager integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_tag_manager.manifest import manifest
from modulex_integrations.tools.google_tag_manager.tools import (
    create_tag,
    get_tag,
    get_tags,
    list_account_id_options,
    update_tag,
    update_variable,
)

TOOLS = (
    create_tag,
    get_tag,
    get_tags,
    list_account_id_options,
    update_tag,
    update_variable,
)

__all__ = [
    "TOOLS",
    "create_tag",
    "get_tag",
    "get_tags",
    "list_account_id_options",
    "manifest",
    "update_tag",
    "update_variable",
]
