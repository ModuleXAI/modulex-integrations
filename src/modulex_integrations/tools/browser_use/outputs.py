"""Pydantic response models for the browser_use integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateBrowserSessionOutput",
    "CreateProfileOutput",
    "CreateSessionOutput",
    "CreateWorkspaceOutput",
    "DeleteProfileOutput",
    "DeleteSessionOutput",
    "DeleteWorkspaceFileOutput",
    "DeleteWorkspaceOutput",
    "GetAccountBillingOutput",
    "GetBrowserSessionOutput",
    "GetProfileOutput",
    "GetSessionOutput",
    "GetWorkspaceOutput",
    "GetWorkspaceSizeOutput",
    "ListBrowserSessionsOutput",
    "ListProfilesOutput",
    "ListSessionMessagesOutput",
    "ListSessionsOutput",
    "ListWorkspaceFilesOutput",
    "ListWorkspacesOutput",
    "StopSessionOutput",
    "UpdateBrowserSessionOutput",
    "UpdateProfileOutput",
    "UpdateWorkspaceOutput",
    "UploadWorkspaceFilesOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class CreateSessionOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    status: str | None = None
    task: str | None = None
    live_url: str | None = None
    data: dict[str, Any] | None = None


class GetSessionOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    status: str | None = None
    task: str | None = None
    output: str | None = None
    live_url: str | None = None
    screenshot_url: str | None = None
    cost: float | None = None
    data: dict[str, Any] | None = None


class ListSessionsOutput(_Base):
    success: bool
    error: str | None = None
    sessions: list[dict[str, Any]] = Field(default_factory=list)
    total: int | None = None


class DeleteSessionOutput(_Base):
    success: bool
    error: str | None = None


class StopSessionOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class ListSessionMessagesOutput(_Base):
    success: bool
    error: str | None = None
    messages: list[dict[str, Any]] = Field(default_factory=list)


class CreateBrowserSessionOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    status: str | None = None
    live_url: str | None = None
    cdp_url: str | None = None
    data: dict[str, Any] | None = None


class GetBrowserSessionOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    status: str | None = None
    live_url: str | None = None
    cdp_url: str | None = None
    timeout: int | None = None
    cost: float | None = None
    data: dict[str, Any] | None = None


class ListBrowserSessionsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    total_items: int | None = None


class UpdateBrowserSessionOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateProfileOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    data: dict[str, Any] | None = None


class GetProfileOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    user_id: str | None = None
    data: dict[str, Any] | None = None


class ListProfilesOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    total_items: int | None = None


class DeleteProfileOutput(_Base):
    success: bool
    error: str | None = None


class UpdateProfileOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    user_id: str | None = None
    data: dict[str, Any] | None = None


class CreateWorkspaceOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    data: dict[str, Any] | None = None


class GetWorkspaceOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    data: dict[str, Any] | None = None


class ListWorkspacesOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    total_items: int | None = None


class DeleteWorkspaceOutput(_Base):
    success: bool
    error: str | None = None


class UpdateWorkspaceOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    data: dict[str, Any] | None = None


class GetWorkspaceSizeOutput(_Base):
    success: bool
    error: str | None = None
    size_bytes: int | None = None
    data: dict[str, Any] | None = None


class ListWorkspaceFilesOutput(_Base):
    success: bool
    error: str | None = None
    files: list[dict[str, Any]] = Field(default_factory=list)
    cursor: str | None = None


class DeleteWorkspaceFileOutput(_Base):
    success: bool
    error: str | None = None


class UploadWorkspaceFilesOutput(_Base):
    success: bool
    error: str | None = None
    files: list[dict[str, Any]] = Field(default_factory=list)


class GetAccountBillingOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None
