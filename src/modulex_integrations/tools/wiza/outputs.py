"""Pydantic response models for the Wiza integration's @tool functions.

Wiza's tools follow the modulex *api_key* runtime convention: the
function signature takes ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair used by oauth/bearer tools), and the
modulex ``ToolExecutor`` injects it by reading the resolved ``api_key``
credential.

Error model: the tools wrap every call in try/except, returning the
typed output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions. Every output model therefore
carries both shapes — fields stay at their permissive defaults on the
failure branch.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CompanyEnrichmentOutput",
    "GetCreditsOutput",
    "IndividualRevealOutput",
    "ProspectProfile",
    "ProspectSearchOutput",
    "RevealEmail",
    "RevealPhone",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class ProspectProfile(_Base):
    """A single sample profile row in ``prospect_search``."""

    full_name: str | None = None
    linkedin_url: str | None = None
    industry: str | None = None
    job_title: str | None = None
    job_title_role: str | None = None
    job_title_sub_role: str | None = None
    job_company_name: str | None = None
    job_company_website: str | None = None
    location_name: str | None = None


class RevealEmail(_Base):
    """A single email entry in ``individual_reveal``'s ``emails`` list."""

    email: str | None = None
    email_type: str | None = None
    email_status: str | None = None


class RevealPhone(_Base):
    """A single phone entry in ``individual_reveal``'s ``phones`` list."""

    number: str | None = None
    pretty_number: str | None = None
    type: str | None = None


# --- Per-action output models ----------------------------------------------


class ProspectSearchOutput(_Base):
    success: bool
    error: str | None = None
    total: int | None = None
    profiles: list[ProspectProfile] = Field(default_factory=list)


class CompanyEnrichmentOutput(_Base):
    success: bool
    error: str | None = None
    company_name: str | None = None
    company_domain: str | None = None
    domain: str | None = None
    company_industry: str | None = None
    company_size: int | None = None
    company_size_range: str | None = None
    company_founded: int | None = None
    company_revenue_range: str | None = None
    company_funding: str | None = None
    company_type: str | None = None
    company_description: str | None = None
    company_ticker: str | None = None
    company_last_funding_round: str | None = None
    company_last_funding_amount: str | None = None
    company_last_funding_at: str | None = None
    company_location: str | None = None
    company_twitter: str | None = None
    company_facebook: str | None = None
    company_linkedin: str | None = None
    company_linkedin_id: str | None = None
    company_street: str | None = None
    company_locality: str | None = None
    company_region: str | None = None
    company_postal_code: str | None = None
    company_country: str | None = None
    credits: dict[str, Any] | None = None


class IndividualRevealOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    status: str | None = None
    is_complete: bool | None = None
    name: str | None = None
    company: str | None = None
    enrichment_level: str | None = None
    linkedin_profile_url: str | None = None
    title: str | None = None
    location: str | None = None
    email: str | None = None
    email_type: str | None = None
    email_status: str | None = None
    emails: list[RevealEmail] = Field(default_factory=list)
    mobile_phone: str | None = None
    phone_number: str | None = None
    phone_status: str | None = None
    phones: list[RevealPhone] = Field(default_factory=list)
    company_size: int | None = None
    company_size_range: str | None = None
    company_type: str | None = None
    company_domain: str | None = None
    company_locality: str | None = None
    company_region: str | None = None
    company_country: str | None = None
    company_street: str | None = None
    company_postal_code: str | None = None
    company_founded: int | None = None
    company_funding: str | None = None
    company_revenue: str | None = None
    company_industry: str | None = None
    company_subindustry: str | None = None
    company_linkedin: str | None = None
    company_location: str | None = None
    company_description: str | None = None
    credits: dict[str, Any] | None = None


class GetCreditsOutput(_Base):
    success: bool
    error: str | None = None
    # Remaining email/phone credits may come back as a number or the
    # string "unlimited", so widen to a permissive union.
    email_credits: int | str | None = None
    phone_credits: int | str | None = None
    export_credits: int | None = None
    api_credits: int | None = None
