"""Pydantic response models for the google_search_console integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "RetrieveSitePerformanceDataOutput",
    "SearchAnalyticsRow",
    "SubmitUrlForIndexingOutput",
    "UrlNotificationMetadata",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class SearchAnalyticsRow(_Base):
    """A single row from the Search Analytics response."""

    keys: list[str] = Field(default_factory=list)
    clicks: float | None = None
    impressions: float | None = None
    ctr: float | None = None
    position: float | None = None


class UrlNotificationMetadata(_Base):
    """Metadata returned after submitting a URL for indexing."""

    url: str | None = None
    latest_update: dict[str, str] | None = None
    latest_remove: dict[str, str] | None = None


# --- Per-action output models ---------------------------------------------


class RetrieveSitePerformanceDataOutput(_Base):
    success: bool
    error: str | None = None
    rows: list[SearchAnalyticsRow] = Field(default_factory=list)
    response_aggregation_type: str | None = None


class SubmitUrlForIndexingOutput(_Base):
    success: bool
    error: str | None = None
    url_notification_metadata: UrlNotificationMetadata | None = None
