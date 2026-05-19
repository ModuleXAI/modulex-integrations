"""Pydantic response models for the mailgun integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateMailinglistMemberOutput",
    "CreateRouteOutput",
    "DeleteMailinglistMemberOutput",
    "DomainSummary",
    "EmailVerificationResult",
    "ListDomainsOutput",
    "ListMailinglistMembersOutput",
    "MailinglistMember",
    "RetrieveMailinglistMemberOutput",
    "SendEmailOutput",
    "SuppressEmailOutput",
    "VerifyEmailOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class EmailVerificationResult(_Base):
    address: str | None = None
    did_you_mean: str | None = None
    is_disposable_address: bool | None = None
    is_role_address: bool | None = None
    reason: list[str] = Field(default_factory=list)
    result: str | None = None
    risk: str | None = None


class DomainSummary(_Base):
    name: str | None = None
    state: str | None = None
    type: str | None = None
    created_at: str | None = None
    smtp_login: str | None = None
    web_prefix: str | None = None


class MailinglistMember(_Base):
    address: str | None = None
    name: str | None = None
    subscribed: bool | None = None
    vars: dict[str, str | int | float | bool | None] | None = None


# --- Per-action output models ---------------------------------------------


class SendEmailOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    message: str | None = None


class VerifyEmailOutput(_Base):
    success: bool
    error: str | None = None
    verification: EmailVerificationResult | None = None


class CreateMailinglistMemberOutput(_Base):
    success: bool
    error: str | None = None
    member: MailinglistMember | None = None


class CreateRouteOutput(_Base):
    success: bool
    error: str | None = None
    route_id: str | None = None
    route_message: str | None = None


class DeleteMailinglistMemberOutput(_Base):
    success: bool
    error: str | None = None
    member_address: str | None = None
    message: str | None = None


class ListDomainsOutput(_Base):
    success: bool
    error: str | None = None
    domains: list[DomainSummary] = Field(default_factory=list)
    total_count: int | None = None


class ListMailinglistMembersOutput(_Base):
    success: bool
    error: str | None = None
    members: list[MailinglistMember] = Field(default_factory=list)
    total_count: int | None = None


class RetrieveMailinglistMemberOutput(_Base):
    success: bool
    error: str | None = None
    member: MailinglistMember | None = None


class SuppressEmailOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
