"""Pydantic response models for the motion integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateTaskOutput",
    "DeleteTaskOutput",
    "GetSchedulesOutput",
    "GetTaskOutput",
    "MoveWorkspaceOutput",
    "ScheduleItem",
    "TaskObject",
    "TaskStatus",
    "UpdateTaskOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class TaskStatus(_Base):
    """Status information for a task."""

    name: str | None = None
    is_default_status: bool | None = None
    is_resolved_status: bool | None = None


class TaskObject(_Base):
    """A Motion task object returned by task-related actions."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    priority: str | None = None
    assignee_id: str | None = None
    labels: list[str] = Field(default_factory=list)
    due_date: str | None = None
    duration: str | None = None
    created_at: str | None = None


class ScheduleItem(_Base):
    """A schedule object returned by the get_schedules action."""

    id: str | None = None
    name: str | None = None
    timezone: str | None = None
    is_default: bool | None = None


# --- Per-action output models ----------------------------------------------


class CreateTaskOutput(_Base):
    success: bool
    error: str | None = None
    task: TaskObject | None = None


class DeleteTaskOutput(_Base):
    success: bool
    error: str | None = None


class GetSchedulesOutput(_Base):
    success: bool
    error: str | None = None
    schedules: list[ScheduleItem] = Field(default_factory=list)


class GetTaskOutput(_Base):
    success: bool
    error: str | None = None
    task: TaskObject | None = None


class MoveWorkspaceOutput(_Base):
    success: bool
    error: str | None = None
    task: TaskObject | None = None


class UpdateTaskOutput(_Base):
    success: bool
    error: str | None = None
    task: TaskObject | None = None
