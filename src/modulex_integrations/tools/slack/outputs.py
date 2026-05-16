"""Pydantic response models for the Slack integration's @tool functions.

Unlike GitHub (which raises on non-2xx), Slack's Web API returns
HTTP 200 with ``{"ok": false, "error": "..."}`` on errors. Each output
model therefore carries both a ``success`` flag and an ``error`` field
populated on the failure branch; on success ``error`` is None and the
result fields are populated instead.

The legacy modulex slack tool wrapped results in a second ``result``
key (``{"success": ..., "action": ..., "result": {...}}``). The
migration flattens this for consistency with the github migration —
no functional change, just a tighter wire shape.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddReactionOutput",
    "Channel",
    "ChannelMessage",
    "GetChannelHistoryOutput",
    "GetThreadRepliesOutput",
    "GetUserProfileOutput",
    "GetUsersOutput",
    "ListChannelsOutput",
    "Message",
    "PostMessageOutput",
    "ReplyToThreadOutput",
    "ThreadMessage",
    "User",
    "UserProfile",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class Channel(_Base):
    """One row in ``list_channels``."""

    id: str | None = None
    name: str | None = None
    is_channel: bool | None = None
    is_private: bool | None = None
    is_archived: bool | None = None
    is_member: bool | None = None
    num_members: int | None = None
    topic: str | None = None
    purpose: str | None = None
    created: int | None = None


class Message(_Base):
    """Compact message representation returned by post/reply actions."""

    text: str | None = None
    user: str | None = None
    type: str | None = None
    ts: str | None = None


class ChannelMessage(_Base):
    """A row in ``get_channel_history``."""

    type: str | None = None
    user: str | None = None
    text: str | None = None
    ts: str | None = None
    thread_ts: str | None = None
    reply_count: int | None = None
    reactions: list[dict[str, object]] = Field(default_factory=list)


class ThreadMessage(_Base):
    """A row in ``get_thread_replies``."""

    type: str | None = None
    user: str | None = None
    text: str | None = None
    ts: str | None = None
    thread_ts: str | None = None
    parent_user_id: str | None = None
    reactions: list[dict[str, object]] = Field(default_factory=list)


class User(_Base):
    """A row in ``get_users``."""

    id: str | None = None
    name: str | None = None
    real_name: str | None = None
    display_name: str | None = None
    email: str | None = None
    is_admin: bool | None = None
    is_owner: bool | None = None
    is_bot: bool | None = None
    deleted: bool | None = None
    tz: str | None = None
    updated: int | None = None


class UserProfile(_Base):
    """The ``profile`` block of ``get_user_profile``."""

    real_name: str | None = None
    display_name: str | None = None
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    status_text: str | None = None
    status_emoji: str | None = None
    image_24: str | None = None
    image_48: str | None = None
    image_72: str | None = None
    image_192: str | None = None
    image_512: str | None = None


# --- Per-action output models ----------------------------------------------


class ListChannelsOutput(_Base):
    success: bool
    error: str | None = None
    channels: list[Channel] = Field(default_factory=list)
    total: int = 0
    next_cursor: str | None = None


class PostMessageOutput(_Base):
    success: bool
    error: str | None = None
    channel: str | None = None
    ts: str | None = None
    message: Message | None = None


class ReplyToThreadOutput(_Base):
    success: bool
    error: str | None = None
    channel: str | None = None
    ts: str | None = None
    thread_ts: str | None = None
    message: Message | None = None


class AddReactionOutput(_Base):
    success: bool
    error: str | None = None
    channel: str | None = None
    timestamp: str | None = None
    reaction: str | None = None


class GetChannelHistoryOutput(_Base):
    success: bool
    error: str | None = None
    channel: str | None = None
    messages: list[ChannelMessage] = Field(default_factory=list)
    total: int = 0
    has_more: bool = False


class GetThreadRepliesOutput(_Base):
    success: bool
    error: str | None = None
    channel: str | None = None
    thread_ts: str | None = None
    messages: list[ThreadMessage] = Field(default_factory=list)
    total: int = 0
    has_more: bool = False


class GetUsersOutput(_Base):
    success: bool
    error: str | None = None
    users: list[User] = Field(default_factory=list)
    total: int = 0
    next_cursor: str | None = None


class GetUserProfileOutput(_Base):
    success: bool
    error: str | None = None
    user_id: str | None = None
    profile: UserProfile | None = None
