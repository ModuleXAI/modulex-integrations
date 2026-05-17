"""Google Meet integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_meet.manifest import manifest
from modulex_integrations.tools.google_meet.tools import (
    list_color_id_options,
    schedule_meeting,
)

TOOLS = (
    schedule_meeting,
    list_color_id_options,
)

__all__ = [
    "TOOLS",
    "list_color_id_options",
    "manifest",
    "schedule_meeting",
]
