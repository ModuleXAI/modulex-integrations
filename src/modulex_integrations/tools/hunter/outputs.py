"""Pydantic response models for the hunter integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AccountInformationOutput",
    "CombinedEnrichmentOutput",
    "CreateLeadOutput",
    "DeleteLeadOutput",
    "DomainSearchOutput",
    "EmailCountOutput",
    "EmailFinderOutput",
    "EmailVerifierOutput",
    "GetLeadOutput",
    "GetLeadsListOutput",
    "ListLeadsListsOutput",
    "ListLeadsOutput",
    "UpdateLeadOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class AccountInformationOutput(_Base):
    success: bool
    error: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    plan_name: str | None = None
    plan_level: int | None = None
    reset_date: str | None = None
    team_id: int | None = None
    calls_used: int | None = None
    calls_available: int | None = None


class CombinedEnrichmentOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateLeadOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class DeleteLeadOutput(_Base):
    success: bool
    error: str | None = None


class DomainSearchOutput(_Base):
    success: bool
    error: str | None = None
    domain: str | None = None
    disposable: bool | None = None
    webmail: bool | None = None
    accept_all: bool | None = None
    pattern: str | None = None
    organization: str | None = None
    emails: list[dict[str, Any]] = Field(default_factory=list)
    total_results: int | None = None


class EmailCountOutput(_Base):
    success: bool
    error: str | None = None
    total: int | None = None
    personal_emails: int | None = None
    generic_emails: int | None = None
    department: dict[str, Any] | None = None


class EmailFinderOutput(_Base):
    success: bool
    error: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    score: int | None = None
    domain: str | None = None
    accept_all: bool | None = None
    position: str | None = None
    twitter: str | None = None
    linkedin_url: str | None = None
    phone_number: str | None = None
    company: str | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)


class EmailVerifierOutput(_Base):
    success: bool
    error: str | None = None
    status: str | None = None
    result: str | None = None
    score: int | None = None
    email: str | None = None
    regexp: bool | None = None
    gibberish: bool | None = None
    disposable: bool | None = None
    webmail: bool | None = None
    mx_records: bool | None = None
    smtp_server: bool | None = None
    smtp_check: bool | None = None
    accept_all: bool | None = None
    block: bool | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)


class GetLeadOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    position: str | None = None
    company: str | None = None


class GetLeadsListOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    name: str | None = None
    leads: list[dict[str, Any]] = Field(default_factory=list)


class ListLeadsListsOutput(_Base):
    success: bool
    error: str | None = None
    leads_lists: list[dict[str, Any]] = Field(default_factory=list)


class ListLeadsOutput(_Base):
    success: bool
    error: str | None = None
    leads: list[dict[str, Any]] = Field(default_factory=list)
    total: int | None = None


class UpdateLeadOutput(_Base):
    success: bool
    error: str | None = None
