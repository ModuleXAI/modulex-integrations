"""Pydantic response models for the google_tag_manager integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AccountItem",
    "CreateTagOutput",
    "GetTagOutput",
    "GetTagsOutput",
    "ListAccountIdOptionsOutput",
    "TagResource",
    "UpdateTagOutput",
    "UpdateVariableOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class TagResource(_Base):
    """A Google Tag Manager tag resource."""

    tag_id: str | None = None
    name: str | None = None
    type: str | None = None
    live_only: bool | None = None
    notes: str | None = None
    parameter: list[dict[str, Any]] = Field(default_factory=list)
    fingerprint: str | None = None
    tag_manager_url: str | None = None
    path: str | None = None
    account_id: str | None = None
    container_id: str | None = None
    workspace_id: str | None = None


class AccountItem(_Base):
    """A Google Tag Manager account."""

    account_id: str | None = None
    name: str | None = None
    share_data: bool | None = None
    fingerprint: str | None = None
    path: str | None = None
    tag_manager_url: str | None = None


# --- Per-action output models ----------------------------------------------


class CreateTagOutput(_Base):
    success: bool
    tag: TagResource | None = None


class GetTagOutput(_Base):
    success: bool
    tag: TagResource | None = None


class GetTagsOutput(_Base):
    success: bool
    tags: list[TagResource] = Field(default_factory=list)


class ListAccountIdOptionsOutput(_Base):
    success: bool
    accounts: list[AccountItem] = Field(default_factory=list)


class UpdateTagOutput(_Base):
    success: bool
    tag: TagResource | None = None


class UpdateVariableOutput(_Base):
    success: bool
    data: dict[str, Any] | None = None
