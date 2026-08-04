"""Fathom integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.fathom.manifest import manifest
from modulex_integrations.tools.fathom.tools import (
    get_summary,
    get_transcript,
    list_meeting_types,
    list_meetings,
    list_team_members,
    list_teams,
)

TOOLS = (
    list_meetings,
    list_meeting_types,
    get_summary,
    get_transcript,
    list_team_members,
    list_teams,
)

__all__ = [
    "TOOLS",
    "get_summary",
    "get_transcript",
    "list_meeting_types",
    "list_meetings",
    "list_team_members",
    "list_teams",
    "manifest",
]
