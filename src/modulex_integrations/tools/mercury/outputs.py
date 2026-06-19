"""Pydantic response models for the mercury integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
    "GetAccountInfoOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class GetAccountInfoOutput(_Base):
    success: bool
    error: str | None = None
    account_id: str | None = None
    name: str | None = None
    status: str | None = None
    account_type: str | None = None
    current_balance: float | None = None
    available_balance: float | None = None
    routing_number: str | None = None
    account_number: str | None = None
    created_at: str | None = None
