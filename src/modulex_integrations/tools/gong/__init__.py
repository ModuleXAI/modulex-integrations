"""Gong integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.gong.manifest import manifest
from modulex_integrations.tools.gong.tools import (
    add_new_call,
    get_extensive_data,
    list_calls,
    list_workspace_id_options,
    retrieve_transcripts_of_calls,
)

TOOLS = (
    add_new_call,
    get_extensive_data,
    list_calls,
    list_workspace_id_options,
    retrieve_transcripts_of_calls,
)

__all__ = [
    "TOOLS",
    "add_new_call",
    "get_extensive_data",
    "list_calls",
    "list_workspace_id_options",
    "manifest",
    "retrieve_transcripts_of_calls",
]
