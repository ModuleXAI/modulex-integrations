"""Pydantic response models for the YouTube integration's @tool functions.

YouTube's tools follow the modulex *api_key* runtime convention: each
function signature takes ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair used by token-based integrations), and
the modulex ``ToolExecutor`` injects it from the resolved credential.
The YouTube Data API v3 passes the key as a ``key=`` query parameter,
not an ``Authorization`` header.

Error model: the API returns HTTP 200 with an ``{"error": {...}}``
envelope on failure. Each function surfaces that as ``success=False`` +
``error`` rather than raising, so every output model carries both
shapes. Every scalar field is permissive (``<type> | None = None``) and
every list defaults to empty, mirroring the upstream ``.get()`` access
pattern.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ChannelInfoOutput",
    "ChannelPlaylistsOutput",
    "ChannelVideoItem",
    "ChannelVideosOutput",
    "CommentItem",
    "CommentsOutput",
    "PlaylistItem",
    "PlaylistItemsOutput",
    "PlaylistSummary",
    "SearchItem",
    "SearchOutput",
    "TrendingItem",
    "TrendingOutput",
    "VideoCategoriesOutput",
    "VideoCategoryItem",
    "VideoDetailsOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class SearchItem(_Base):
    """A single video row in ``search``."""

    video_id: str | None = None
    title: str | None = None
    description: str | None = None
    thumbnail: str | None = None
    channel_id: str | None = None
    channel_title: str | None = None
    published_at: str | None = None
    live_broadcast_content: str | None = None


class TrendingItem(_Base):
    """A single video row in ``trending``."""

    video_id: str | None = None
    title: str | None = None
    description: str | None = None
    thumbnail: str | None = None
    channel_id: str | None = None
    channel_title: str | None = None
    published_at: str | None = None
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    duration: str | None = None


class ChannelVideoItem(_Base):
    """A single video row in ``channel_videos``."""

    video_id: str | None = None
    title: str | None = None
    description: str | None = None
    thumbnail: str | None = None
    published_at: str | None = None
    channel_title: str | None = None


class PlaylistSummary(_Base):
    """A single playlist row in ``channel_playlists``."""

    playlist_id: str | None = None
    title: str | None = None
    description: str | None = None
    thumbnail: str | None = None
    item_count: int | None = None
    published_at: str | None = None
    channel_title: str | None = None


class PlaylistItem(_Base):
    """A single video row in ``playlist_items``."""

    video_id: str | None = None
    title: str | None = None
    description: str | None = None
    thumbnail: str | None = None
    published_at: str | None = None
    channel_title: str | None = None
    position: int | None = None
    video_owner_channel_id: str | None = None
    video_owner_channel_title: str | None = None


class CommentItem(_Base):
    """A single top-level comment row in ``comments``."""

    comment_id: str | None = None
    author_display_name: str | None = None
    author_channel_url: str | None = None
    author_profile_image_url: str | None = None
    text_display: str | None = None
    text_original: str | None = None
    like_count: int | None = None
    published_at: str | None = None
    updated_at: str | None = None
    reply_count: int | None = None


class VideoCategoryItem(_Base):
    """A single category row in ``video_categories``."""

    category_id: str | None = None
    title: str | None = None
    assignable: bool | None = None


# --- Per-action output models ----------------------------------------------


class SearchOutput(_Base):
    success: bool
    error: str | None = None
    items: list[SearchItem] = Field(default_factory=list)
    total_results: int = 0
    next_page_token: str | None = None


class TrendingOutput(_Base):
    success: bool
    error: str | None = None
    items: list[TrendingItem] = Field(default_factory=list)
    total_results: int = 0
    next_page_token: str | None = None


class VideoDetailsOutput(_Base):
    success: bool
    error: str | None = None
    video_id: str | None = None
    title: str | None = None
    description: str | None = None
    channel_id: str | None = None
    channel_title: str | None = None
    published_at: str | None = None
    duration: str | None = None
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    favorite_count: int | None = None
    thumbnail: str | None = None
    tags: list[str] = Field(default_factory=list)
    category_id: str | None = None
    definition: str | None = None
    caption: str | None = None
    licensed_content: bool | None = None
    privacy_status: str | None = None
    live_broadcast_content: str | None = None
    default_language: str | None = None
    default_audio_language: str | None = None
    is_live_content: bool | None = None
    scheduled_start_time: str | None = None
    actual_start_time: str | None = None
    actual_end_time: str | None = None
    concurrent_viewers: int | None = None
    active_live_chat_id: str | None = None


class VideoCategoriesOutput(_Base):
    success: bool
    error: str | None = None
    items: list[VideoCategoryItem] = Field(default_factory=list)
    total_results: int = 0


class ChannelInfoOutput(_Base):
    success: bool
    error: str | None = None
    channel_id: str | None = None
    title: str | None = None
    description: str | None = None
    subscriber_count: int | None = None
    video_count: int | None = None
    view_count: int | None = None
    published_at: str | None = None
    thumbnail: str | None = None
    custom_url: str | None = None
    country: str | None = None
    uploads_playlist_id: str | None = None
    banner_image_url: str | None = None
    hidden_subscriber_count: bool | None = None


class ChannelVideosOutput(_Base):
    success: bool
    error: str | None = None
    items: list[ChannelVideoItem] = Field(default_factory=list)
    total_results: int = 0
    next_page_token: str | None = None


class ChannelPlaylistsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[PlaylistSummary] = Field(default_factory=list)
    total_results: int = 0
    next_page_token: str | None = None


class PlaylistItemsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[PlaylistItem] = Field(default_factory=list)
    total_results: int = 0
    next_page_token: str | None = None


class CommentsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[CommentItem] = Field(default_factory=list)
    total_results: int = 0
    next_page_token: str | None = None
