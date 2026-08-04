"""Fireflies integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.fireflies.manifest import manifest
from modulex_integrations.tools.fireflies.tools import (
    add_to_live_meeting,
    create_bite,
    delete_transcript,
    get_transcript,
    get_user,
    list_bites,
    list_contacts,
    list_transcripts,
    list_users,
    upload_audio,
)

TOOLS = (
    list_transcripts,
    get_transcript,
    get_user,
    list_users,
    upload_audio,
    delete_transcript,
    add_to_live_meeting,
    create_bite,
    list_bites,
    list_contacts,
)

__all__ = [
    "TOOLS",
    "add_to_live_meeting",
    "create_bite",
    "delete_transcript",
    "get_transcript",
    "get_user",
    "list_bites",
    "list_contacts",
    "list_transcripts",
    "list_users",
    "manifest",
    "upload_audio",
]
