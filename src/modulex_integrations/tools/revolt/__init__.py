"""Revolt integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.revolt.manifest import manifest
from modulex_integrations.tools.revolt.tools import (
    add_group_member,
    create_group,
    send_friend_request,
)

TOOLS = (
    create_group,
    add_group_member,
    send_friend_request,
)

__all__ = [
    "TOOLS",
    "add_group_member",
    "create_group",
    "manifest",
    "send_friend_request",
]
