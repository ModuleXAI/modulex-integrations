"""Pydantic response models for the google_merchant_center integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "CreateProductOutput",
    "UpdateProductOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class CreateProductOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class UpdateProductOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None
