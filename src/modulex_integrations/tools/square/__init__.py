"""Square integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.square.manifest import manifest
from modulex_integrations.tools.square.tools import (
    create_customer,
    create_invoice,
    create_order,
    list_event_types_options,
    list_location_options,
    send_invoice,
)

TOOLS = (
    create_customer,
    create_invoice,
    create_order,
    list_event_types_options,
    list_location_options,
    send_invoice,
)

__all__ = [
    "TOOLS",
    "create_customer",
    "create_invoice",
    "create_order",
    "list_event_types_options",
    "list_location_options",
    "manifest",
    "send_invoice",
]
