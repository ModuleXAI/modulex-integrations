"""Pydantic response models for the reflect integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AppendDailyNoteOutput",
    "CreateLinkOutput",
    "GetUserOutput",
    "LinkItem",
    "ListGraphIdOptionsOutput",
    "ListLinksOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class LinkItem(_Base):
    """A link object returned by the Reflect API."""

    id: str | None = None
    url: str | None = None
    title: str | None = None
    description: str | None = None
    updated_at: str | None = None


# --- Per-action output models ---------------------------------------------


class AppendDailyNoteOutput(_Base):
    success: bool
    error: str | None = None


class CreateLinkOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class GetUserOutput(_Base):
    success: bool
    error: str | None = None
    uid: str | None = None
    graph_ids: list[str] = Field(default_factory=list)


class ListGraphIdOptionsOutput(_Base):
    success: bool
    error: str | None = None
    graph_ids: list[str] = Field(default_factory=list)


class ListLinksOutput(_Base):
    success: bool
    error: str | None = None
    links: list[LinkItem] = Field(default_factory=list)
