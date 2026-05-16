"""Pydantic response models for the Hacker News integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "GetItemOutput",
    "GetStoriesOutput",
    "GetUserOutput",
    "HNRSSItem",
    "SearchOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HNRSSItem(_Base):
    title: str | None = None
    link: str | None = None
    description: str | None = None
    pub_date: str | None = None
    guid: str | None = None
    author: str | None = None
    comments_url: str | None = None


class SearchOutput(_Base):
    success: bool
    error: str | None = None
    # For stories -> "stories"; for comments -> "comments". Mirroring
    # legacy: only one of these is populated per action.
    stories: list[HNRSSItem] = Field(default_factory=list)
    comments: list[HNRSSItem] = Field(default_factory=list)
    count: int = 0
    keyword: str = ""
    source: str = "hnrss.org"


class GetStoriesOutput(_Base):
    success: bool
    error: str | None = None
    # When fetch_details=True
    stories: list[dict[str, Any]] = Field(default_factory=list)
    # job_stories has a separate "jobs" name in legacy; we surface it on
    # `stories` as well to keep one shape, and `type` carries the source.
    # When fetch_details=False
    story_ids: list[int] = Field(default_factory=list)
    count: int = 0
    type: str | None = None


class GetItemOutput(_Base):
    success: bool
    error: str | None = None
    item: dict[str, Any] | None = None
    item_id: int | None = None


class GetUserOutput(_Base):
    success: bool
    error: str | None = None
    user: dict[str, Any] | None = None
    username: str | None = None
