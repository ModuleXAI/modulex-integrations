"""Pydantic response models for the Buffer integration's @tool functions.

Buffer exposes a single GraphQL endpoint (``https://api.buffer.com``), so
every action posts a query/mutation and reads its typed result out of the
``data`` envelope. The models below flatten those GraphQL nodes into stable
snake_case shapes.

Buffer answers HTTP 200 for practically everything — transport failures,
top-level ``errors`` arrays, and typed mutation errors alike — so each model
carries ``success`` + ``error`` and every data field stays optional.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "BufferAccount",
    "BufferAsset",
    "BufferChannel",
    "BufferIdea",
    "BufferIdeaGroup",
    "BufferOrganization",
    "BufferPageInfo",
    "BufferPost",
    "BufferPostError",
    "CreateIdeaOutput",
    "CreatePostOutput",
    "DeletePostOutput",
    "EditPostOutput",
    "GetAccountOutput",
    "GetChannelsOutput",
    "GetIdeaGroupsOutput",
    "GetIdeasOutput",
    "GetPostOutput",
    "GetPostsOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class BufferAsset(_Base):
    """A media attachment on a post (image, video, or document)."""

    id: str | None = None
    type: str | None = None
    mime_type: str | None = None
    source: str | None = None
    thumbnail: str | None = None


class BufferPostError(_Base):
    """Publishing failure details carried by a post in ``error`` status."""

    message: str | None = None
    support_url: str | None = None
    raw_error: str | None = None


class BufferPost(_Base):
    """A single post in the queue, draft box, or sent history."""

    id: str | None = None
    text: str | None = None
    status: str | None = None
    via: str | None = None
    channel_id: str | None = None
    channel_service: str | None = None
    scheduling_type: str | None = None
    share_mode: str | None = None
    is_custom_scheduled: bool | None = None
    shared_now: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None
    due_at: str | None = None
    sent_at: str | None = None
    external_link: str | None = None
    error: BufferPostError | None = None
    assets: list[BufferAsset] = Field(default_factory=list)


class BufferChannel(_Base):
    """A social account connected to an organization."""

    id: str | None = None
    name: str | None = None
    display_name: str | None = None
    service: str | None = None
    service_id: str | None = None
    avatar: str | None = None
    timezone: str | None = None
    type: str | None = None
    is_queue_paused: bool | None = None
    is_disconnected: bool | None = None
    organization_id: str | None = None


class BufferOrganization(_Base):
    """An organization the authenticated account belongs to."""

    id: str | None = None
    name: str | None = None
    channel_count: int | None = None
    owner_email: str | None = None


class BufferAccount(_Base):
    """The authenticated account and the organizations it can reach."""

    id: str | None = None
    email: str | None = None
    name: str | None = None
    timezone: str | None = None
    organizations: list[BufferOrganization] = Field(default_factory=list)


class BufferIdea(_Base):
    """A content idea saved on the ideas board."""

    id: str | None = None
    organization_id: str | None = None
    group_id: str | None = None
    title: str | None = None
    text: str | None = None


class BufferIdeaGroup(_Base):
    """A column on the ideas board."""

    id: str | None = None
    name: str | None = None
    is_locked: bool | None = None


class BufferPageInfo(_Base):
    """Relay-style cursor info for a paginated result."""

    has_next_page: bool | None = None
    end_cursor: str | None = None


# --- Per-action output models ----------------------------------------------


class CreatePostOutput(_Base):
    success: bool
    error: str | None = None
    post: BufferPost | None = None


class EditPostOutput(_Base):
    success: bool
    error: str | None = None
    post: BufferPost | None = None


class GetPostOutput(_Base):
    success: bool
    error: str | None = None
    post: BufferPost | None = None


class GetPostsOutput(_Base):
    success: bool
    error: str | None = None
    posts: list[BufferPost] = Field(default_factory=list)
    page_info: BufferPageInfo | None = None


class DeletePostOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool = False
    id: str | None = None


class GetChannelsOutput(_Base):
    success: bool
    error: str | None = None
    channels: list[BufferChannel] = Field(default_factory=list)


class GetAccountOutput(_Base):
    success: bool
    error: str | None = None
    account: BufferAccount | None = None


class CreateIdeaOutput(_Base):
    success: bool
    error: str | None = None
    idea: BufferIdea | None = None


class GetIdeasOutput(_Base):
    success: bool
    error: str | None = None
    ideas: list[BufferIdea] = Field(default_factory=list)
    page_info: BufferPageInfo | None = None


class GetIdeaGroupsOutput(_Base):
    success: bool
    error: str | None = None
    idea_groups: list[BufferIdeaGroup] = Field(default_factory=list)
