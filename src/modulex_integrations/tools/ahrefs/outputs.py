"""Pydantic response models for the ahrefs integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "BacklinkItem",
    "GetBacklinksOnePerDomainOutput",
    "GetBacklinksOutput",
    "GetReferringDomainsOutput",
    "ReferringDomainItem",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class BacklinkItem(_Base):
    """A single backlink record returned by the Ahrefs API."""

    url_from: str | None = None
    url_to: str | None = None
    ahrefs_rank: int | None = None
    anchor: str | None = None
    page_title: str | None = None
    first_seen: str | None = None
    last_seen: str | None = None
    domain_rating: float | None = None
    extra: dict[str, Any] | None = Field(default=None, description="Additional fields returned by the API based on the select parameter")


class ReferringDomainItem(_Base):
    """A single referring domain record returned by the Ahrefs API."""

    domain: str | None = None
    domain_rating: float | None = None
    backlinks: int | None = None
    first_seen: str | None = None
    last_seen: str | None = None
    extra: dict[str, Any] | None = Field(default=None, description="Additional fields returned by the API based on the select parameter")


class GetBacklinksOutput(_Base):
    success: bool
    error: str | None = None
    backlinks: list[BacklinkItem] = Field(default_factory=list)
    total: int | None = None


class GetBacklinksOnePerDomainOutput(_Base):
    success: bool
    error: str | None = None
    backlinks: list[BacklinkItem] = Field(default_factory=list)
    total: int | None = None


class GetReferringDomainsOutput(_Base):
    success: bool
    error: str | None = None
    refdomains: list[ReferringDomainItem] = Field(default_factory=list)
    total: int | None = None
