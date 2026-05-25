"""Cal.com integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.cal_com.manifest import manifest
from modulex_integrations.tools.cal_com.tools import (
    create_booking,
    delete_booking,
    get_all_bookings,
    get_bookable_slots,
    get_booking,
    list_event_type_id_options,
)

TOOLS = (
    create_booking,
    delete_booking,
    get_all_bookings,
    get_bookable_slots,
    get_booking,
    list_event_type_id_options,
)

__all__ = [
    "TOOLS",
    "create_booking",
    "delete_booking",
    "get_all_bookings",
    "get_bookable_slots",
    "get_booking",
    "list_event_type_id_options",
    "manifest",
]
