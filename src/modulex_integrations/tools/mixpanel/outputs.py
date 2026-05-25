"""Pydantic response models for the mixpanel integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "EmitEventToOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class EmitEventToOutput(_Base):
    success: bool
    error: str | None = None
    distinct_id: str | None = None
    properties: dict[str, Any] | None = Field(default=None)
