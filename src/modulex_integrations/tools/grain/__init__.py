"""Grain integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.grain.manifest import manifest
from modulex_integrations.tools.grain.tools import (
    create_hook,
    delete_hook,
    get_recording,
    get_transcript,
    list_hooks,
    list_meeting_types,
    list_recordings,
    list_teams,
    list_views,
)

TOOLS = (
    list_recordings,
    get_recording,
    get_transcript,
    list_views,
    list_teams,
    list_meeting_types,
    create_hook,
    list_hooks,
    delete_hook,
)

__all__ = [
    "TOOLS",
    "create_hook",
    "delete_hook",
    "get_recording",
    "get_transcript",
    "list_hooks",
    "list_meeting_types",
    "list_recordings",
    "list_teams",
    "list_views",
    "manifest",
]
