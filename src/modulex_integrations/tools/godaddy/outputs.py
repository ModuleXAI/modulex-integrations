"""Pydantic response models for the godaddy integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CheckDomainAvailabilityOutput",
    "DomainSummary",
    "ListDomainsOutput",
    "ListTldsOptionsOutput",
    "RenewDomainOutput",
    "SuggestDomainsOutput",
    "TldInfo",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class DomainSummary(_Base):
    """A domain summary object from the list domains endpoint."""

    domain: str | None = None
    status: str | None = None
    expires: str | None = None
    created_at: str | None = None
    renewable: bool | None = None


class TldInfo(_Base):
    """A TLD entry from the list TLDs endpoint."""

    name: str | None = None
    type: str | None = None


# --- Per-action output models ----------------------------------------------


class CheckDomainAvailabilityOutput(_Base):
    success: bool
    error: str | None = None
    available: bool | None = None
    domain: str | None = None
    definitive: bool | None = None
    price: int | None = None
    currency: str | None = None
    period: int | None = None


class ListDomainsOutput(_Base):
    success: bool
    error: str | None = None
    domains: list[DomainSummary] = Field(default_factory=list)


class ListTldsOptionsOutput(_Base):
    success: bool
    error: str | None = None
    tlds: list[TldInfo] = Field(default_factory=list)


class RenewDomainOutput(_Base):
    success: bool
    error: str | None = None
    order_id: int | None = None
    item_count: int | None = None
    total: int | None = None
    currency: str | None = None


class SuggestDomainsOutput(_Base):
    success: bool
    error: str | None = None
    suggestions: list[dict[str, Any]] = Field(default_factory=list)
