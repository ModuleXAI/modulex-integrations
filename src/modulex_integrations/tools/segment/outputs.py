"""Pydantic response models for the segment integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
    "AliasOutput",
    "GroupOutput",
    "IdentifyOutput",
    "PageOutput",
    "ScreenOutput",
    "TrackOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class AliasOutput(_Base):
    success: bool
    error: str | None = None


class GroupOutput(_Base):
    success: bool
    error: str | None = None


class IdentifyOutput(_Base):
    success: bool
    error: str | None = None


class PageOutput(_Base):
    success: bool
    error: str | None = None


class ScreenOutput(_Base):
    success: bool
    error: str | None = None


class TrackOutput(_Base):
    success: bool
    error: str | None = None
