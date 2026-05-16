"""Pydantic response models for the Pinterest integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreatePinOutput",
    "GetBoardSectionsOutput",
    "ListBoardsOutput",
    "ListPinsOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ListBoardsOutput(_Base):
    success: bool
    error: str | None = None
    boards: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    bookmark: str | None = None


class GetBoardSectionsOutput(_Base):
    success: bool
    error: str | None = None
    board_id: str | None = None
    sections: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    bookmark: str | None = None


class CreatePinOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    title: str | None = None
    description: str | None = None
    link: str | None = None
    board_id: str | None = None
    board_section_id: str | None = None
    created_at: str | None = None
    # Full Pinterest pin response (media, etc.) — kept as raw dict.
    pin: dict[str, Any] | None = None


class ListPinsOutput(_Base):
    success: bool
    error: str | None = None
    board_id: str | None = None
    board_section_id: str | None = None
    pins: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    bookmark: str | None = None
