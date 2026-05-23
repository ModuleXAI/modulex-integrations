"""Pydantic response models for the heroku integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AppSummary",
    "ListAppsOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class AppSummary(_Base):
    """A Heroku app summary."""

    id: str | None = None
    name: str | None = None
    web_url: str | None = None
    region: str | None = None
    stack: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


# --- Per-action output models ---------------------------------------------


class ListAppsOutput(_Base):
    success: bool
    apps: list[AppSummary] = Field(default_factory=list)
