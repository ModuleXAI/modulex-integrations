"""Microsoft Entra ID integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.microsoft_entra_id.manifest import manifest
from modulex_integrations.tools.microsoft_entra_id.tools import (
    add_member_to_group,
    create_group,
    delete_group,
    get_manager,
    get_ms365_groups,
    get_organization_groups,
    get_organization_users,
    get_profile,
    remove_member_from_group,
    search_groups,
    update_group,
    update_user,
)

TOOLS = (
    add_member_to_group,
    create_group,
    delete_group,
    get_manager,
    get_ms365_groups,
    get_organization_groups,
    get_organization_users,
    get_profile,
    remove_member_from_group,
    search_groups,
    update_group,
    update_user,
)

__all__ = [
    "TOOLS",
    "add_member_to_group",
    "create_group",
    "delete_group",
    "get_manager",
    "get_ms365_groups",
    "get_organization_groups",
    "get_organization_users",
    "get_profile",
    "manifest",
    "remove_member_from_group",
    "search_groups",
    "update_group",
    "update_user",
]
