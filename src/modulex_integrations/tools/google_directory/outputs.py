"""Pydantic response models for the google_directory integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddMemberToGroupOutput",
    "CreateGroupOutput",
    "CreateUserOutput",
    "GetGroupOutput",
    "GetUserOutput",
    "GroupResource",
    "ListGroupsOutput",
    "ListUsersOutput",
    "MemberResource",
    "UserResource",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class MemberResource(_Base):
    """A Google Directory group member."""

    id: str | None = None
    email: str | None = None
    role: str | None = None
    type: str | None = None
    status: str | None = None
    kind: str | None = None
    etag: str | None = None


class GroupResource(_Base):
    """A Google Directory group."""

    id: str | None = None
    email: str | None = None
    name: str | None = None
    description: str | None = None
    direct_members_count: str | None = None
    kind: str | None = None
    etag: str | None = None
    admin_created: bool | None = None


class UserResource(_Base):
    """A Google Directory user."""

    id: str | None = None
    primary_email: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    is_admin: bool | None = None
    is_delegated_admin: bool | None = None
    kind: str | None = None
    etag: str | None = None
    creation_time: str | None = None
    org_unit_path: str | None = None


# --- Per-action output models ----------------------------------------------


class AddMemberToGroupOutput(_Base):
    success: bool
    member: MemberResource | None = None


class CreateGroupOutput(_Base):
    success: bool
    group: GroupResource | None = None


class CreateUserOutput(_Base):
    success: bool
    user: UserResource | None = None


class GetGroupOutput(_Base):
    success: bool
    group: GroupResource | None = None


class GetUserOutput(_Base):
    success: bool
    user: UserResource | None = None


class ListGroupsOutput(_Base):
    success: bool
    groups: list[GroupResource] = Field(default_factory=list)


class ListUsersOutput(_Base):
    success: bool
    users: list[UserResource] = Field(default_factory=list)
