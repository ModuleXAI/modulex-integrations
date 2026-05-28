"""Pydantic response models for the netlify integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "GetSiteOutput",
    "ListFilesOutput",
    "ListSiteDeploysOutput",
    "RollbackDeployOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class GetSiteOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    url: str | None = None
    ssl_url: str | None = None
    admin_url: str | None = None
    state: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    default_domain: str | None = None
    custom_domain: str | None = None


class ListFilesOutput(_Base):
    success: bool
    error: str | None = None
    files: list[dict[str, Any]] = Field(default_factory=list)


class ListSiteDeploysOutput(_Base):
    success: bool
    error: str | None = None
    deploys: list[dict[str, Any]] = Field(default_factory=list)


class RollbackDeployOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    state: str | None = None
    name: str | None = None
    url: str | None = None
    ssl_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
