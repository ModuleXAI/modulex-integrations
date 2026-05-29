"""Pydantic response models for the livestorm integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateEventOutput",
    "GetEventOutput",
    "ListAttendeesFromEventOutput",
    "ListEventsOutput",
    "ListSessionsOutput",
    "RegisterSomeoneForSessionOutput",
    "UpdateEventOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Per-action output models ------------------------------------------------


class CreateEventOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetEventOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class ListAttendeesFromEventOutput(_Base):
    success: bool
    error: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)


class ListEventsOutput(_Base):
    success: bool
    error: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)


class ListSessionsOutput(_Base):
    success: bool
    error: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)


class RegisterSomeoneForSessionOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class UpdateEventOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None
