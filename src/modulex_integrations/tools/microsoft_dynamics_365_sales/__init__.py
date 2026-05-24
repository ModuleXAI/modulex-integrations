"""Microsoft Dynamics 365 Sales integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.microsoft_dynamics_365_sales.manifest import manifest
from modulex_integrations.tools.microsoft_dynamics_365_sales.tools import (
    create_appointment,
    create_custom_entity,
    find_contact,
    get_account,
    list_accounts,
    list_appointment_categories,
    list_appointment_category_options,
    list_appointments,
    list_solution_id_options,
    search_accounts,
    update_appointment,
)

TOOLS = (
    create_appointment,
    create_custom_entity,
    find_contact,
    get_account,
    list_accounts,
    list_appointment_categories,
    list_appointment_category_options,
    list_appointments,
    list_solution_id_options,
    search_accounts,
    update_appointment,
)

__all__ = [
    "TOOLS",
    "create_appointment",
    "create_custom_entity",
    "find_contact",
    "get_account",
    "list_accounts",
    "list_appointment_categories",
    "list_appointment_category_options",
    "list_appointments",
    "list_solution_id_options",
    "manifest",
    "search_accounts",
    "update_appointment",
]
