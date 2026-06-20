"""Amplitude integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.amplitude.manifest import manifest
from modulex_integrations.tools.amplitude.tools import (
    event_segmentation,
    get_active_users,
    get_revenue,
    group_identify,
    identify_user,
    list_events,
    realtime_active_users,
    send_event,
    user_activity,
    user_profile,
    user_search,
)

TOOLS = (
    send_event,
    identify_user,
    group_identify,
    user_search,
    user_activity,
    user_profile,
    event_segmentation,
    get_active_users,
    realtime_active_users,
    list_events,
    get_revenue,
)

__all__ = [
    "TOOLS",
    "event_segmentation",
    "get_active_users",
    "get_revenue",
    "group_identify",
    "identify_user",
    "list_events",
    "manifest",
    "realtime_active_users",
    "send_event",
    "user_activity",
    "user_profile",
    "user_search",
]
