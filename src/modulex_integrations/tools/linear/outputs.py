"""Pydantic response models for the Linear integration.

Linear returns deeply-nested GraphQL responses (issues with state +
team + assignee + creator + labels.nodes; projects with status +
lead). We keep these on a single open ``dict[str, Any]`` per object
rather than re-modelling every field, mirroring legacy's
forward-the-upstream approach.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateIssueOutput",
    "CreateProjectOutput",
    "GetIssueOutput",
    "GetTeamsOutput",
    "ListProjectsOutput",
    "SearchIssuesOutput",
    "UpdateIssueOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class _PagedListBase(_Base):
    count: int = 0
    page_info: dict[str, Any] | None = None


class GetTeamsOutput(_PagedListBase):
    teams: list[dict[str, Any]] = Field(default_factory=list)


class GetIssueOutput(_Base):
    issue: dict[str, Any] | None = None


class SearchIssuesOutput(_PagedListBase):
    issues: list[dict[str, Any]] = Field(default_factory=list)


class CreateIssueOutput(_Base):
    issue: dict[str, Any] | None = None


class UpdateIssueOutput(_Base):
    issue: dict[str, Any] | None = None


class ListProjectsOutput(_PagedListBase):
    projects: list[dict[str, Any]] = Field(default_factory=list)


class CreateProjectOutput(_Base):
    project: dict[str, Any] | None = None
