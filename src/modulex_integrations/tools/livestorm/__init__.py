"""Livestorm integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.livestorm.manifest import manifest
from modulex_integrations.tools.livestorm.tools import (
    create_event,
    get_event,
    list_attendees_from_event,
    list_events,
    list_sessions,
    register_someone_for_session,
    update_event,
)

TOOLS = (
    create_event,
    get_event,
    list_attendees_from_event,
    list_events,
    list_sessions,
    register_someone_for_session,
    update_event,
)

__all__ = [
    "TOOLS",
    "create_event",
    "get_event",
    "list_attendees_from_event",
    "list_events",
    "list_sessions",
    "manifest",
    "register_someone_for_session",
    "update_event",
]
