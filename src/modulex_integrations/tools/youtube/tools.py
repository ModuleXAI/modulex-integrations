"""YouTube LangChain ``@tool`` functions.

Nine async tools wrapping the YouTube Data API v3
(``https://www.googleapis.com/youtube/v3``). The modulex
``ToolExecutor`` injects an ``api_key: str`` directly (resolved from the
user's API-key credential), not an ``auth_type``/``auth_data`` pair.

The YouTube Data API v3 authenticates with an API key passed as a
``key=`` **query parameter**, not an ``Authorization`` header — every
request sets ``params["key"] = api_key``.

Error model: the API returns HTTP 200 with an ``{"error": {...}}``
envelope on failure. Each function inspects ``data["error"]`` and
returns ``success=False`` + the upstream ``error.message`` rather than
raising. Non-2xx HTTP responses, timeouts, and unexpected exceptions are
likewise caught and surfaced as ``success=False`` + ``error``.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.youtube.outputs import (
    ChannelInfoOutput,
    ChannelPlaylistsOutput,
    ChannelVideoItem,
    ChannelVideosOutput,
    CommentItem,
    CommentsOutput,
    PlaylistItem,
    PlaylistItemsOutput,
    PlaylistSummary,
    SearchItem,
    SearchOutput,
    TrendingItem,
    TrendingOutput,
    VideoCategoriesOutput,
    VideoCategoryItem,
    VideoDetailsOutput,
)

__all__ = [
    "channel_info",
    "channel_playlists",
    "channel_videos",
    "comments",
    "playlist_items",
    "search",
    "trending",
    "video_categories",
    "video_details",
]

_API_BASE = "https://www.googleapis.com/youtube/v3"
_TIMEOUT = 30.0
_EMPTY_KEY_ERROR = (
    "YouTube API key is empty. Please configure a valid YouTube API credential."
)


# --- Helpers ---------------------------------------------------------------


def _to_int(value: Any) -> int | None:
    """Coerce a YouTube statistic (which arrives as a numeric string) to int."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _best_thumbnail(snippet: dict[str, Any], *, order: list[str]) -> str:
    thumbs = snippet.get("thumbnails") or {}
    for size in order:
        url = (thumbs.get(size) or {}).get("url")
        if url:
            return str(url)
    return ""


# --- Input schemas (args_schema for each @tool) ----------------------------


class SearchInput(BaseModel):
    query: str = Field(description="Search query for YouTube videos")
    api_key: str = Field(description="YouTube API key (provided by credential system)")
    max_results: int = Field(default=5, description="Maximum number of videos to return (1-50)")
    page_token: str | None = Field(
        default=None, description="Page token for pagination (from a previous nextPageToken)"
    )
    channel_id: str | None = Field(
        default=None, description="Filter results to a specific channel ID (starts with 'UC')"
    )
    published_after: str | None = Field(
        default=None,
        description=(
            "Only return videos published after this RFC 3339 date "
            "(e.g. 2024-01-01T00:00:00Z)"
        ),
    )
    published_before: str | None = Field(
        default=None,
        description=(
            "Only return videos published before this RFC 3339 date "
            "(e.g. 2024-12-31T23:59:59Z)"
        ),
    )
    video_duration: str | None = Field(
        default=None,
        description=(
            "Filter by length: 'short' (<4 min), 'medium' (4-20 min), "
            "'long' (>20 min), 'any'"
        ),
    )
    order: str | None = Field(
        default=None,
        description=(
            "Sort by: 'date', 'rating', 'relevance' (default), 'title', "
            "'videoCount', 'viewCount'"
        ),
    )
    video_category_id: str | None = Field(
        default=None,
        description=(
            "Filter by category ID (e.g. '10' Music). Use video_categories to list IDs."
        ),
    )
    video_definition: str | None = Field(
        default=None, description="Filter by quality: 'high' (HD), 'standard', 'any'"
    )
    video_caption: str | None = Field(
        default=None,
        description=(
            "Filter by captions: 'closedCaption' (has captions), "
            "'none' (no captions), 'any'"
        ),
    )
    event_type: str | None = Field(
        default=None,
        description="Filter by live status: 'live', 'upcoming', 'completed'",
    )
    region_code: str | None = Field(
        default=None, description="ISO 3166-1 alpha-2 country code (e.g. 'US', 'GB')"
    )
    relevance_language: str | None = Field(
        default=None, description="ISO 639-1 language code for relevance (e.g. 'en', 'es')"
    )
    safe_search: str | None = Field(
        default=None, description="Content filtering: 'moderate' (default), 'none', 'strict'"
    )


class TrendingInput(BaseModel):
    api_key: str = Field(description="YouTube API key (provided by credential system)")
    region_code: str | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code (e.g. 'US', 'GB', 'JP'). Defaults to US.",
    )
    video_category_id: str | None = Field(
        default=None, description="Filter by category ID (e.g. '10' Music, '20' Gaming)"
    )
    max_results: int = Field(
        default=10, description="Maximum number of trending videos to return (1-50)"
    )
    page_token: str | None = Field(
        default=None, description="Page token for pagination (from a previous nextPageToken)"
    )


class VideoDetailsInput(BaseModel):
    video_id: str = Field(description="YouTube video ID (11-character string)")
    api_key: str = Field(description="YouTube API key (provided by credential system)")


class VideoCategoriesInput(BaseModel):
    api_key: str = Field(description="YouTube API key (provided by credential system)")
    region_code: str | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code (e.g. 'US', 'GB'). Defaults to US.",
    )
    hl: str | None = Field(
        default=None,
        description=(
            "Language for category titles (ISO 639-1, e.g. 'en'). Defaults to English."
        ),
    )


class ChannelInfoInput(BaseModel):
    api_key: str = Field(description="YouTube API key (provided by credential system)")
    channel_id: str | None = Field(
        default=None,
        description="Channel ID starting with 'UC' (use either channel_id or username)",
    )
    username: str | None = Field(
        default=None, description="Channel username (use either channel_id or username)"
    )


class ChannelVideosInput(BaseModel):
    channel_id: str = Field(description="YouTube channel ID starting with 'UC' to get videos from")
    api_key: str = Field(description="YouTube API key (provided by credential system)")
    max_results: int = Field(default=10, description="Maximum number of videos to return (1-50)")
    order: str | None = Field(
        default=None,
        description="Sort order: 'date' (default), 'rating', 'relevance', 'title', 'viewCount'",
    )
    page_token: str | None = Field(
        default=None, description="Page token for pagination (from a previous nextPageToken)"
    )


class ChannelPlaylistsInput(BaseModel):
    channel_id: str = Field(
        description="YouTube channel ID starting with 'UC' to get playlists from"
    )
    api_key: str = Field(description="YouTube API key (provided by credential system)")
    max_results: int = Field(default=10, description="Maximum number of playlists to return (1-50)")
    page_token: str | None = Field(
        default=None, description="Page token for pagination (from a previous nextPageToken)"
    )


class PlaylistItemsInput(BaseModel):
    playlist_id: str = Field(
        description="YouTube playlist ID (e.g. starts with 'PL' or 'UU'). "
        "Use uploads_playlist_id from channel_info to get all channel videos."
    )
    api_key: str = Field(description="YouTube API key (provided by credential system)")
    max_results: int = Field(default=10, description="Maximum number of videos to return (1-50)")
    page_token: str | None = Field(
        default=None, description="Page token for pagination (from a previous nextPageToken)"
    )


class CommentsInput(BaseModel):
    video_id: str = Field(description="YouTube video ID (11-character string)")
    api_key: str = Field(description="YouTube API key (provided by credential system)")
    max_results: int = Field(default=20, description="Maximum number of comments to return (1-100)")
    order: str = Field(
        default="relevance",
        description="Order of comments: 'time' (newest first) or 'relevance' (most relevant first)",
    )
    page_token: str | None = Field(
        default=None, description="Page token for pagination (from a previous nextPageToken)"
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(
    query: str,
    api_key: str,
    max_results: int = 5,
    page_token: str | None = None,
    channel_id: str | None = None,
    published_after: str | None = None,
    published_before: str | None = None,
    video_duration: str | None = None,
    order: str | None = None,
    video_category_id: str | None = None,
    video_definition: str | None = None,
    video_caption: str | None = None,
    event_type: str | None = None,
    region_code: str | None = None,
    relevance_language: str | None = None,
    safe_search: str | None = None,
) -> SearchOutput:
    """Search for videos on YouTube with advanced filtering by channel, date range,
    duration, category, quality, captions, live streams, and more."""
    if not api_key or not api_key.strip():
        return SearchOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {
        "part": "snippet",
        "type": "video",
        "key": api_key,
        "q": query,
        "maxResults": max_results or 5,
    }
    if page_token:
        params["pageToken"] = page_token
    if channel_id:
        params["channelId"] = channel_id
    if published_after:
        params["publishedAfter"] = published_after
    if published_before:
        params["publishedBefore"] = published_before
    if video_duration:
        params["videoDuration"] = video_duration
    if order:
        params["order"] = order
    if video_category_id:
        params["videoCategoryId"] = video_category_id
    if video_definition:
        params["videoDefinition"] = video_definition
    if video_caption:
        params["videoCaption"] = video_caption
    if event_type:
        params["eventType"] = event_type
    if region_code:
        params["regionCode"] = region_code
    if relevance_language:
        params["relevanceLanguage"] = relevance_language
    if safe_search:
        params["safeSearch"] = safe_search

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_API_BASE}/search", params=params)
        if response.status_code != 200:
            return SearchOutput(
                success=False,
                error=f"YouTube API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchOutput(success=False, error=f"Search failed: {exc}")

    if data.get("error"):
        return SearchOutput(
            success=False, error=data["error"].get("message") or "Search failed"
        )

    items: list[SearchItem] = []
    for item in data.get("items") or []:
        snippet = item.get("snippet") or {}
        items.append(
            SearchItem(
                video_id=(item.get("id") or {}).get("videoId") or "",
                title=snippet.get("title") or "",
                description=snippet.get("description") or "",
                thumbnail=_best_thumbnail(snippet, order=["default", "medium", "high"]),
                channel_id=snippet.get("channelId") or "",
                channel_title=snippet.get("channelTitle") or "",
                published_at=snippet.get("publishedAt") or "",
                live_broadcast_content=snippet.get("liveBroadcastContent") or "none",
            )
        )

    page_info = data.get("pageInfo") or {}
    return SearchOutput(
        success=True,
        items=items,
        total_results=page_info.get("totalResults") or 0,
        next_page_token=data.get("nextPageToken"),
    )


@tool(args_schema=TrendingInput)
@serialize_pydantic_return
async def trending(
    api_key: str,
    region_code: str | None = None,
    video_category_id: str | None = None,
    max_results: int = 10,
    page_token: str | None = None,
) -> TrendingOutput:
    """Get the most popular/trending videos on YouTube, optionally filtered by
    region and video category."""
    if not api_key or not api_key.strip():
        return TrendingOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {
        "part": "snippet,statistics,contentDetails",
        "chart": "mostPopular",
        "key": api_key,
        "maxResults": max_results or 10,
        "regionCode": region_code or "US",
    }
    if video_category_id:
        params["videoCategoryId"] = video_category_id
    if page_token:
        params["pageToken"] = page_token

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_API_BASE}/videos", params=params)
        if response.status_code != 200:
            return TrendingOutput(
                success=False,
                error=f"YouTube API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return TrendingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return TrendingOutput(success=False, error=f"Failed to fetch trending videos: {exc}")

    if data.get("error"):
        return TrendingOutput(
            success=False,
            error=data["error"].get("message") or "Failed to fetch trending videos",
        )

    items: list[TrendingItem] = []
    for item in data.get("items") or []:
        snippet = item.get("snippet") or {}
        statistics = item.get("statistics") or {}
        content_details = item.get("contentDetails") or {}
        items.append(
            TrendingItem(
                video_id=item.get("id") or "",
                title=snippet.get("title") or "",
                description=snippet.get("description") or "",
                thumbnail=_best_thumbnail(snippet, order=["high", "medium", "default"]),
                channel_id=snippet.get("channelId") or "",
                channel_title=snippet.get("channelTitle") or "",
                published_at=snippet.get("publishedAt") or "",
                view_count=_to_int(statistics.get("viewCount")) or 0,
                like_count=_to_int(statistics.get("likeCount")) or 0,
                comment_count=_to_int(statistics.get("commentCount")) or 0,
                duration=content_details.get("duration") or "",
            )
        )

    page_info = data.get("pageInfo") or {}
    return TrendingOutput(
        success=True,
        items=items,
        total_results=page_info.get("totalResults") or len(items),
        next_page_token=data.get("nextPageToken"),
    )


@tool(args_schema=VideoDetailsInput)
@serialize_pydantic_return
async def video_details(video_id: str, api_key: str) -> VideoDetailsOutput:
    """Get detailed information about a specific YouTube video including
    statistics, content details, live streaming info, and metadata."""
    if not api_key or not api_key.strip():
        return VideoDetailsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {
        "part": "snippet,statistics,contentDetails,status,liveStreamingDetails",
        "id": video_id,
        "key": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_API_BASE}/videos", params=params)
        if response.status_code != 200:
            return VideoDetailsOutput(
                success=False,
                error=f"YouTube API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return VideoDetailsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return VideoDetailsOutput(success=False, error=f"Failed to fetch video details: {exc}")

    if data.get("error"):
        return VideoDetailsOutput(
            success=False,
            error=data["error"].get("message") or "Failed to fetch video details",
        )

    api_items = data.get("items") or []
    if not api_items:
        return VideoDetailsOutput(success=False, error="Video not found")

    item = api_items[0]
    snippet = item.get("snippet") or {}
    statistics = item.get("statistics") or {}
    content_details = item.get("contentDetails") or {}
    status = item.get("status") or {}
    live_details = item.get("liveStreamingDetails")

    return VideoDetailsOutput(
        success=True,
        video_id=item.get("id") or "",
        title=snippet.get("title") or "",
        description=snippet.get("description") or "",
        channel_id=snippet.get("channelId") or "",
        channel_title=snippet.get("channelTitle") or "",
        published_at=snippet.get("publishedAt") or "",
        duration=content_details.get("duration") or "",
        view_count=_to_int(statistics.get("viewCount")) or 0,
        like_count=_to_int(statistics.get("likeCount")) or 0,
        comment_count=_to_int(statistics.get("commentCount")) or 0,
        favorite_count=_to_int(statistics.get("favoriteCount")) or 0,
        thumbnail=_best_thumbnail(snippet, order=["high", "medium", "default"]),
        tags=snippet.get("tags") or [],
        category_id=snippet.get("categoryId"),
        definition=content_details.get("definition"),
        caption=content_details.get("caption"),
        licensed_content=content_details.get("licensedContent"),
        privacy_status=status.get("privacyStatus"),
        live_broadcast_content=snippet.get("liveBroadcastContent"),
        default_language=snippet.get("defaultLanguage"),
        default_audio_language=snippet.get("defaultAudioLanguage"),
        is_live_content=live_details is not None,
        scheduled_start_time=(live_details or {}).get("scheduledStartTime"),
        actual_start_time=(live_details or {}).get("actualStartTime"),
        actual_end_time=(live_details or {}).get("actualEndTime"),
        concurrent_viewers=_to_int((live_details or {}).get("concurrentViewers")),
        active_live_chat_id=(live_details or {}).get("activeLiveChatId"),
    )


@tool(args_schema=VideoCategoriesInput)
@serialize_pydantic_return
async def video_categories(
    api_key: str,
    region_code: str | None = None,
    hl: str | None = None,
) -> VideoCategoriesOutput:
    """Get the list of video categories available on YouTube. Use this to discover
    valid category IDs for filtering search and trending results."""
    if not api_key or not api_key.strip():
        return VideoCategoriesOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {
        "part": "snippet",
        "key": api_key,
        "regionCode": region_code or "US",
    }
    if hl:
        params["hl"] = hl

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_API_BASE}/videoCategories", params=params)
        if response.status_code != 200:
            return VideoCategoriesOutput(
                success=False,
                error=f"YouTube API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return VideoCategoriesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return VideoCategoriesOutput(
            success=False, error=f"Failed to fetch video categories: {exc}"
        )

    if data.get("error"):
        return VideoCategoriesOutput(
            success=False,
            error=data["error"].get("message") or "Failed to fetch video categories",
        )

    items: list[VideoCategoryItem] = []
    for item in data.get("items") or []:
        snippet = item.get("snippet") or {}
        if snippet.get("assignable") is False:
            continue
        items.append(
            VideoCategoryItem(
                category_id=item.get("id") or "",
                title=snippet.get("title") or "",
                assignable=snippet.get("assignable") or False,
            )
        )

    return VideoCategoriesOutput(success=True, items=items, total_results=len(items))


@tool(args_schema=ChannelInfoInput)
@serialize_pydantic_return
async def channel_info(
    api_key: str,
    channel_id: str | None = None,
    username: str | None = None,
) -> ChannelInfoOutput:
    """Get detailed information about a YouTube channel including statistics,
    branding, and content details. Provide either channel_id or username."""
    if not api_key or not api_key.strip():
        return ChannelInfoOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {
        "part": "snippet,statistics,contentDetails,brandingSettings",
        "key": api_key,
    }
    if channel_id:
        params["id"] = channel_id
    elif username:
        params["forUsername"] = username

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_API_BASE}/channels", params=params)
        if response.status_code != 200:
            return ChannelInfoOutput(
                success=False,
                error=f"YouTube API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ChannelInfoOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ChannelInfoOutput(success=False, error=f"Failed to fetch channel info: {exc}")

    if data.get("error"):
        return ChannelInfoOutput(
            success=False,
            error=data["error"].get("message") or "Failed to fetch channel info",
        )

    api_items = data.get("items") or []
    if not api_items:
        return ChannelInfoOutput(success=False, error="Channel not found")

    item = api_items[0]
    snippet = item.get("snippet") or {}
    statistics = item.get("statistics") or {}
    content_details = item.get("contentDetails") or {}
    branding = item.get("brandingSettings") or {}
    related = content_details.get("relatedPlaylists") or {}
    branding_image = branding.get("image") or {}

    return ChannelInfoOutput(
        success=True,
        channel_id=item.get("id") or "",
        title=snippet.get("title") or "",
        description=snippet.get("description") or "",
        subscriber_count=_to_int(statistics.get("subscriberCount")) or 0,
        video_count=_to_int(statistics.get("videoCount")) or 0,
        view_count=_to_int(statistics.get("viewCount")) or 0,
        published_at=snippet.get("publishedAt") or "",
        thumbnail=_best_thumbnail(snippet, order=["high", "medium", "default"]),
        custom_url=snippet.get("customUrl"),
        country=snippet.get("country"),
        uploads_playlist_id=related.get("uploads"),
        banner_image_url=branding_image.get("bannerExternalUrl"),
        hidden_subscriber_count=statistics.get("hiddenSubscriberCount") or False,
    )


@tool(args_schema=ChannelVideosInput)
@serialize_pydantic_return
async def channel_videos(
    channel_id: str,
    api_key: str,
    max_results: int = 10,
    order: str | None = None,
    page_token: str | None = None,
) -> ChannelVideosOutput:
    """Search for videos from a specific YouTube channel with sorting options."""
    if not api_key or not api_key.strip():
        return ChannelVideosOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {
        "part": "snippet",
        "type": "video",
        "channelId": channel_id,
        "key": api_key,
        "maxResults": max_results or 10,
        "order": order or "date",
    }
    if page_token:
        params["pageToken"] = page_token

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_API_BASE}/search", params=params)
        if response.status_code != 200:
            return ChannelVideosOutput(
                success=False,
                error=f"YouTube API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ChannelVideosOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ChannelVideosOutput(success=False, error=f"Failed to fetch channel videos: {exc}")

    if data.get("error"):
        return ChannelVideosOutput(
            success=False,
            error=data["error"].get("message") or "Failed to fetch channel videos",
        )

    items: list[ChannelVideoItem] = []
    for item in data.get("items") or []:
        snippet = item.get("snippet") or {}
        items.append(
            ChannelVideoItem(
                video_id=(item.get("id") or {}).get("videoId") or "",
                title=snippet.get("title") or "",
                description=snippet.get("description") or "",
                thumbnail=_best_thumbnail(snippet, order=["medium", "default", "high"]),
                published_at=snippet.get("publishedAt") or "",
                channel_title=snippet.get("channelTitle") or "",
            )
        )

    page_info = data.get("pageInfo") or {}
    return ChannelVideosOutput(
        success=True,
        items=items,
        total_results=page_info.get("totalResults") or len(items),
        next_page_token=data.get("nextPageToken"),
    )


@tool(args_schema=ChannelPlaylistsInput)
@serialize_pydantic_return
async def channel_playlists(
    channel_id: str,
    api_key: str,
    max_results: int = 10,
    page_token: str | None = None,
) -> ChannelPlaylistsOutput:
    """Get all public playlists from a specific YouTube channel."""
    if not api_key or not api_key.strip():
        return ChannelPlaylistsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {
        "part": "snippet,contentDetails",
        "channelId": channel_id,
        "key": api_key,
        "maxResults": max_results or 10,
    }
    if page_token:
        params["pageToken"] = page_token

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_API_BASE}/playlists", params=params)
        if response.status_code != 200:
            return ChannelPlaylistsOutput(
                success=False,
                error=f"YouTube API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ChannelPlaylistsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ChannelPlaylistsOutput(
            success=False, error=f"Failed to fetch channel playlists: {exc}"
        )

    if data.get("error"):
        return ChannelPlaylistsOutput(
            success=False,
            error=data["error"].get("message") or "Failed to fetch channel playlists",
        )

    items: list[PlaylistSummary] = []
    for item in data.get("items") or []:
        snippet = item.get("snippet") or {}
        content_details = item.get("contentDetails") or {}
        items.append(
            PlaylistSummary(
                playlist_id=item.get("id") or "",
                title=snippet.get("title") or "",
                description=snippet.get("description") or "",
                thumbnail=_best_thumbnail(snippet, order=["medium", "default", "high"]),
                item_count=_to_int(content_details.get("itemCount")) or 0,
                published_at=snippet.get("publishedAt") or "",
                channel_title=snippet.get("channelTitle") or "",
            )
        )

    page_info = data.get("pageInfo") or {}
    return ChannelPlaylistsOutput(
        success=True,
        items=items,
        total_results=page_info.get("totalResults") or len(items),
        next_page_token=data.get("nextPageToken"),
    )


@tool(args_schema=PlaylistItemsInput)
@serialize_pydantic_return
async def playlist_items(
    playlist_id: str,
    api_key: str,
    max_results: int = 10,
    page_token: str | None = None,
) -> PlaylistItemsOutput:
    """Get videos from a YouTube playlist. Can be used with a channel's uploads
    playlist to get all of a channel's videos."""
    if not api_key or not api_key.strip():
        return PlaylistItemsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {
        "part": "snippet,contentDetails",
        "playlistId": playlist_id,
        "key": api_key,
        "maxResults": max_results or 10,
    }
    if page_token:
        params["pageToken"] = page_token

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_API_BASE}/playlistItems", params=params)
        if response.status_code != 200:
            return PlaylistItemsOutput(
                success=False,
                error=f"YouTube API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PlaylistItemsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PlaylistItemsOutput(success=False, error=f"Failed to fetch playlist items: {exc}")

    if data.get("error"):
        return PlaylistItemsOutput(
            success=False,
            error=data["error"].get("message") or "Failed to fetch playlist items",
        )

    items: list[PlaylistItem] = []
    for index, item in enumerate(data.get("items") or []):
        snippet = item.get("snippet") or {}
        content_details = item.get("contentDetails") or {}
        resource_id = snippet.get("resourceId") or {}
        position = snippet.get("position")
        items.append(
            PlaylistItem(
                video_id=content_details.get("videoId") or resource_id.get("videoId") or "",
                title=snippet.get("title") or "",
                description=snippet.get("description") or "",
                thumbnail=_best_thumbnail(snippet, order=["medium", "default", "high"]),
                published_at=snippet.get("publishedAt") or "",
                channel_title=snippet.get("channelTitle") or "",
                position=position if position is not None else index,
                video_owner_channel_id=snippet.get("videoOwnerChannelId"),
                video_owner_channel_title=snippet.get("videoOwnerChannelTitle"),
            )
        )

    page_info = data.get("pageInfo") or {}
    return PlaylistItemsOutput(
        success=True,
        items=items,
        total_results=page_info.get("totalResults") or len(items),
        next_page_token=data.get("nextPageToken"),
    )


@tool(args_schema=CommentsInput)
@serialize_pydantic_return
async def comments(
    video_id: str,
    api_key: str,
    max_results: int = 20,
    order: str = "relevance",
    page_token: str | None = None,
) -> CommentsOutput:
    """Get top-level comments from a YouTube video with author details and
    engagement metrics."""
    if not api_key or not api_key.strip():
        return CommentsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {
        "part": "snippet,replies",
        "videoId": video_id,
        "key": api_key,
        "maxResults": max_results or 20,
        "order": order or "relevance",
    }
    if page_token:
        params["pageToken"] = page_token

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_API_BASE}/commentThreads", params=params)
        if response.status_code != 200:
            return CommentsOutput(
                success=False,
                error=f"YouTube API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CommentsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CommentsOutput(success=False, error=f"Failed to fetch comments: {exc}")

    if data.get("error"):
        return CommentsOutput(
            success=False, error=data["error"].get("message") or "Failed to fetch comments"
        )

    items: list[CommentItem] = []
    for item in data.get("items") or []:
        thread_snippet = item.get("snippet") or {}
        top_level = thread_snippet.get("topLevelComment") or {}
        top_snippet = top_level.get("snippet") or {}
        items.append(
            CommentItem(
                comment_id=top_level.get("id") or item.get("id") or "",
                author_display_name=top_snippet.get("authorDisplayName") or "",
                author_channel_url=top_snippet.get("authorChannelUrl") or "",
                author_profile_image_url=top_snippet.get("authorProfileImageUrl") or "",
                text_display=top_snippet.get("textDisplay") or "",
                text_original=top_snippet.get("textOriginal") or "",
                like_count=_to_int(top_snippet.get("likeCount")) or 0,
                published_at=top_snippet.get("publishedAt") or "",
                updated_at=top_snippet.get("updatedAt") or "",
                reply_count=_to_int(thread_snippet.get("totalReplyCount")) or 0,
            )
        )

    page_info = data.get("pageInfo") or {}
    return CommentsOutput(
        success=True,
        items=items,
        total_results=page_info.get("totalResults") or len(items),
        next_page_token=data.get("nextPageToken"),
    )
