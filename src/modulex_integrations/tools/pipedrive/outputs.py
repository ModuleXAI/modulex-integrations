"""Pydantic response models for the pipedrive integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddActivityOutput",
    "AddDealOutput",
    "AddLabelsOutput",
    "AddLeadOutput",
    "AddNoteOutput",
    "AddOrganizationOutput",
    "AddPersonOutput",
    "GetAllLeadsOutput",
    "GetDealOutput",
    "GetLeadByIdOutput",
    "GetPersonDetailsOutput",
    "LabelOption",
    "LeadItem",
    "ListDealsOutput",
    "ListLeadLabelIdsOptionsOutput",
    "ListOrganizationLabelIdsOptionsOutput",
    "ListPersonLabelIdsOptionsOutput",
    "ListUserIdOptionsOutput",
    "MergeDealsOutput",
    "MergePersonsOutput",
    "RemoveDuplicateNotesOutput",
    "RemoveLabelsOutput",
    "SearchLeadsOutput",
    "SearchNotesOutput",
    "SearchPersonsOutput",
    "UpdateDealOutput",
    "UpdateLeadOutput",
    "UpdatePersonOutput",
    "UserOption",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class LabelOption(_Base):
    label: str | None = None
    value: str | None = None


class UserOption(_Base):
    label: str | None = None
    value: int | None = None


class LeadItem(_Base):
    id: str | None = None
    title: str | None = None
    owner_id: int | None = None
    person_id: int | None = None
    organization_id: int | None = None
    was_seen: bool | None = None
    expected_close_date: str | None = None
    add_time: str | None = None
    update_time: str | None = None


class AddActivityOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class AddDealOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class AddLabelsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class AddLeadOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class AddNoteOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class AddOrganizationOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class AddPersonOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetAllLeadsOutput(_Base):
    success: bool
    error: str | None = None
    leads: list[LeadItem] = Field(default_factory=list)
    total: int = 0


class GetDealOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetLeadByIdOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetPersonDetailsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class ListDealsOutput(_Base):
    success: bool
    error: str | None = None
    deals: list[dict[str, Any]] = Field(default_factory=list)
    cursor: str | None = None


class ListLeadLabelIdsOptionsOutput(_Base):
    success: bool
    error: str | None = None
    options: list[LabelOption] = Field(default_factory=list)


class ListOrganizationLabelIdsOptionsOutput(_Base):
    success: bool
    error: str | None = None
    options: list[LabelOption] = Field(default_factory=list)


class ListPersonLabelIdsOptionsOutput(_Base):
    success: bool
    error: str | None = None
    options: list[LabelOption] = Field(default_factory=list)


class ListUserIdOptionsOutput(_Base):
    success: bool
    error: str | None = None
    options: list[UserOption] = Field(default_factory=list)


class MergeDealsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class MergePersonsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class RemoveDuplicateNotesOutput(_Base):
    success: bool
    error: str | None = None
    total_notes: int = 0
    duplicates_found: int = 0
    duplicates_removed: list[dict[str, Any]] = Field(default_factory=list)


class RemoveLabelsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class SearchLeadsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class SearchNotesOutput(_Base):
    success: bool
    error: str | None = None
    notes: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class SearchPersonsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class UpdateDealOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class UpdateLeadOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class UpdatePersonOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None
