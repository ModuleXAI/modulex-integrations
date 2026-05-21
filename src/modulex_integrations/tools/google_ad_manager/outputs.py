"""Pydantic response models for the google_ad_manager integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateReportOutput",
    "ListNetworkOptionsOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class CreateReportOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class ListNetworkOptionsOutput(_Base):
    success: bool
    error: str | None = None
    networks: list[str] = Field(default_factory=list)
