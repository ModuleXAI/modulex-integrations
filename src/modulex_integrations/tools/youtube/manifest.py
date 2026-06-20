"""YouTube integration manifest.

Wraps the YouTube Data API v3
(``https://www.googleapis.com/youtube/v3``) for searching videos,
inspecting channels and playlists, and reading public comments. The API
authenticates with a public Data-API key passed as a ``key=`` query
parameter, so the integration ships a single ``api_key`` auth schema.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


_REGION_DESC = "ISO 3166-1 alpha-2 country code (e.g. 'US', 'GB', 'JP')"
_MAX_RESULTS_DESC = "Maximum number of results to return (1-50)"
_PAGE_TOKEN_DESC = "Page token for pagination (from a previous nextPageToken)"
_ORDER_DESC = "Sort order: 'date', 'rating', 'relevance', 'title', 'viewCount'"


manifest = IntegrationManifest(
    name="youtube",
    display_name="YouTube",
    description=(
        "Search YouTube videos, fetch trending videos and video details, list "
        "video categories, get channel information, channel videos and "
        "playlists, read playlist items, and retrieve video comments via the "
        "YouTube Data API v3."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:youtube",
    app_url="https://www.youtube.com",
    categories=["Social Media", "marketing", "content-management"],
    actions=[
        ActionDefinition(
            name="search",
            description=(
                "Search for videos on YouTube with advanced filtering by channel, "
                "date range, duration, category, quality, captions, and live streams."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Search query for YouTube videos",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of videos to return (1-50)",
                    default=5,
                ),
                "page_token": ParameterDef(type="string", description=_PAGE_TOKEN_DESC),
                "channel_id": ParameterDef(
                    type="string",
                    description="Filter results to a specific channel ID (starts with 'UC')",
                ),
                "published_after": ParameterDef(
                    type="string",
                    description=(
                        "Only return videos published after this RFC 3339 date "
                        "(e.g. 2024-01-01T00:00:00Z)"
                    ),
                ),
                "published_before": ParameterDef(
                    type="string",
                    description=(
                        "Only return videos published before this RFC 3339 date "
                        "(e.g. 2024-12-31T23:59:59Z)"
                    ),
                ),
                "video_duration": ParameterDef(
                    type="string",
                    description=(
                        "Filter by length: 'short' (<4 min), 'medium' (4-20 min), "
                        "'long' (>20 min), 'any'"
                    ),
                ),
                "order": ParameterDef(
                    type="string",
                    description=(
                        "Sort by: 'date', 'rating', 'relevance' (default), 'title', "
                        "'videoCount', 'viewCount'"
                    ),
                ),
                "video_category_id": ParameterDef(
                    type="string",
                    description=(
                        "Filter by category ID (e.g. '10' Music). Use video_categories "
                        "to list IDs."
                    ),
                ),
                "video_definition": ParameterDef(
                    type="string",
                    description="Filter by quality: 'high' (HD), 'standard', 'any'",
                ),
                "video_caption": ParameterDef(
                    type="string",
                    description=(
                        "Filter by captions: 'closedCaption' (has captions), "
                        "'none' (no captions), 'any'"
                    ),
                ),
                "event_type": ParameterDef(
                    type="string",
                    description="Filter by live status: 'live', 'upcoming', 'completed'",
                ),
                "region_code": ParameterDef(type="string", description=_REGION_DESC),
                "relevance_language": ParameterDef(
                    type="string",
                    description="ISO 639-1 language code for relevance (e.g. 'en', 'es')",
                ),
                "safe_search": ParameterDef(
                    type="string",
                    description="Content filtering: 'moderate' (default), 'none', 'strict'",
                ),
            },
        ),
        ActionDefinition(
            name="trending",
            description=(
                "Get the most popular/trending videos on YouTube, optionally "
                "filtered by region and video category."
            ),
            parameters={
                "region_code": ParameterDef(
                    type="string",
                    description=f"{_REGION_DESC}. Defaults to US.",
                ),
                "video_category_id": ParameterDef(
                    type="string",
                    description="Filter by category ID (e.g. '10' Music, '20' Gaming)",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of trending videos to return (1-50)",
                    default=10,
                ),
                "page_token": ParameterDef(type="string", description=_PAGE_TOKEN_DESC),
            },
        ),
        ActionDefinition(
            name="video_details",
            description=(
                "Get detailed information about a specific YouTube video including "
                "statistics, content details, live streaming info, and metadata."
            ),
            parameters={
                "video_id": ParameterDef(
                    type="string",
                    description="YouTube video ID (11-character string)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="video_categories",
            description=(
                "Get the list of video categories available on YouTube to discover "
                "valid category IDs for filtering search and trending results."
            ),
            parameters={
                "region_code": ParameterDef(
                    type="string",
                    description=f"{_REGION_DESC}. Defaults to US.",
                ),
                "hl": ParameterDef(
                    type="string",
                    description=(
                        "Language for category titles (ISO 639-1, e.g. 'en'). "
                        "Defaults to English."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="channel_info",
            description=(
                "Get detailed information about a YouTube channel including "
                "statistics, branding, and content details. Provide either "
                "channel_id or username."
            ),
            parameters={
                "channel_id": ParameterDef(
                    type="string",
                    description=(
                        "Channel ID starting with 'UC' (use either channel_id or username)"
                    ),
                ),
                "username": ParameterDef(
                    type="string",
                    description="Channel username (use either channel_id or username)",
                ),
            },
        ),
        ActionDefinition(
            name="channel_videos",
            description=(
                "Search for videos from a specific YouTube channel with sorting options."
            ),
            parameters={
                "channel_id": ParameterDef(
                    type="string",
                    description="YouTube channel ID starting with 'UC' to get videos from",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description=_MAX_RESULTS_DESC,
                    default=10,
                ),
                "order": ParameterDef(
                    type="string",
                    description=f"{_ORDER_DESC} (default 'date')",
                ),
                "page_token": ParameterDef(type="string", description=_PAGE_TOKEN_DESC),
            },
        ),
        ActionDefinition(
            name="channel_playlists",
            description="Get all public playlists from a specific YouTube channel.",
            parameters={
                "channel_id": ParameterDef(
                    type="string",
                    description="YouTube channel ID starting with 'UC' to get playlists from",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description=_MAX_RESULTS_DESC,
                    default=10,
                ),
                "page_token": ParameterDef(type="string", description=_PAGE_TOKEN_DESC),
            },
        ),
        ActionDefinition(
            name="playlist_items",
            description=(
                "Get videos from a YouTube playlist. Can be used with a channel's "
                "uploads playlist to get all of a channel's videos."
            ),
            parameters={
                "playlist_id": ParameterDef(
                    type="string",
                    description=(
                        "YouTube playlist ID. Use uploads_playlist_id from "
                        "channel_info to get all channel videos."
                    ),
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description=_MAX_RESULTS_DESC,
                    default=10,
                ),
                "page_token": ParameterDef(type="string", description=_PAGE_TOKEN_DESC),
            },
        ),
        ActionDefinition(
            name="comments",
            description=(
                "Get top-level comments from a YouTube video with author details "
                "and engagement metrics."
            ),
            parameters={
                "video_id": ParameterDef(
                    type="string",
                    description="YouTube video ID (11-character string)",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of comments to return (1-100)",
                    default=20,
                ),
                "order": ParameterDef(
                    type="string",
                    description=(
                        "Order of comments: 'time' (newest first) or 'relevance' "
                        "(most relevant first)"
                    ),
                    default="relevance",
                ),
                "page_token": ParameterDef(type="string", description=_PAGE_TOKEN_DESC),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your YouTube Data API v3 key",
            setup_instructions=[
                "Go to https://console.cloud.google.com and create or select a project",
                "Open 'APIs & Services' > 'Library' and enable the 'YouTube Data API v3'",
                "Open 'APIs & Services' > 'Credentials' and create an API key",
                "Restrict the key to the YouTube Data API v3 (recommended) and copy it",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="YOUTUBE_API_KEY",
                    display_name="YouTube API Key",
                    description="Your YouTube Data API v3 key from Google Cloud Console",
                    required=True,
                    sensitive=True,
                    sample_format="AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                    about_url="https://developers.google.com/youtube/v3/getting-started",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://www.googleapis.com/youtube/v3/videoCategories",
                method="GET",
                params={"part": "snippet", "regionCode": "US", "key": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["items"],
                ),
                cost_level="minimal",
                description="Validates the API key by listing US video categories",
            ),
        ),
    ],
)
