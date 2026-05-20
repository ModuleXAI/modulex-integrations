"""Pydantic response models for the google_workspace integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ListActivitiesByAdminOutput",
    "ListActivitiesByEventAndAdminOutput",
    "ListActivitiesByEventNameOutput",
    "ListAllActivitiesOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class ListActivitiesByAdminOutput(_Base):
    success: bool
    error: str | None = None
    activities: list[dict[str, Any]] = Field(default_factory=list)


class ListActivitiesByEventAndAdminOutput(_Base):
    success: bool
    error: str | None = None
    activities: list[dict[str, Any]] = Field(default_factory=list)


class ListActivitiesByEventNameOutput(_Base):
    success: bool
    error: str | None = None
    activities: list[dict[str, Any]] = Field(default_factory=list)


class ListAllActivitiesOutput(_Base):
    success: bool
    error: str | None = None
    activities: list[dict[str, Any]] = Field(default_factory=list)
