"""Pydantic response models for the hootsuite integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateMediaUploadJobOutput",
    "GetMediaUploadStatusOutput",
    "ListSocialProfilesOutput",
    "ScheduleMessageOutput",
    "ScheduledMessage",
    "SocialProfile",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class SocialProfile(_Base):
    """A Hootsuite social profile."""

    id: str | None = None
    type: str | None = None
    social_network_username: str | None = None
    social_network_id: str | None = None


class ScheduledMessage(_Base):
    """A scheduled message returned by the Hootsuite API."""

    id: str | None = None
    state: str | None = None
    text: str | None = None
    scheduled_send_time: str | None = None


# --- Per-action output models ---------------------------------------------


class CreateMediaUploadJobOutput(_Base):
    success: bool
    error: str | None = None
    file_id: str | None = None


class GetMediaUploadStatusOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    state: str | None = None
    download_url: str | None = None
    thumbnail_url: str | None = None


class ListSocialProfilesOutput(_Base):
    success: bool
    error: str | None = None
    profiles: list[SocialProfile] = Field(default_factory=list)


class ScheduleMessageOutput(_Base):
    success: bool
    error: str | None = None
    messages: list[ScheduledMessage] = Field(default_factory=list)
