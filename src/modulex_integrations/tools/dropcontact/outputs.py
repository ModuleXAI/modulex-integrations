"""Pydantic response models for the Dropcontact integration's @tool functions.

Dropcontact follows the modulex *api_key* runtime convention: each
function signature takes ``api_key: str`` directly, which the runtime
injects as the ``X-Access-Token`` header on every request.

Error model: enrichment is a submit-then-poll flow. Any non-2xx
response, an error flag in the JSON, a timeout, or the polling window
expiring surfaces as ``success=False`` + ``error`` rather than an
exception. Every output model carries both the success and failure
shapes; on failure the data fields stay at their pydantic defaults.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "EmailEntry",
    "EnrichContactOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class EmailEntry(_Base):
    """A single email address with its deliverability qualification."""

    email: str | None = None
    qualification: str | None = None


# --- Per-action output models ----------------------------------------------


class EnrichContactOutput(_Base):
    """Flat enriched-contact result returned by ``enrich_contact``."""

    success: bool
    error: str | None = None

    request_id: str | None = None
    email_found: bool = False
    email: str | None = None
    emails: list[EmailEntry] = Field(default_factory=list)
    qualification: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    civility: str | None = None
    phone: str | None = None
    mobile_phone: str | None = None
    company: str | None = None
    website: str | None = None
    company_linkedin: str | None = None
    linkedin: str | None = None
    country: str | None = None
    siren: str | None = None
    siret: str | None = None
    siret_address: str | None = None
    siret_zip: str | None = None
    siret_city: str | None = None
    vat: str | None = None
    nb_employees: str | None = None
    employee_count: int | None = None
    naf5_code: str | None = None
    naf5_des: str | None = None
    industry: str | None = None
    job: str | None = None
    job_level: str | None = None
    job_function: str | None = None
    company_turnover: str | None = None
    company_results: str | None = None
