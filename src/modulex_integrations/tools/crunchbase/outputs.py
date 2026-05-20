"""Pydantic response models for the crunchbase integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "GetOrganizationOutput",
    "SearchOrganizationsOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class GetOrganizationOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class SearchOrganizationsOutput(_Base):
    success: bool
    error: str | None = None
    entities: list[dict[str, Any]] = Field(default_factory=list)
    total_count: int | None = None
