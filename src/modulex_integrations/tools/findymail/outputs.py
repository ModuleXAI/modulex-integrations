"""Pydantic response models for the Findymail integration's @tool functions.

Findymail uses the modulex *api_key* runtime convention: each tool takes
``api_key: str`` directly and the runtime injects it from the resolved
credential.

Error model: non-2xx responses, timeouts, and unexpected exceptions are
caught and surfaced as ``success=False`` + ``error`` rather than raising.
Every output model carries both shapes; fields stay permissive (``.get()``
parsing).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "Contact",
    "Employee",
    "FindEmailFromLinkedinOutput",
    "FindEmailFromNameOutput",
    "FindEmailsByDomainOutput",
    "FindEmployeesOutput",
    "FindPhoneOutput",
    "GetCompanyOutput",
    "GetCreditsOutput",
    "LookupTechnologiesOutput",
    "ReverseEmailLookupOutput",
    "SearchTechnologiesOutput",
    "Technology",
    "VerifyEmailOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class Contact(_Base):
    """A contact discovered by an email-finder action."""

    name: str | None = None
    email: str | None = None
    domain: str | None = None


class Employee(_Base):
    """A person returned by ``find_employees``."""

    name: str | None = None
    linkedin_url: str | None = None
    company_website: str | None = None
    company_name: str | None = None
    job_title: str | None = None


class Technology(_Base):
    """A technology returned by the technology endpoints."""

    name: str | None = None
    category: str | None = None
    subcategory: str | None = None
    last_detected_at: str | None = None


# --- Per-action output models ----------------------------------------------


class VerifyEmailOutput(_Base):
    success: bool
    error: str | None = None
    email: str | None = None
    verified: bool | None = None
    provider: str | None = None


class FindEmailFromNameOutput(_Base):
    success: bool
    error: str | None = None
    contact: Contact | None = None


class FindEmailFromLinkedinOutput(_Base):
    success: bool
    error: str | None = None
    contact: Contact | None = None


class FindEmailsByDomainOutput(_Base):
    success: bool
    error: str | None = None
    contacts: list[Contact] = Field(default_factory=list)


class ReverseEmailLookupOutput(_Base):
    success: bool
    error: str | None = None
    email: str | None = None
    linkedin_url: str | None = None
    full_name: str | None = None
    username: str | None = None
    headline: str | None = None
    job_title: str | None = None
    summary: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    company_linkedin_url: str | None = None
    company_name: str | None = None
    company_website: str | None = None
    is_premium: bool | None = None
    is_open_profile: bool | None = None
    skills: list[Any] = Field(default_factory=list)
    jobs: list[Any] = Field(default_factory=list)
    educations: list[Any] = Field(default_factory=list)
    certificates: list[Any] = Field(default_factory=list)


class GetCompanyOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    domain: str | None = None
    company_size: str | None = None
    industry: str | None = None
    linkedin_url: str | None = None
    description: str | None = None


class FindEmployeesOutput(_Base):
    success: bool
    error: str | None = None
    employees: list[Employee] = Field(default_factory=list)


class FindPhoneOutput(_Base):
    success: bool
    error: str | None = None
    phone: str | None = None
    line_type: str | None = None


class SearchTechnologiesOutput(_Base):
    success: bool
    error: str | None = None
    technologies: list[Technology] = Field(default_factory=list)


class LookupTechnologiesOutput(_Base):
    success: bool
    error: str | None = None
    domain: str | None = None
    technologies: list[Technology] = Field(default_factory=list)


class GetCreditsOutput(_Base):
    success: bool
    error: str | None = None
    credits: int | None = None
    verifier_credits: int | None = None
