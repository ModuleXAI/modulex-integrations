"""Pydantic response models for the gong integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddNewCallOutput",
    "GetExtensiveDataOutput",
    "ListCallsOutput",
    "ListWorkspaceIdOptionsOutput",
    "RetrieveTranscriptsOfCallsOutput",
    "Workspace",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class Workspace(_Base):
    """A Gong workspace entry."""

    id: str | None = None
    name: str | None = None


# --- Per-action output models ---------------------------------------------


class AddNewCallOutput(_Base):
    success: bool
    error: str | None = None
    request_id: str | None = None
    call_id: str | None = None


class GetExtensiveDataOutput(_Base):
    success: bool
    error: str | None = None
    calls: list[dict[str, Any]] = Field(default_factory=list)


class ListCallsOutput(_Base):
    success: bool
    error: str | None = None
    request_id: str | None = None
    cursor: str | None = None
    calls: list[dict[str, Any]] = Field(default_factory=list)


class ListWorkspaceIdOptionsOutput(_Base):
    success: bool
    error: str | None = None
    workspaces: list[Workspace] = Field(default_factory=list)


class RetrieveTranscriptsOfCallsOutput(_Base):
    success: bool
    error: str | None = None
    call_transcripts: list[dict[str, Any]] = Field(default_factory=list)
