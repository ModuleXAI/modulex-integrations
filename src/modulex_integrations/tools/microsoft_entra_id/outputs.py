"""Pydantic response models for the microsoft_entra_id integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddMemberToGroupOutput",
    "CreateGroupOutput",
    "DeleteGroupOutput",
    "GetManagerOutput",
    "GetMs365GroupsOutput",
    "GetOrganizationGroupsOutput",
    "GetOrganizationUsersOutput",
    "GetProfileOutput",
    "GroupSummary",
    "ManagerInfo",
    "RemoveMemberFromGroupOutput",
    "SearchGroupsOutput",
    "UpdateGroupOutput",
    "UpdateUserOutput",
    "UserSummary",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class GroupSummary(_Base):
    id: str | None = None
    display_name: str | None = None
    description: str | None = None
    mail_enabled: bool | None = None
    mail_nickname: str | None = None
    security_enabled: bool | None = None
    group_types: list[str] = Field(default_factory=list)
    deleted_date_time: str | None = None


class UserSummary(_Base):
    id: str | None = None
    full_name: str | None = None
    description: str | None = None
    email: str | None = None
    user_principal_name: str | None = None
    surname: str | None = None
    given_name: str | None = None
    job_title: str | None = None
    mobile_phone: str | None = None


class ManagerInfo(_Base):
    id: str | None = None
    display_name: str | None = None
    email: str | None = None
    job_title: str | None = None
    mobile_phone: str | None = None


# --- Per-action output models ---------------------------------------------


class AddMemberToGroupOutput(_Base):
    success: bool
    error: str | None = None


class CreateGroupOutput(_Base):
    success: bool
    error: str | None = None
    group: GroupSummary | None = None


class DeleteGroupOutput(_Base):
    success: bool
    error: str | None = None


class GetManagerOutput(_Base):
    success: bool
    error: str | None = None
    manager: ManagerInfo | None = None
    message: str | None = None


class GetMs365GroupsOutput(_Base):
    success: bool
    error: str | None = None
    groups: list[GroupSummary] = Field(default_factory=list)


class GetOrganizationGroupsOutput(_Base):
    success: bool
    error: str | None = None
    groups: list[GroupSummary] = Field(default_factory=list)


class GetOrganizationUsersOutput(_Base):
    success: bool
    error: str | None = None
    users: list[UserSummary] = Field(default_factory=list)


class GetProfileOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, object] | None = None


class RemoveMemberFromGroupOutput(_Base):
    success: bool
    error: str | None = None


class SearchGroupsOutput(_Base):
    success: bool
    error: str | None = None
    groups: list[GroupSummary] = Field(default_factory=list)


class UpdateGroupOutput(_Base):
    success: bool
    error: str | None = None


class UpdateUserOutput(_Base):
    success: bool
    error: str | None = None
