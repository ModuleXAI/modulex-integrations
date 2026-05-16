"""Pydantic response models for the HubSpot integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateCompanyOutput",
    "CreateContactOutput",
    "CreateDealOutput",
    "CreateMeetingOutput",
    "CreateNoteOutput",
    "CreateTaskOutput",
    "CreateTicketOutput",
    "GetCompanyActivityOutput",
    "GetCompanyByIdOutput",
    "GetContactByIdOutput",
    "GetDealByIdOutput",
    "GetPropertyOutput",
    "GetRecentCompaniesOutput",
    "GetRecentContactsOutput",
    "GetRecentDealsOutput",
    "GetRecentTicketsOutput",
    "GetTicketByIdOutput",
    "ListPropertiesOutput",
    "SearchCompaniesOutput",
    "SearchContactsOutput",
    "SearchDealsOutput",
    "SearchTicketsOutput",
    "UpdateCompanyOutput",
    "UpdateContactOutput",
    "UpdateDealOutput",
    "UpdateTicketOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


# --- Listing outputs (object-type-keyed) ---

class GetRecentContactsOutput(_Base):
    contacts: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class SearchContactsOutput(_Base):
    contacts: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class GetContactByIdOutput(_Base):
    result: dict[str, Any] | None = None


class CreateContactOutput(_Base):
    result: dict[str, Any] | None = None


class UpdateContactOutput(_Base):
    result: dict[str, Any] | None = None


class GetRecentCompaniesOutput(_Base):
    companies: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class SearchCompaniesOutput(_Base):
    companies: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class GetCompanyByIdOutput(_Base):
    result: dict[str, Any] | None = None


class CreateCompanyOutput(_Base):
    result: dict[str, Any] | None = None


class UpdateCompanyOutput(_Base):
    result: dict[str, Any] | None = None


class GetCompanyActivityOutput(_Base):
    activities: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class GetRecentDealsOutput(_Base):
    deals: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class SearchDealsOutput(_Base):
    deals: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class GetDealByIdOutput(_Base):
    result: dict[str, Any] | None = None


class CreateDealOutput(_Base):
    result: dict[str, Any] | None = None


class UpdateDealOutput(_Base):
    result: dict[str, Any] | None = None


class GetRecentTicketsOutput(_Base):
    tickets: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class SearchTicketsOutput(_Base):
    tickets: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class GetTicketByIdOutput(_Base):
    result: dict[str, Any] | None = None


class CreateTicketOutput(_Base):
    result: dict[str, Any] | None = None


class UpdateTicketOutput(_Base):
    result: dict[str, Any] | None = None


class CreateNoteOutput(_Base):
    result: dict[str, Any] | None = None


class CreateTaskOutput(_Base):
    result: dict[str, Any] | None = None


class CreateMeetingOutput(_Base):
    result: dict[str, Any] | None = None


class GetPropertyOutput(_Base):
    result: dict[str, Any] | None = None


class ListPropertiesOutput(_Base):
    properties: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
