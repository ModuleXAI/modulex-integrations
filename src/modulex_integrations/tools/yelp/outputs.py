"""Pydantic response models for the yelp integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "BusinessSummary",
    "GetBusinessDetailsOutput",
    "ListBusinessReviewsOutput",
    "ReviewSummary",
    "SearchBusinessesByPhoneNumberOutput",
    "SearchBusinessesOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class BusinessSummary(_Base):
    """A business object returned by Yelp search endpoints."""

    id: str | None = None
    alias: str | None = None
    name: str | None = None
    image_url: str | None = None
    url: str | None = None
    review_count: int | None = None
    categories: list[dict[str, Any]] = Field(default_factory=list)
    rating: float | None = None
    coordinates: dict[str, Any] | None = None
    location: dict[str, Any] | None = None
    phone: str | None = None
    display_phone: str | None = None
    distance: float | None = None


class ReviewSummary(_Base):
    """A review object returned by the reviews endpoint."""

    id: str | None = None
    url: str | None = None
    text: str | None = None
    rating: int | None = None
    time_created: str | None = None
    user: dict[str, Any] | None = None


# --- Per-action output models ---------------------------------------------


class SearchBusinessesOutput(_Base):
    success: bool
    error: str | None = None
    businesses: list[BusinessSummary] = Field(default_factory=list)
    total: int = 0


class GetBusinessDetailsOutput(_Base):
    success: bool
    error: str | None = None
    business: dict[str, Any] | None = None


class ListBusinessReviewsOutput(_Base):
    success: bool
    error: str | None = None
    reviews: list[ReviewSummary] = Field(default_factory=list)
    total: int = 0
    possible_languages: list[str] = Field(default_factory=list)


class SearchBusinessesByPhoneNumberOutput(_Base):
    success: bool
    error: str | None = None
    businesses: list[BusinessSummary] = Field(default_factory=list)
