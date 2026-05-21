"""Pydantic response models for the google_my_business integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreatePostOutput",
    "CreateUpdateReplyToReviewOutput",
    "GetReviewsMultipleLocationsOutput",
    "GetSpecificReviewOutput",
    "ListAllReviewsOutput",
    "ListPostsOutput",
    "LocalPost",
    "LocationReview",
    "Review",
    "ReviewReply",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class ReviewReply(_Base):
    """A reply to a review."""

    comment: str | None = None
    update_time: str | None = None


class Review(_Base):
    """A Google My Business review."""

    name: str | None = None
    review_id: str | None = None
    reviewer_display_name: str | None = None
    star_rating: str | None = None
    comment: str | None = None
    create_time: str | None = None
    update_time: str | None = None
    review_reply: ReviewReply | None = None


class LocationReview(_Base):
    """A review associated with a location in a batch response."""

    location_name: str | None = None
    reviews: list[Review] = Field(default_factory=list)


class LocalPost(_Base):
    """A Google My Business local post."""

    name: str | None = None
    summary: str | None = None
    topic_type: str | None = None
    state: str | None = None
    create_time: str | None = None
    update_time: str | None = None
    search_url: str | None = None
    event: dict[str, Any] | None = None
    offer: dict[str, Any] | None = None
    call_to_action: dict[str, Any] | None = None


# --- Per-action output models ---------------------------------------------


class CreatePostOutput(_Base):
    success: bool
    error: str | None = None
    post: LocalPost | None = None


class CreateUpdateReplyToReviewOutput(_Base):
    success: bool
    error: str | None = None
    comment: str | None = None
    update_time: str | None = None


class GetReviewsMultipleLocationsOutput(_Base):
    success: bool
    error: str | None = None
    location_reviews: list[LocationReview] = Field(default_factory=list)


class GetSpecificReviewOutput(_Base):
    success: bool
    error: str | None = None
    review: Review | None = None


class ListAllReviewsOutput(_Base):
    success: bool
    error: str | None = None
    reviews: list[Review] = Field(default_factory=list)
    next_page_token: str | None = None


class ListPostsOutput(_Base):
    success: bool
    error: str | None = None
    posts: list[LocalPost] = Field(default_factory=list)
