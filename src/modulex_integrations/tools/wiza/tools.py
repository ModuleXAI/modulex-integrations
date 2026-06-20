"""Wiza LangChain ``@tool`` functions.

Four async tools wrapping the Wiza REST API (``wiza.co/api``). The
calling convention is the modulex *api_key* one: the ``ToolExecutor``
injects ``api_key: str`` directly (resolved from the user's ``api_key``
credential), not an ``auth_type``/``auth_data`` pair. The key is sent
as ``Authorization: Bearer <api_key>``.

Error model: every call is wrapped in try/except and returns the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions — non-2xx HTTP responses do *not*
raise.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.wiza.outputs import (
    CompanyEnrichmentOutput,
    GetCreditsOutput,
    IndividualRevealOutput,
    ProspectProfile,
    ProspectSearchOutput,
    RevealEmail,
    RevealPhone,
)

__all__ = [
    "company_enrichment",
    "get_credits",
    "individual_reveal",
    "prospect_search",
]

_BASE_URL = "https://wiza.co/api"
_DEFAULT_TIMEOUT = 30.0

# Individual reveals are asynchronous: a create call returns a reveal id
# and a non-terminal status, then the result is polled until terminal.
_POLL_INTERVAL_SECONDS = 2.0
_MAX_POLL_SECONDS = 120.0
_MAX_CONSECUTIVE_POLL_ERRORS = 3


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _is_terminal_reveal(data: dict[str, Any]) -> bool:
    """Whether a reveal payload has reached a terminal state."""
    return (
        data.get("status") in ("finished", "failed")
        or data.get("is_complete") is True
    )


def _map_reveal_data(data: dict[str, Any]) -> dict[str, Any]:
    """Map a Wiza individual-reveal ``data`` object to output fields."""
    emails = data.get("emails")
    phones = data.get("phones")
    return {
        "id": data.get("id"),
        "status": data.get("status"),
        "is_complete": data.get("is_complete"),
        "name": data.get("name"),
        "company": data.get("company"),
        "enrichment_level": data.get("enrichment_level"),
        "linkedin_profile_url": data.get("linkedin_profile_url"),
        "title": data.get("title"),
        "location": data.get("location"),
        "email": data.get("email"),
        "email_type": data.get("email_type"),
        "email_status": data.get("email_status"),
        "emails": [
            RevealEmail(
                email=e.get("email"),
                email_type=e.get("email_type"),
                email_status=e.get("email_status"),
            )
            for e in (emails if isinstance(emails, list) else [])
        ],
        "mobile_phone": data.get("mobile_phone"),
        "phone_number": data.get("phone_number"),
        "phone_status": data.get("phone_status"),
        "phones": [
            RevealPhone(
                number=p.get("number"),
                pretty_number=p.get("pretty_number"),
                type=p.get("type"),
            )
            for p in (phones if isinstance(phones, list) else [])
        ],
        "company_size": data.get("company_size"),
        "company_size_range": data.get("company_size_range"),
        "company_type": data.get("company_type"),
        "company_domain": data.get("company_domain"),
        "company_locality": data.get("company_locality"),
        "company_region": data.get("company_region"),
        "company_country": data.get("company_country"),
        "company_street": data.get("company_street"),
        "company_postal_code": data.get("company_postal_code"),
        "company_founded": data.get("company_founded"),
        "company_funding": data.get("company_funding"),
        "company_revenue": data.get("company_revenue"),
        "company_industry": data.get("company_industry"),
        "company_subindustry": data.get("company_subindustry"),
        "company_linkedin": data.get("company_linkedin"),
        "company_location": data.get("company_location"),
        "company_description": data.get("company_description"),
        "credits": data.get("credits"),
    }


# --- Input schemas (args_schema for each @tool) ----------------------------


class ProspectSearchInput(BaseModel):
    api_key: str = Field(description="Wiza API key (provided by credential system)")
    size: int | None = Field(
        default=None,
        description="Number of sample profiles to return (0-30, default 0 returns total only)",
    )
    filters: dict[str, Any] | None = Field(
        default=None,
        description="Full filters object (overrides individual filter params if provided)",
    )
    first_name: list[str] | None = Field(
        default=None, description='Exact first names to match (e.g., ["John", "Jane"])'
    )
    last_name: list[str] | None = Field(
        default=None, description="Exact last names to match"
    )
    job_title: list[dict[str, Any]] | None = Field(
        default=None,
        description='Job titles to include/exclude (e.g., [{"v":"CEO","s":"i"}])',
    )
    job_title_level: list[str] | None = Field(
        default=None, description='Seniority levels (e.g., ["cxo", "director"])'
    )
    job_role: list[str] | None = Field(
        default=None, description='Job role categories (e.g., ["sales", "engineering"])'
    )
    job_sub_role: list[str] | None = Field(
        default=None, description='Detailed role categories (e.g., ["software"])'
    )
    location: list[dict[str, Any]] | None = Field(
        default=None,
        description="Person location filters (city/state/country with include/exclude)",
    )
    skill: list[str] | None = Field(
        default=None, description='Professional skills (e.g., ["python", "marketing"])'
    )
    school: list[str] | None = Field(
        default=None, description="Educational institutions"
    )
    major: list[str] | None = Field(default=None, description="Field of study")
    linkedin_slug: list[str] | None = Field(
        default=None, description="LinkedIn profile slugs"
    )
    job_company: list[dict[str, Any]] | None = Field(
        default=None, description="Current company filters (include/exclude)"
    )
    past_company: list[dict[str, Any]] | None = Field(
        default=None, description="Past company filters (include/exclude)"
    )
    company_location: list[dict[str, Any]] | None = Field(
        default=None, description="Company HQ location filters"
    )
    company_industry: list[dict[str, Any]] | None = Field(
        default=None, description="Company industry filters (include/exclude)"
    )
    company_size: list[str] | None = Field(
        default=None, description='Company headcount brackets (e.g., ["11-50"])'
    )
    company_type: list[str] | None = Field(
        default=None, description='Company type (e.g., ["private", "public"])'
    )


class CompanyEnrichmentInput(BaseModel):
    api_key: str = Field(description="Wiza API key (provided by credential system)")
    company_name: str | None = Field(
        default=None, description='Company name (e.g., "Wiza")'
    )
    company_domain: str | None = Field(
        default=None, description='Company domain (e.g., "wiza.co")'
    )
    company_linkedin_id: str | None = Field(
        default=None, description="Company LinkedIn ID"
    )
    company_linkedin_slug: str | None = Field(
        default=None, description="Company LinkedIn slug from the URL"
    )


class IndividualRevealInput(BaseModel):
    api_key: str = Field(description="Wiza API key (provided by credential system)")
    enrichment_level: str = Field(
        description="Enrichment depth: 'none', 'partial', 'phone', or 'full'"
    )
    profile_url: str | None = Field(
        default=None,
        description="LinkedIn profile URL (e.g., https://linkedin.com/in/johndoe)",
    )
    full_name: str | None = Field(
        default=None, description="Full name (used with company or domain)"
    )
    company: str | None = Field(
        default=None, description="Company name (used with full_name)"
    )
    domain: str | None = Field(
        default=None, description="Company domain (used with full_name)"
    )
    email: str | None = Field(
        default=None, description="Email address (use alone or with other identifiers)"
    )
    accept_work: bool | None = Field(
        default=None, description="Whether to accept work emails (email_options)"
    )
    accept_personal: bool | None = Field(
        default=None, description="Whether to accept personal emails (email_options)"
    )


class GetCreditsInput(BaseModel):
    api_key: str = Field(description="Wiza API key (provided by credential system)")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=ProspectSearchInput)
@serialize_pydantic_return
async def prospect_search(
    api_key: str,
    size: int | None = None,
    filters: dict[str, Any] | None = None,
    first_name: list[str] | None = None,
    last_name: list[str] | None = None,
    job_title: list[dict[str, Any]] | None = None,
    job_title_level: list[str] | None = None,
    job_role: list[str] | None = None,
    job_sub_role: list[str] | None = None,
    location: list[dict[str, Any]] | None = None,
    skill: list[str] | None = None,
    school: list[str] | None = None,
    major: list[str] | None = None,
    linkedin_slug: list[str] | None = None,
    job_company: list[dict[str, Any]] | None = None,
    past_company: list[dict[str, Any]] | None = None,
    company_location: list[dict[str, Any]] | None = None,
    company_industry: list[dict[str, Any]] | None = None,
    company_size: list[str] | None = None,
    company_type: list[str] | None = None,
) -> ProspectSearchOutput:
    """Search Wiza's database of prospects using person, company, and financial filters."""
    if not api_key or not api_key.strip():
        return ProspectSearchOutput(
            success=False,
            error="Wiza API key is empty. Please configure a valid Wiza credential.",
        )

    body: dict[str, Any] = {}
    if size is not None:
        body["size"] = max(0, min(size, 30))

    if filters:
        body["filters"] = filters
    else:
        built: dict[str, Any] = {}
        candidates: dict[str, Any] = {
            "first_name": first_name,
            "last_name": last_name,
            "job_title": job_title,
            "job_title_level": job_title_level,
            "job_role": job_role,
            "job_sub_role": job_sub_role,
            "location": location,
            "skill": skill,
            "school": school,
            "major": major,
            "linkedin_slug": linkedin_slug,
            "job_company": job_company,
            "past_company": past_company,
            "company_location": company_location,
            "company_industry": company_industry,
            "company_size": company_size,
            "company_type": company_type,
        }
        for key, value in candidates.items():
            if value:
                built[key] = value
        if built:
            body["filters"] = built

    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/prospects/search", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return ProspectSearchOutput(
                success=False,
                error=f"Wiza API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ProspectSearchOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ProspectSearchOutput(
            success=False, error=f"Prospect search failed: {exc}"
        )

    payload = data.get("data") or {}
    raw_profiles = payload.get("profiles")
    return ProspectSearchOutput(
        success=True,
        total=payload.get("total") or 0,
        profiles=[
            ProspectProfile(
                full_name=p.get("full_name"),
                linkedin_url=p.get("linkedin_url"),
                industry=p.get("industry"),
                job_title=p.get("job_title"),
                job_title_role=p.get("job_title_role"),
                job_title_sub_role=p.get("job_title_sub_role"),
                job_company_name=p.get("job_company_name"),
                job_company_website=p.get("job_company_website"),
                location_name=p.get("location_name"),
            )
            for p in (raw_profiles if isinstance(raw_profiles, list) else [])
        ],
    )


@tool(args_schema=CompanyEnrichmentInput)
@serialize_pydantic_return
async def company_enrichment(
    api_key: str,
    company_name: str | None = None,
    company_domain: str | None = None,
    company_linkedin_id: str | None = None,
    company_linkedin_slug: str | None = None,
) -> CompanyEnrichmentOutput:
    """Enrich a company by name, domain, LinkedIn ID, or LinkedIn slug with firmographic data."""
    if not api_key or not api_key.strip():
        return CompanyEnrichmentOutput(
            success=False,
            error="Wiza API key is empty. Please configure a valid Wiza credential.",
        )

    body: dict[str, Any] = {}
    if company_name:
        body["company_name"] = company_name
    if company_domain:
        body["company_domain"] = company_domain
    if company_linkedin_id:
        body["company_linkedin_id"] = company_linkedin_id
    if company_linkedin_slug:
        body["company_linkedin_slug"] = company_linkedin_slug

    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/company_enrichments",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return CompanyEnrichmentOutput(
                success=False,
                error=f"Wiza API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CompanyEnrichmentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CompanyEnrichmentOutput(
            success=False, error=f"Company enrichment failed: {exc}"
        )

    d = data.get("data") or {}
    return CompanyEnrichmentOutput(
        success=True,
        company_name=d.get("company_name"),
        company_domain=d.get("company_domain"),
        domain=d.get("domain"),
        company_industry=d.get("company_industry"),
        company_size=d.get("company_size"),
        company_size_range=d.get("company_size_range"),
        company_founded=d.get("company_founded"),
        company_revenue_range=d.get("company_revenue_range"),
        company_funding=d.get("company_funding"),
        company_type=d.get("company_type"),
        company_description=d.get("company_description"),
        company_ticker=d.get("company_ticker"),
        company_last_funding_round=d.get("company_last_funding_round"),
        company_last_funding_amount=d.get("company_last_funding_amount"),
        company_last_funding_at=d.get("company_last_funding_at"),
        company_location=d.get("company_location"),
        company_twitter=d.get("company_twitter"),
        company_facebook=d.get("company_facebook"),
        company_linkedin=d.get("company_linkedin"),
        company_linkedin_id=d.get("company_linkedin_id"),
        company_street=d.get("company_street"),
        company_locality=d.get("company_locality"),
        company_region=d.get("company_region"),
        company_postal_code=d.get("company_postal_code"),
        company_country=d.get("company_country"),
        credits=d.get("credits"),
    )


@tool(args_schema=IndividualRevealInput)
@serialize_pydantic_return
async def individual_reveal(
    api_key: str,
    enrichment_level: str,
    profile_url: str | None = None,
    full_name: str | None = None,
    company: str | None = None,
    domain: str | None = None,
    email: str | None = None,
    accept_work: bool | None = None,
    accept_personal: bool | None = None,
) -> IndividualRevealOutput:
    """Reveal a contact via LinkedIn URL, name + company/domain, or email.

    Starts an individual reveal and polls until it resolves. Uses 2 credits
    per valid email and 5 credits per phone, charged only on success.
    """
    if not api_key or not api_key.strip():
        return IndividualRevealOutput(
            success=False,
            error="Wiza API key is empty. Please configure a valid Wiza credential.",
        )

    individual: dict[str, Any] = {}
    if profile_url:
        individual["profile_url"] = profile_url
    if full_name:
        individual["full_name"] = full_name
    if company:
        individual["company"] = company
    if domain:
        individual["domain"] = domain
    if email:
        individual["email"] = email

    body: dict[str, Any] = {
        "individual_reveal": individual,
        "enrichment_level": enrichment_level,
    }
    if accept_work is not None or accept_personal is not None:
        email_options: dict[str, Any] = {}
        if accept_work is not None:
            email_options["accept_work"] = accept_work
        if accept_personal is not None:
            email_options["accept_personal"] = accept_personal
        body["email_options"] = email_options

    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/individual_reveals",
                headers=_headers(api_key),
                json=body,
            )
            if response.status_code != 200:
                return IndividualRevealOutput(
                    success=False,
                    error=f"Wiza API error ({response.status_code}): {response.text}",
                )
            payload = (response.json() or {}).get("data") or {}

            # A reveal may resolve synchronously (cache hit). Otherwise poll
            # until it reaches a terminal state or the window elapses.
            if not _is_terminal_reveal(payload):
                reveal_id = payload.get("id")
                if reveal_id is None:
                    return IndividualRevealOutput(
                        success=False,
                        error="Wiza individual reveal did not return an id.",
                        **_map_reveal_data(payload),
                    )

                elapsed = 0.0
                consecutive_errors = 0
                while elapsed < _MAX_POLL_SECONDS:
                    await asyncio.sleep(_POLL_INTERVAL_SECONDS)
                    elapsed += _POLL_INTERVAL_SECONDS

                    poll = await client.get(
                        f"{_BASE_URL}/individual_reveals/{reveal_id}",
                        headers=_headers(api_key),
                    )
                    if poll.status_code != 200:
                        consecutive_errors += 1
                        if consecutive_errors >= _MAX_CONSECUTIVE_POLL_ERRORS:
                            return IndividualRevealOutput(
                                success=False,
                                error=(
                                    f"Wiza API error ({poll.status_code}): {poll.text}"
                                ),
                                **_map_reveal_data(payload),
                            )
                        continue
                    consecutive_errors = 0

                    polled = (poll.json() or {}).get("data") or {}
                    if _is_terminal_reveal(polled):
                        payload = polled
                        break
                else:
                    return IndividualRevealOutput(
                        success=False,
                        error=(
                            "Wiza individual reveal did not complete within the "
                            "polling window."
                        ),
                        **_map_reveal_data(payload),
                    )
    except httpx.TimeoutException:
        return IndividualRevealOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return IndividualRevealOutput(
            success=False, error=f"Individual reveal failed: {exc}"
        )

    mapped = _map_reveal_data(payload)
    return IndividualRevealOutput(success=mapped.get("status") != "failed", **mapped)


@tool(args_schema=GetCreditsInput)
@serialize_pydantic_return
async def get_credits(api_key: str) -> GetCreditsOutput:
    """Retrieve the remaining credits on your Wiza account."""
    if not api_key or not api_key.strip():
        return GetCreditsOutput(
            success=False,
            error="Wiza API key is empty. Please configure a valid Wiza credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/meta/credits", headers=_headers(api_key)
            )
        if response.status_code != 200:
            return GetCreditsOutput(
                success=False,
                error=f"Wiza API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetCreditsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCreditsOutput(success=False, error=f"Get credits failed: {exc}")

    credits = data.get("credits") or {}
    return GetCreditsOutput(
        success=True,
        email_credits=credits.get("email_credits"),
        phone_credits=credits.get("phone_credits"),
        export_credits=credits.get("export_credits"),
        api_credits=credits.get("api_credits"),
    )
