"""Pydantic response models for the linkedin integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateCommentOutput",
    "CreateImagePostOrganizationOutput",
    "CreateImagePostUserOutput",
    "CreateLikeOnShareOutput",
    "CreateTextPostOrganizationOutput",
    "CreateTextPostUserOutput",
    "DeletePostOutput",
    "FetchAdAccountOutput",
    "GetCurrentMemberProfileOutput",
    "GetMemberProfileOutput",
    "GetMultipleMemberProfilesOutput",
    "GetOrgMemberAccessOutput",
    "GetOrganizationAccessControlOutput",
    "GetOrganizationAdministratorsOutput",
    "GetProfilePictureFieldsOutput",
    "RetrieveCommentsOnCommentsOutput",
    "RetrieveCommentsSharesOutput",
    "SearchOrganizationOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Per-action output models ------------------------------------------------


class CreateCommentOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateImagePostOrganizationOutput(_Base):
    success: bool
    error: str | None = None
    post_urn: str | None = None


class CreateImagePostUserOutput(_Base):
    success: bool
    error: str | None = None
    post_urn: str | None = None


class CreateLikeOnShareOutput(_Base):
    success: bool
    error: str | None = None


class CreateTextPostOrganizationOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateTextPostUserOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class DeletePostOutput(_Base):
    success: bool
    error: str | None = None


class FetchAdAccountOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetCurrentMemberProfileOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetMemberProfileOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetMultipleMemberProfilesOutput(_Base):
    success: bool
    error: str | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)


class GetOrgMemberAccessOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetOrganizationAccessControlOutput(_Base):
    success: bool
    error: str | None = None
    elements: list[dict[str, Any]] = Field(default_factory=list)


class GetOrganizationAdministratorsOutput(_Base):
    success: bool
    error: str | None = None
    elements: list[dict[str, Any]] = Field(default_factory=list)


class GetProfilePictureFieldsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class RetrieveCommentsOnCommentsOutput(_Base):
    success: bool
    error: str | None = None
    elements: list[dict[str, Any]] = Field(default_factory=list)


class RetrieveCommentsSharesOutput(_Base):
    success: bool
    error: str | None = None
    elements: list[dict[str, Any]] = Field(default_factory=list)


class SearchOrganizationOutput(_Base):
    success: bool
    error: str | None = None
    elements: list[dict[str, Any]] = Field(default_factory=list)
