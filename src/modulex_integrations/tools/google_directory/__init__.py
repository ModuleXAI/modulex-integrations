"""Google Directory integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_directory.manifest import manifest
from modulex_integrations.tools.google_directory.tools import (
    add_member_to_group,
    create_group,
    create_user,
    get_group,
    get_user,
    list_groups,
    list_users,
)

TOOLS = (
    add_member_to_group,
    create_group,
    create_user,
    get_group,
    get_user,
    list_groups,
    list_users,
)

__all__ = [
    "TOOLS",
    "add_member_to_group",
    "create_group",
    "create_user",
    "get_group",
    "get_user",
    "list_groups",
    "list_users",
    "manifest",
]
