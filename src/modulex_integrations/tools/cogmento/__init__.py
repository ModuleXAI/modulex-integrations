"""Cogmento integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.cogmento.manifest import manifest
from modulex_integrations.tools.cogmento.tools import (
    create_contact,
    create_deal,
    create_task,
    list_user_ids_options,
)

TOOLS = (
    create_contact,
    create_deal,
    create_task,
    list_user_ids_options,
)

__all__ = [
    "TOOLS",
    "create_contact",
    "create_deal",
    "create_task",
    "list_user_ids_options",
    "manifest",
]
