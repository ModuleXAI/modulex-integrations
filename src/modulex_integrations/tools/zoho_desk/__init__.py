"""Zoho Desk integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.zoho_desk.manifest import manifest
from modulex_integrations.tools.zoho_desk.tools import (
    add_comment,
    get_contact,
    get_thread,
    get_ticket,
    list_comments,
    list_organizations,
    list_threads,
    list_tickets,
    update_ticket,
)

TOOLS = (
    list_tickets,
    get_ticket,
    update_ticket,
    list_comments,
    add_comment,
    list_threads,
    get_thread,
    get_contact,
    list_organizations,
)

__all__ = [
    "TOOLS",
    "add_comment",
    "get_contact",
    "get_thread",
    "get_ticket",
    "list_comments",
    "list_organizations",
    "list_threads",
    "list_tickets",
    "manifest",
    "update_ticket",
]
