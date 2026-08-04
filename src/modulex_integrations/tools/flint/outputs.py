"""Pydantic response models for the Flint integration.

One ``*Output`` model per action. Every field is permissive
(``<type> | None = None`` / ``default_factory=list``) because the Agent
Tasks API omits keys that do not apply to the current task state — a
running task carries no ``output`` block, and a failed task carries
``errorMessage`` instead.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateTaskOutput",
    "GeneratePagesOutput",
    "GetTaskOutput",
    "TaskPage",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TaskPage(_Base):
    """A page created, modified, or deleted by an agent task."""

    slug: str | None = None
    preview_url: str | None = None
    edit_url: str | None = None
    published_url: str | None = None


class CreateTaskOutput(_Base):
    """Result of starting a prompt-driven agent task."""

    success: bool
    error: str | None = None
    task_id: str | None = None
    status: str | None = None
    created_at: str | None = None


class GeneratePagesOutput(_Base):
    """Result of starting a template page-generation task."""

    success: bool
    error: str | None = None
    task_id: str | None = None
    status: str | None = None
    created_at: str | None = None


class GetTaskOutput(_Base):
    """Status and results of a background agent task."""

    success: bool
    error: str | None = None
    task_id: str | None = None
    status: str | None = None
    pages_created: list[TaskPage] = Field(default_factory=list)
    pages_modified: list[TaskPage] = Field(default_factory=list)
    pages_deleted: list[TaskPage] = Field(default_factory=list)
    error_message: str | None = None
