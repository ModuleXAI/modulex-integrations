"""Google Workspace integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_workspace.manifest import manifest
from modulex_integrations.tools.google_workspace.tools import (
    list_activities_by_admin,
    list_activities_by_event_and_admin,
    list_activities_by_event_name,
    list_all_activities,
)

TOOLS = (
    list_activities_by_admin,
    list_activities_by_event_and_admin,
    list_activities_by_event_name,
    list_all_activities,
)

__all__ = [
    "TOOLS",
    "list_activities_by_admin",
    "list_activities_by_event_and_admin",
    "list_activities_by_event_name",
    "list_all_activities",
    "manifest",
]
