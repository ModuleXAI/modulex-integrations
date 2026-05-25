"""Pydantic response models for the google_maps_platform integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "GetPlaceDetailsOutput",
    "SearchPlacesOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class SearchPlacesOutput(_Base):
    success: bool
    error: str | None = None
    places: list[dict[str, Any]] = Field(default_factory=list)


class GetPlaceDetailsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None
