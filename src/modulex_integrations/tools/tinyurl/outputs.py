"""Pydantic response models for the TinyURL integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateShortenedLinkOutput",
    "RetrieveLinkAnalyticsOutput",
    "UpdateLinkMetadataOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateShortenedLinkOutput(_Base):
    success: bool
    error: str | None = None
    tiny_url: str | None = None
    url: str | None = None
    domain: str | None = None
    alias: str | None = None
    created_at: str | None = None


class RetrieveLinkAnalyticsOutput(_Base):
    success: bool
    error: str | None = None
    total_clicks: int | None = None
    # date_range is `{"from": ..., "to": ...}` — kept as raw dict
    # because `from` collides with the Python keyword.
    date_range: dict[str, Any] | None = None
    clicks_by_country: list[dict[str, Any]] = Field(default_factory=list)
    clicks_by_device: list[dict[str, Any]] = Field(default_factory=list)
    clicks_by_referrer: list[dict[str, Any]] = Field(default_factory=list)


class UpdateLinkMetadataOutput(_Base):
    success: bool
    error: str | None = None
    tiny_url: str | None = None
    url: str | None = None
    domain: str | None = None
    alias: str | None = None
    updated_at: str | None = None
    analytics_enabled: bool | None = None
