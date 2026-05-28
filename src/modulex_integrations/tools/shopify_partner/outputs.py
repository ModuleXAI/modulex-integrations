"""Pydantic response models for the shopify_partner integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
    "VerifyWebhookOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class VerifyWebhookOutput(_Base):
    success: bool
    error: str | None = None
    valid: bool | None = None
