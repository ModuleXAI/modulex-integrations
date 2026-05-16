"""Pydantic response models for the Klaviyo integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddMembersToListOutput",
    "CreateListOutput",
    "GetListOutput",
    "GetListsOutput",
    "GetProfilesOutput",
    "KlaviyoList",
    "KlaviyoProfile",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class KlaviyoList(_Base):
    id: str | None = None
    name: str | None = None
    created: str | None = None
    updated: str | None = None
    opt_in_process: str | None = None


class KlaviyoProfile(_Base):
    id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    created: str | None = None
    updated: str | None = None


class GetListsOutput(_Base):
    success: bool
    error: str | None = None
    lists: list[KlaviyoList] = Field(default_factory=list)
    count: int = 0


class GetListOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    created: str | None = None
    updated: str | None = None
    opt_in_process: str | None = None


class CreateListOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    created: str | None = None
    updated: str | None = None
    opt_in_process: str | None = None


class GetProfilesOutput(_Base):
    success: bool
    error: str | None = None
    profiles: list[KlaviyoProfile] = Field(default_factory=list)
    count: int = 0


class AddMembersToListOutput(_Base):
    success: bool
    error: str | None = None
    list_id: str | None = None
    profiles_added: int | None = None
    profile_ids: list[str] = Field(default_factory=list)
    # echo any extra payload bits without locking them down
    extra: dict[str, Any] | None = None
