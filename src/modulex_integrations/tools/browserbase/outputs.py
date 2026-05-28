"""Pydantic response models for the browserbase integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateContextOutput",
    "CreateSessionOutput",
    "ListProjectsOutput",
    "ProjectSummary",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class ProjectSummary(_Base):
    id: str | None = None
    name: str | None = None


# --- Per-action output models ---------------------------------------------


class CreateContextOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    project_id: str | None = None
    created_at: str | None = None


class CreateSessionOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    project_id: str | None = None
    status: str | None = None
    created_at: str | None = None
    region: str | None = None
    connect_url: str | None = None


class ListProjectsOutput(_Base):
    success: bool
    error: str | None = None
    projects: list[ProjectSummary] = Field(default_factory=list)
