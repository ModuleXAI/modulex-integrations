"""Microsoft Bookings integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.microsoft_bookings.manifest import manifest
from modulex_integrations.tools.microsoft_bookings.tools import (
    cancel_appointment,
    create_appointment,
    create_business,
    create_customer,
    create_service,
    create_staff_member,
    list_appointments,
    list_businesses,
    list_services,
    list_staff_members,
)

TOOLS = (
    cancel_appointment,
    create_appointment,
    create_business,
    create_customer,
    create_service,
    create_staff_member,
    list_appointments,
    list_businesses,
    list_services,
    list_staff_members,
)

__all__ = [
    "TOOLS",
    "cancel_appointment",
    "create_appointment",
    "create_business",
    "create_customer",
    "create_service",
    "create_staff_member",
    "list_appointments",
    "list_businesses",
    "list_services",
    "list_staff_members",
    "manifest",
]
