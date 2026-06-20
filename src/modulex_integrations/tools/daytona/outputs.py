"""Pydantic response models for the Daytona integration's @tool functions.

Daytona follows the modulex *api_key* runtime convention: each function
signature takes ``api_key: str`` directly, and the modulex
``ToolExecutor`` injects it from the resolved credential.

Error model: every call is wrapped in try/except, so non-2xx HTTP
responses, timeouts, and unexpected exceptions surface as
``success=False`` + ``error`` rather than raising. Every output model
carries both shapes; data fields stay at their defaults on failure.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateSandboxOutput",
    "DeleteSandboxOutput",
    "DownloadFileOutput",
    "ExecuteCommandOutput",
    "FileInfo",
    "GetSandboxOutput",
    "GitCloneOutput",
    "ListFilesOutput",
    "ListSandboxesOutput",
    "RunCodeOutput",
    "SandboxSummary",
    "StartSandboxOutput",
    "StopSandboxOutput",
    "UploadFileOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class SandboxSummary(_Base):
    """Normalized summary of a Daytona sandbox."""

    id: str | None = None
    name: str | None = None
    state: str | None = None
    snapshot: str | None = None
    target: str | None = None
    cpu: int | None = None
    gpu: int | None = None
    memory: int | None = None
    disk: int | None = None
    labels: dict[str, Any] = Field(default_factory=dict)
    public: bool | None = None
    error_reason: str | None = None
    auto_stop_interval: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class FileInfo(_Base):
    """A single entry returned by ``list_files``."""

    name: str | None = None
    is_dir: bool | None = None
    size: int | None = None
    mode: str | None = None
    permissions: str | None = None
    owner: str | None = None
    group: str | None = None
    modified_at: str | None = None


# --- Per-action output models ----------------------------------------------


class CreateSandboxOutput(_Base):
    success: bool
    error: str | None = None
    sandbox: SandboxSummary | None = None


class ListSandboxesOutput(_Base):
    success: bool
    error: str | None = None
    sandboxes: list[SandboxSummary] = Field(default_factory=list)
    next_cursor: str | None = None


class GetSandboxOutput(_Base):
    success: bool
    error: str | None = None
    sandbox: SandboxSummary | None = None


class StartSandboxOutput(_Base):
    success: bool
    error: str | None = None
    sandbox: SandboxSummary | None = None


class StopSandboxOutput(_Base):
    success: bool
    error: str | None = None
    sandbox: SandboxSummary | None = None


class DeleteSandboxOutput(_Base):
    success: bool
    error: str | None = None
    sandbox: SandboxSummary | None = None


class ExecuteCommandOutput(_Base):
    success: bool
    error: str | None = None
    exit_code: int | None = None
    result: str | None = None


class RunCodeOutput(_Base):
    success: bool
    error: str | None = None
    exit_code: int | None = None
    result: str | None = None
    artifacts: dict[str, Any] | None = None


class UploadFileOutput(_Base):
    success: bool
    error: str | None = None
    uploaded_path: str | None = None
    name: str | None = None
    size: int | None = None


class DownloadFileOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    mime_type: str | None = None
    size: int | None = None
    content_base64: str | None = None


class ListFilesOutput(_Base):
    success: bool
    error: str | None = None
    files: list[FileInfo] = Field(default_factory=list)


class GitCloneOutput(_Base):
    success: bool
    error: str | None = None
    repo_url: str | None = None
    clone_path: str | None = None
