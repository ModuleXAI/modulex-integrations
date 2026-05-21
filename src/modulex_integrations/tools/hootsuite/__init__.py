"""Hootsuite integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.hootsuite.manifest import manifest
from modulex_integrations.tools.hootsuite.tools import (
    create_media_upload_job,
    get_media_upload_status,
    list_social_profiles,
    schedule_message,
)

TOOLS = (
    create_media_upload_job,
    get_media_upload_status,
    list_social_profiles,
    schedule_message,
)

__all__ = [
    "TOOLS",
    "create_media_upload_job",
    "get_media_upload_status",
    "list_social_profiles",
    "manifest",
    "schedule_message",
]
