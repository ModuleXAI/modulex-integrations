"""HeyGen integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.heygen.manifest import manifest
from modulex_integrations.tools.heygen.tools import (
    create_talking_photo,
    create_video_from_template,
    list_custom_events_options,
    list_voice_id_options,
    retrieve_video_link,
)

TOOLS = (
    create_talking_photo,
    create_video_from_template,
    list_custom_events_options,
    list_voice_id_options,
    retrieve_video_link,
)

__all__ = [
    "TOOLS",
    "create_talking_photo",
    "create_video_from_template",
    "list_custom_events_options",
    "list_voice_id_options",
    "manifest",
    "retrieve_video_link",
]
