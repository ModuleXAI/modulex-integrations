"""Pydantic response models for the medium integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreatePostOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class CreatePostOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    title: str | None = None
    author_id: str | None = None
    url: str | None = None
    canonical_url: str | None = None
    publish_status: str | None = None
    published_at: int | None = None
    license: str | None = None
    license_url: str | None = None
    tags: list[str] = Field(default_factory=list)
