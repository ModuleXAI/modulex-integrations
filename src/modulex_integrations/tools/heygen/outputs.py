"""Pydantic response models for the heygen integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateTalkingPhotoOutput",
    "CreateVideoFromTemplateOutput",
    "ListCustomEventsOptionsOutput",
    "ListVoiceIdOptionsOutput",
    "RetrieveVideoLinkOutput",
    "VoiceInfo",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class VoiceInfo(_Base):
    """A voice entry returned by the list voices endpoint."""

    voice_id: str | None = None
    name: str | None = None


# --- Per-action output models ---------------------------------------------


class CreateTalkingPhotoOutput(_Base):
    success: bool
    error: str | None = None
    video_id: str | None = None
    status: str | None = None


class CreateVideoFromTemplateOutput(_Base):
    success: bool
    error: str | None = None
    video_id: str | None = None
    status: str | None = None


class ListCustomEventsOptionsOutput(_Base):
    success: bool
    error: str | None = None
    events: list[str] = Field(default_factory=list)


class ListVoiceIdOptionsOutput(_Base):
    success: bool
    error: str | None = None
    voices: list[VoiceInfo] = Field(default_factory=list)


class RetrieveVideoLinkOutput(_Base):
    success: bool
    error: str | None = None
    video_id: str | None = None
    status: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    duration: float | None = None
    caption_url: str | None = None
