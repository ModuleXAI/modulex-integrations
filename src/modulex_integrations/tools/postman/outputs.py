"""Pydantic response models for the postman integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateEnvironmentOutput",
    "ListWorkspaceIdOptionsOutput",
    "RunMonitorOutput",
    "UpdateVariableOutput",
    "WorkspaceSummary",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class WorkspaceSummary(_Base):
    id: str | None = None
    name: str | None = None
    type: str | None = None


# --- Per-action output models ---------------------------------------------


class CreateEnvironmentOutput(_Base):
    success: bool
    error: str | None = None
    environment_id: str | None = None
    environment_name: str | None = None


class ListWorkspaceIdOptionsOutput(_Base):
    success: bool
    error: str | None = None
    workspaces: list[WorkspaceSummary] = Field(default_factory=list)


class RunMonitorOutput(_Base):
    success: bool
    error: str | None = None
    run: dict[str, Any] | None = None


class UpdateVariableOutput(_Base):
    success: bool
    error: str | None = None
    environment_id: str | None = None
    environment_name: str | None = None
