"""Mailgun integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.mailgun.manifest import manifest
from modulex_integrations.tools.mailgun.tools import (
    create_mailinglist_member,
    create_route,
    delete_mailinglist_member,
    list_domains,
    list_mailinglist_members,
    retrieve_mailinglist_member,
    send_email,
    suppress_email,
    verify_email,
)

TOOLS = (
    send_email,
    verify_email,
    create_mailinglist_member,
    create_route,
    delete_mailinglist_member,
    list_domains,
    list_mailinglist_members,
    retrieve_mailinglist_member,
    suppress_email,
)

__all__ = [
    "TOOLS",
    "create_mailinglist_member",
    "create_route",
    "delete_mailinglist_member",
    "list_domains",
    "list_mailinglist_members",
    "manifest",
    "retrieve_mailinglist_member",
    "send_email",
    "suppress_email",
    "verify_email",
]
