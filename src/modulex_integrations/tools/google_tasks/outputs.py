"""Pydantic response models for the google_tasks integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateTaskListOutput",
    "CreateTaskOutput",
    "DeleteTaskListOutput",
    "DeleteTaskOutput",
    "ListTaskListsOutput",
    "ListTasksOutput",
    "TaskItem",
    "TaskListItem",
    "UpdateTaskListOutput",
    "UpdateTaskOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class TaskItem(_Base):
    """A Google Tasks task resource."""

    id: str | None = None
    title: str | None = None
    notes: str | None = None
    status: str | None = None
    due: str | None = None
    updated: str | None = None
    self_link: str | None = None
    etag: str | None = None
    kind: str | None = None


class TaskListItem(_Base):
    """A Google Tasks task list resource."""

    id: str | None = None
    title: str | None = None
    updated: str | None = None
    self_link: str | None = None
    etag: str | None = None
    kind: str | None = None


# --- Per-action output models ----------------------------------------------


class CreateTaskOutput(_Base):
    success: bool
    error: str | None = None
    task: TaskItem | None = None


class CreateTaskListOutput(_Base):
    success: bool
    error: str | None = None
    task_list: TaskListItem | None = None


class DeleteTaskOutput(_Base):
    success: bool
    error: str | None = None


class DeleteTaskListOutput(_Base):
    success: bool
    error: str | None = None


class ListTasksOutput(_Base):
    success: bool
    error: str | None = None
    tasks: list[TaskItem] = Field(default_factory=list)


class ListTaskListsOutput(_Base):
    success: bool
    error: str | None = None
    task_lists: list[TaskListItem] = Field(default_factory=list)


class UpdateTaskOutput(_Base):
    success: bool
    error: str | None = None
    task: TaskItem | None = None


class UpdateTaskListOutput(_Base):
    success: bool
    error: str | None = None
    task_list: TaskListItem | None = None
