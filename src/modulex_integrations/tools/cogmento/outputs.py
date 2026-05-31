"""Pydantic response models for the cogmento integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateContactOutput",
    "CreateDealOutput",
    "CreateTaskOutput",
    "ListUserIdsOptionsOutput",
    "UserOption",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class UserOption(_Base):
    """A user option with label and value."""

    label: str | None = None
    value: str | None = None


# --- Per-action output models ---------------------------------------------


class CreateContactOutput(_Base):
    success: bool
    error: str | None = None
    contact: dict[str, Any] | None = None


class CreateDealOutput(_Base):
    success: bool
    error: str | None = None
    deal: dict[str, Any] | None = None


class CreateTaskOutput(_Base):
    success: bool
    error: str | None = None
    task: dict[str, Any] | None = None


class ListUserIdsOptionsOutput(_Base):
    success: bool
    error: str | None = None
    users: list[UserOption] = Field(default_factory=list)
