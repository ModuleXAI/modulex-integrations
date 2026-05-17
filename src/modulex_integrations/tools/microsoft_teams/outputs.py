"""Pydantic response models for the microsoft_teams integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ChannelResource",
    "ChatMessageResource",
    "ChatResource",
    "CreateChannelOutput",
    "CurrentUser",
    "GetChatMessageOutput",
    "GetCurrentUserOutput",
    "ListChannelMessagesOutput",
    "ListChannelsOutput",
    "ListChatsOutput",
    "ListMessagesInChatOutput",
    "ListShiftsOutput",
    "ListTeamsOutput",
    "SearchMessagesOutput",
    "SearchResponse",
    "SendChannelMessageOutput",
    "SendChatMessageOutput",
    "ShiftResource",
    "TeamResource",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class ChannelResource(_Base):
    """Microsoft Graph Channel resource."""

    id: str | None = None
    displayName: str | None = None
    description: str | None = None
    membershipType: str | None = None
    webUrl: str | None = None


class ChatMessageResource(_Base):
    """Microsoft Graph chatMessage resource (permissive — upstream returns many optional fields)."""

    id: str | None = None
    createdDateTime: str | None = None
    from_: dict[str, Any] | None = Field(default=None, alias="from")
    body: dict[str, Any] | None = None
    importance: str | None = None
    webUrl: str | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ChatResource(_Base):
    """Microsoft Graph Chat resource (with members expanded)."""

    id: str | None = None
    topic: str | None = None
    chatType: str | None = None
    createdDateTime: str | None = None
    lastUpdatedDateTime: str | None = None
    webUrl: str | None = None
    members: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class CurrentUser(_Base):
    """Subset of Microsoft Graph user resource returned by get_current_user."""

    id: str | None = None
    displayName: str | None = None
    mail: str | None = None
    userPrincipalName: str | None = None


class SearchResponse(_Base):
    """Microsoft Graph search response wrapper."""

    value: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ShiftResource(_Base):
    """Microsoft Graph Shift resource."""

    id: str | None = None
    userId: str | None = None
    schedulingGroupId: str | None = None
    createdDateTime: str | None = None
    lastModifiedDateTime: str | None = None
    sharedShift: dict[str, Any] | None = None
    draftShift: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")


class TeamResource(_Base):
    """Microsoft Graph Team resource."""

    id: str | None = None
    displayName: str | None = None
    description: str | None = None
    visibility: str | None = None
    webUrl: str | None = None


# --- Per-action output models ---------------------------------------------


class CreateChannelOutput(_Base):
    success: bool
    error: str | None = None
    channel: ChannelResource | None = None


class GetChatMessageOutput(_Base):
    success: bool
    error: str | None = None
    message: ChatMessageResource | None = None


class GetCurrentUserOutput(_Base):
    success: bool
    error: str | None = None
    user: CurrentUser | None = None


class ListChannelMessagesOutput(_Base):
    success: bool
    error: str | None = None
    messages: list[ChatMessageResource] = Field(default_factory=list)


class ListChannelsOutput(_Base):
    success: bool
    error: str | None = None
    channels: list[ChannelResource] = Field(default_factory=list)


class ListChatsOutput(_Base):
    success: bool
    error: str | None = None
    chats: list[ChatResource] = Field(default_factory=list)


class ListMessagesInChatOutput(_Base):
    success: bool
    error: str | None = None
    messages: list[ChatMessageResource] = Field(default_factory=list)


class ListShiftsOutput(_Base):
    success: bool
    error: str | None = None
    shifts: list[ShiftResource] = Field(default_factory=list)


class ListTeamsOutput(_Base):
    success: bool
    error: str | None = None
    teams: list[TeamResource] = Field(default_factory=list)


class SearchMessagesOutput(_Base):
    success: bool
    error: str | None = None
    result: SearchResponse | None = None


class SendChannelMessageOutput(_Base):
    success: bool
    error: str | None = None
    message: ChatMessageResource | None = None


class SendChatMessageOutput(_Base):
    success: bool
    error: str | None = None
    message: ChatMessageResource | None = None
