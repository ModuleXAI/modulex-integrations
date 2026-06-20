"""YouTube integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.youtube.manifest import manifest
from modulex_integrations.tools.youtube.tools import (
    channel_info,
    channel_playlists,
    channel_videos,
    comments,
    playlist_items,
    search,
    trending,
    video_categories,
    video_details,
)

TOOLS = (
    search,
    trending,
    video_details,
    video_categories,
    channel_info,
    channel_videos,
    channel_playlists,
    playlist_items,
    comments,
)

__all__ = [
    "TOOLS",
    "channel_info",
    "channel_playlists",
    "channel_videos",
    "comments",
    "manifest",
    "playlist_items",
    "search",
    "trending",
    "video_categories",
    "video_details",
]
