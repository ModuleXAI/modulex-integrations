"""Pydantic response models for the ClickUp integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddTagToTaskOutput",
    "CreateFolderOutput",
    "CreateListOutput",
    "CreateSpaceOutput",
    "CreateTaskCommentOutput",
    "CreateTaskOutput",
    "DeleteFolderOutput",
    "DeleteTaskOutput",
    "GetFolderOutput",
    "GetFoldersOutput",
    "GetListOutput",
    "GetListsOutput",
    "GetSpaceOutput",
    "GetSpaceTagsOutput",
    "GetSpacesOutput",
    "GetTaskCommentsOutput",
    "GetTaskOutput",
    "GetTasksOutput",
    "GetTeamMembersOutput",
    "GetTeamsOutput",
    "RemoveTagFromTaskOutput",
    "SearchTasksOutput",
    "UpdateTaskOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


# --- Listing outputs (object-type-keyed) ---


class GetTeamsOutput(_Base):
    teams: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class GetSpacesOutput(_Base):
    spaces: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    team_id: str | None = None


class GetSpaceOutput(_Base):
    result: dict[str, Any] | None = None


class CreateSpaceOutput(_Base):
    result: dict[str, Any] | None = None


class GetFoldersOutput(_Base):
    folders: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    space_id: str | None = None


class GetFolderOutput(_Base):
    result: dict[str, Any] | None = None


class CreateFolderOutput(_Base):
    result: dict[str, Any] | None = None


class DeleteFolderOutput(_Base):
    deleted: bool = False
    folder_id: str | None = None


class GetListsOutput(_Base):
    lists: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    folder_id: str | None = None
    space_id: str | None = None


class GetListOutput(_Base):
    result: dict[str, Any] | None = None


class CreateListOutput(_Base):
    result: dict[str, Any] | None = None


class GetTasksOutput(_Base):
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    list_id: str | None = None


class GetTaskOutput(_Base):
    result: dict[str, Any] | None = None


class CreateTaskOutput(_Base):
    result: dict[str, Any] | None = None


class UpdateTaskOutput(_Base):
    result: dict[str, Any] | None = None


class DeleteTaskOutput(_Base):
    deleted: bool = False
    task_id: str | None = None


class GetTaskCommentsOutput(_Base):
    comments: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    task_id: str | None = None


class CreateTaskCommentOutput(_Base):
    result: dict[str, Any] | None = None


class SearchTasksOutput(_Base):
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    team_id: str | None = None


class GetSpaceTagsOutput(_Base):
    tags: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    space_id: str | None = None


class AddTagToTaskOutput(_Base):
    added: bool = False
    task_id: str | None = None
    tag_name: str | None = None


class RemoveTagFromTaskOutput(_Base):
    removed: bool = False
    task_id: str | None = None
    tag_name: str | None = None


class GetTeamMembersOutput(_Base):
    members: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    team_id: str | None = None
