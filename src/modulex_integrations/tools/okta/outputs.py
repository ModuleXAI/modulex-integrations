"""Pydantic response models for the okta integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateUserOutput",
    "GetUserOutput",
    "ListTypeIdOptionsOutput",
    "TypeIdOption",
    "UpdateUserOutput",
    "UserResource",
    "UserTypeRef",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# --- Nested resource models ------------------------------------------------


class UserTypeRef(_Base):
    """Reference to a user type returned alongside a user resource."""

    id: str | None = None


class UserResource(_Base):
    """An Okta user as returned by /users endpoints.

    Field set is intentionally permissive — Okta returns many fields; we
    expose the ones agents commonly need and let the rest live in ``profile``.
    """

    id: str | None = None
    status: str | None = None
    created: str | None = None
    activated: str | None = None
    status_changed: str | None = Field(default=None, alias="statusChanged")
    last_login: str | None = Field(default=None, alias="lastLogin")
    last_updated: str | None = Field(default=None, alias="lastUpdated")
    password_changed: str | None = Field(default=None, alias="passwordChanged")
    type: UserTypeRef | None = None
    profile: dict[str, object] | None = None
    credentials: dict[str, object] | None = None


class TypeIdOption(_Base):
    """One row from the dropdown returned by list_type_id_options."""

    label: str | None = None
    value: str | None = None


# --- Per-action output models ----------------------------------------------


class CreateUserOutput(_Base):
    success: bool
    error: str | None = None
    user: UserResource | None = None


class GetUserOutput(_Base):
    success: bool
    error: str | None = None
    user: UserResource | None = None


class ListTypeIdOptionsOutput(_Base):
    success: bool
    error: str | None = None
    options: list[TypeIdOption] = Field(default_factory=list)


class UpdateUserOutput(_Base):
    success: bool
    error: str | None = None
    user: UserResource | None = None
