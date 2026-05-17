"""Customer.io integration."""
from modulex_integrations.tools.customerio.manifest import manifest
from modulex_integrations.tools.customerio.tools import (
    add_customers_to_segment,
    create_or_update_customer,
    send_event,
)

TOOLS = (create_or_update_customer, send_event, add_customers_to_segment)

__all__ = [
    "TOOLS",
    "add_customers_to_segment",
    "create_or_update_customer",
    "manifest",
    "send_event",
]
