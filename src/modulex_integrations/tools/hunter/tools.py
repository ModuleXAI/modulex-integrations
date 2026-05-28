"""Hunter LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.hunter.outputs import (
    AccountInformationOutput,
    CombinedEnrichmentOutput,
    CreateLeadOutput,
    DeleteLeadOutput,
    DomainSearchOutput,
    EmailCountOutput,
    EmailFinderOutput,
    EmailVerifierOutput,
    GetLeadOutput,
    GetLeadsListOutput,
    ListLeadsListsOutput,
    ListLeadsOutput,
    UpdateLeadOutput,
)

__all__ = [
    "account_information",
    "combined_enrichment",
    "create_lead",
    "delete_lead",
    "domain_search",
    "email_count",
    "email_finder",
    "email_verifier",
    "get_lead",
    "get_leads_list",
    "list_leads",
    "list_leads_lists",
    "update_lead",
]

_BASE_URL = "https://api.hunter.io/v2"


def _params(api_key: str, **extra: Any) -> dict[str, Any]:
    """Build query params with the API key included."""
    p: dict[str, Any] = {"api_key": api_key}
    for k, v in extra.items():
        if v is not None:
            p[k] = v
    return p


# --- Input schemas --------------------------------------------------------


class AccountInformationInput(BaseModel):
    api_key: str = Field(description="Hunter API key")


class CombinedEnrichmentInput(BaseModel):
    email: str = Field(description="The email address you want to find information about")
    api_key: str = Field(description="Hunter API key")


class CreateLeadInput(BaseModel):
    email: str = Field(description="The email address of the lead")
    api_key: str = Field(description="Hunter API key")
    first_name: str | None = Field(default=None, description="The first name of the lead")
    last_name: str | None = Field(default=None, description="The last name of the lead")
    position: str | None = Field(default=None, description="The job title of the lead")
    company: str | None = Field(default=None, description="The name of the company the lead is working in")
    company_industry: str | None = Field(default=None, description="The sector of the company")
    company_size: str | None = Field(default=None, description="The size of the company")
    confidence_score: int | None = Field(default=None, description="Probability the email address is correct, between 0 and 100")
    website: str | None = Field(default=None, description="The domain name of the company")
    country_code: str | None = Field(default=None, description="The country of the lead (ISO 3166-1 alpha-2)")
    linkedin_url: str | None = Field(default=None, description="The public LinkedIn profile URL")
    phone_number: str | None = Field(default=None, description="The phone number of the lead")
    twitter: str | None = Field(default=None, description="The Twitter handle of the lead")
    notes: str | None = Field(default=None, description="Personal notes about the lead")
    source: str | None = Field(default=None, description="The source where the lead has been found")
    leads_list_id: str | None = Field(default=None, description="The identifier of the list the lead belongs to")


class DeleteLeadInput(BaseModel):
    lead_id: str = Field(description="The unique identifier of the lead")
    api_key: str = Field(description="Hunter API key")


class DomainSearchInput(BaseModel):
    api_key: str = Field(description="Hunter API key")
    domain: str | None = Field(default=None, description="Domain name to search. Either domain or company must be provided")
    company: str | None = Field(default=None, description="Company name to search. Either domain or company must be provided")
    limit: int = Field(default=100, description="Max number of email addresses to return")
    type: str | None = Field(default=None, description="Get only personal or generic email addresses. Allowed values: personal, generic")
    seniority: str | None = Field(default=None, description="Seniority level(s), comma-separated: junior, senior, executive")
    department: str | None = Field(default=None, description="Department(s), comma-separated: executive, it, finance, management, sales, legal, support, hr, marketing, communication, education, design, health, operations")


class EmailCountInput(BaseModel):
    api_key: str = Field(description="Hunter API key")
    domain: str | None = Field(default=None, description="Domain name. Either domain or company must be provided")
    company: str | None = Field(default=None, description="Company name. Either domain or company must be provided")
    type: str | None = Field(default=None, description="Get only personal or generic email addresses. Allowed values: personal, generic")


class EmailFinderInput(BaseModel):
    first_name: str = Field(description="The person's first name")
    last_name: str = Field(description="The person's last name")
    api_key: str = Field(description="Hunter API key")
    domain: str | None = Field(default=None, description="Domain name. Either domain or company must be provided")
    company: str | None = Field(default=None, description="Company name. Either domain or company must be provided")


class EmailVerifierInput(BaseModel):
    email: str = Field(description="The email address you want to verify")
    api_key: str = Field(description="Hunter API key")


class GetLeadInput(BaseModel):
    lead_id: str = Field(description="The unique identifier of the lead")
    api_key: str = Field(description="Hunter API key")


class GetLeadsListInput(BaseModel):
    leads_list_id: str = Field(description="Identifier of the leads list to retrieve")
    api_key: str = Field(description="Hunter API key")
    limit: int = Field(default=100, description="A limit on the number of leads to be returned (1-100)")


class ListLeadsInput(BaseModel):
    api_key: str = Field(description="Hunter API key")
    limit: int = Field(default=100, description="A limit on the number of leads to be returned (1-1000)")
    leads_list_id: str | None = Field(default=None, description="Only returns leads belonging to this list")
    email: str | None = Field(default=None, description="Filter leads by email")
    first_name: str | None = Field(default=None, description="Filter leads by first name")
    last_name: str | None = Field(default=None, description="Filter leads by last name")
    position: str | None = Field(default=None, description="Filter leads by position")
    company: str | None = Field(default=None, description="Filter leads by company")
    industry: str | None = Field(default=None, description="Filter leads by industry")
    website: str | None = Field(default=None, description="Filter leads by website")
    country_code: str | None = Field(default=None, description="Filter leads by country code (ISO 3166-1 alpha-2)")
    company_size: str | None = Field(default=None, description="Filter leads by company size")
    source: str | None = Field(default=None, description="Filter leads by source")
    twitter: str | None = Field(default=None, description="Filter leads by Twitter handle")
    linkedin_url: str | None = Field(default=None, description="Filter leads by LinkedIn URL")
    phone_number: str | None = Field(default=None, description="Filter leads by phone number")
    sync_status: str | None = Field(default=None, description="Filter by synchronization status: pending, error, success")
    sending_status: str | None = Field(default=None, description="Filter by sending status, comma-separated: clicked, opened, sent, pending, error, bounced, unsubscribed, replied")
    verification_status: str | None = Field(default=None, description="Filter by verification status, comma-separated: accept_all, disposable, invalid, unknown, valid, webmail, pending")
    last_activity_at: str | None = Field(default=None, description="Filter by last activity: * (any), ~ (unset)")
    last_contacted_at: str | None = Field(default=None, description="Filter by last contact date: * (any), ~ (unset)")
    query: str | None = Field(default=None, description="Search leads by First Name, Last Name, or Email")


class ListLeadsListsInput(BaseModel):
    api_key: str = Field(description="Hunter API key")
    limit: int = Field(default=100, description="A limit on the number of lists to be returned (1-100)")


class UpdateLeadInput(BaseModel):
    lead_id: str = Field(description="The unique identifier of the lead")
    api_key: str = Field(description="Hunter API key")
    email: str | None = Field(default=None, description="The email address of the lead")
    first_name: str | None = Field(default=None, description="The person's first name")
    last_name: str | None = Field(default=None, description="The person's last name")
    position: str | None = Field(default=None, description="The person's position in the company")
    company: str | None = Field(default=None, description="The company name")
    website: str | None = Field(default=None, description="The website URL of the company")
    phone_number: str | None = Field(default=None, description="The person's phone number")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AccountInformationInput)
@serialize_pydantic_return
async def account_information(
    api_key: str,
) -> AccountInformationOutput:
    """Get information about your Hunter account."""
    if not api_key or not api_key.strip():
        return AccountInformationOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/account",
                params=_params(api_key),
            )
        if response.status_code != 200:
            return AccountInformationOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json().get("data", {})
    except httpx.TimeoutException:
        return AccountInformationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AccountInformationOutput(success=False, error=f"Call failed: {exc}")

    calls = data.get("calls", {})
    return AccountInformationOutput(
        success=True,
        email=data.get("email"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        plan_name=data.get("plan_name"),
        plan_level=data.get("plan_level"),
        reset_date=data.get("reset_date"),
        team_id=data.get("team_id"),
        calls_used=calls.get("used"),
        calls_available=calls.get("available"),
    )


@tool(args_schema=CombinedEnrichmentInput)
@serialize_pydantic_return
async def combined_enrichment(
    email: str,
    api_key: str,
) -> CombinedEnrichmentOutput:
    """Returns all the information associated with an email address and its domain name."""
    if not api_key or not api_key.strip():
        return CombinedEnrichmentOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/combined/find",
                params=_params(api_key, email=email),
            )
        if response.status_code != 200:
            return CombinedEnrichmentOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json().get("data", {})
    except httpx.TimeoutException:
        return CombinedEnrichmentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CombinedEnrichmentOutput(success=False, error=f"Call failed: {exc}")

    return CombinedEnrichmentOutput(success=True, data=data)


@tool(args_schema=CreateLeadInput)
@serialize_pydantic_return
async def create_lead(
    email: str,
    api_key: str,
    first_name: str | None = None,
    last_name: str | None = None,
    position: str | None = None,
    company: str | None = None,
    company_industry: str | None = None,
    company_size: str | None = None,
    confidence_score: int | None = None,
    website: str | None = None,
    country_code: str | None = None,
    linkedin_url: str | None = None,
    phone_number: str | None = None,
    twitter: str | None = None,
    notes: str | None = None,
    source: str | None = None,
    leads_list_id: str | None = None,
) -> CreateLeadOutput:
    """Create a new lead in your Hunter account."""
    if not api_key or not api_key.strip():
        return CreateLeadOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {"email": email}
    for field_name, value in [
        ("first_name", first_name),
        ("last_name", last_name),
        ("position", position),
        ("company", company),
        ("company_industry", company_industry),
        ("company_size", company_size),
        ("confidence_score", confidence_score),
        ("website", website),
        ("country_code", country_code),
        ("linkedin_url", linkedin_url),
        ("phone_number", phone_number),
        ("twitter", twitter),
        ("notes", notes),
        ("source", source),
        ("leads_list_id", leads_list_id),
    ]:
        if value is not None:
            body[field_name] = value
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/leads",
                params=_params(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateLeadOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json().get("data", {})
    except httpx.TimeoutException:
        return CreateLeadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateLeadOutput(success=False, error=f"Call failed: {exc}")

    return CreateLeadOutput(
        success=True,
        id=data.get("id"),
        email=data.get("email"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
    )


@tool(args_schema=DeleteLeadInput)
@serialize_pydantic_return
async def delete_lead(
    lead_id: str,
    api_key: str,
) -> DeleteLeadOutput:
    """Delete an existing lead from your Hunter account."""
    if not api_key or not api_key.strip():
        return DeleteLeadOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{_BASE_URL}/leads/{lead_id}",
                params=_params(api_key),
            )
        if response.status_code not in (200, 204):
            return DeleteLeadOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteLeadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteLeadOutput(success=False, error=f"Call failed: {exc}")

    return DeleteLeadOutput(success=True)


@tool(args_schema=DomainSearchInput)
@serialize_pydantic_return
async def domain_search(
    api_key: str,
    domain: str | None = None,
    company: str | None = None,
    limit: int = 100,
    type: str | None = None,
    seniority: str | None = None,
    department: str | None = None,
) -> DomainSearchOutput:
    """Search all the email addresses corresponding to one website or company."""
    if not api_key or not api_key.strip():
        return DomainSearchOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    if not domain and not company:
        return DomainSearchOutput(
            success=False,
            error="Either domain or company must be provided.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/domain-search",
                params=_params(
                    api_key,
                    domain=domain,
                    company=company,
                    limit=limit,
                    type=type,
                    seniority=seniority,
                    department=department,
                ),
            )
        if response.status_code != 200:
            return DomainSearchOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        resp = response.json()
        data = resp.get("data", {})
        meta = resp.get("meta", {})
    except httpx.TimeoutException:
        return DomainSearchOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DomainSearchOutput(success=False, error=f"Call failed: {exc}")

    return DomainSearchOutput(
        success=True,
        domain=data.get("domain"),
        disposable=data.get("disposable"),
        webmail=data.get("webmail"),
        accept_all=data.get("accept_all"),
        pattern=data.get("pattern"),
        organization=data.get("organization"),
        emails=data.get("emails", []),
        total_results=meta.get("results"),
    )


@tool(args_schema=EmailCountInput)
@serialize_pydantic_return
async def email_count(
    api_key: str,
    domain: str | None = None,
    company: str | None = None,
    type: str | None = None,
) -> EmailCountOutput:
    """Get the number of email addresses Hunter has for one domain or company."""
    if not api_key or not api_key.strip():
        return EmailCountOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    if not domain and not company:
        return EmailCountOutput(
            success=False,
            error="Either domain or company must be provided.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/email-count",
                params=_params(api_key, domain=domain, company=company, type=type),
            )
        if response.status_code != 200:
            return EmailCountOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json().get("data", {})
    except httpx.TimeoutException:
        return EmailCountOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return EmailCountOutput(success=False, error=f"Call failed: {exc}")

    return EmailCountOutput(
        success=True,
        total=data.get("total"),
        personal_emails=data.get("personal_emails"),
        generic_emails=data.get("generic_emails"),
        department=data.get("department"),
    )


@tool(args_schema=EmailFinderInput)
@serialize_pydantic_return
async def email_finder(
    first_name: str,
    last_name: str,
    api_key: str,
    domain: str | None = None,
    company: str | None = None,
) -> EmailFinderOutput:
    """Find the most likely email address from a domain name, a first name and a last name."""
    if not api_key or not api_key.strip():
        return EmailFinderOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    if not domain and not company:
        return EmailFinderOutput(
            success=False,
            error="Either domain or company must be provided.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/email-finder",
                params=_params(
                    api_key,
                    domain=domain,
                    company=company,
                    first_name=first_name,
                    last_name=last_name,
                ),
            )
        if response.status_code != 200:
            return EmailFinderOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json().get("data", {})
    except httpx.TimeoutException:
        return EmailFinderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return EmailFinderOutput(success=False, error=f"Call failed: {exc}")

    return EmailFinderOutput(
        success=True,
        email=data.get("email"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        score=data.get("score"),
        domain=data.get("domain"),
        accept_all=data.get("accept_all"),
        position=data.get("position"),
        twitter=data.get("twitter"),
        linkedin_url=data.get("linkedin_url"),
        phone_number=data.get("phone_number"),
        company=data.get("company"),
        sources=data.get("sources", []),
    )


@tool(args_schema=EmailVerifierInput)
@serialize_pydantic_return
async def email_verifier(
    email: str,
    api_key: str,
) -> EmailVerifierOutput:
    """Check the deliverability of a given email address, verify if it has been found in Hunter's database, and return their sources."""
    if not api_key or not api_key.strip():
        return EmailVerifierOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/email-verifier",
                params=_params(api_key, email=email),
            )
        if response.status_code != 200:
            return EmailVerifierOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json().get("data", {})
    except httpx.TimeoutException:
        return EmailVerifierOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return EmailVerifierOutput(success=False, error=f"Call failed: {exc}")

    return EmailVerifierOutput(
        success=True,
        status=data.get("status"),
        result=data.get("result"),
        score=data.get("score"),
        email=data.get("email"),
        regexp=data.get("regexp"),
        gibberish=data.get("gibberish"),
        disposable=data.get("disposable"),
        webmail=data.get("webmail"),
        mx_records=data.get("mx_records"),
        smtp_server=data.get("smtp_server"),
        smtp_check=data.get("smtp_check"),
        accept_all=data.get("accept_all"),
        block=data.get("block"),
        sources=data.get("sources", []),
    )


@tool(args_schema=GetLeadInput)
@serialize_pydantic_return
async def get_lead(
    lead_id: str,
    api_key: str,
) -> GetLeadOutput:
    """Retrieve one of your leads by ID."""
    if not api_key or not api_key.strip():
        return GetLeadOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/leads/{lead_id}",
                params=_params(api_key),
            )
        if response.status_code != 200:
            return GetLeadOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json().get("data", {})
    except httpx.TimeoutException:
        return GetLeadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetLeadOutput(success=False, error=f"Call failed: {exc}")

    return GetLeadOutput(
        success=True,
        id=data.get("id"),
        email=data.get("email"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        position=data.get("position"),
        company=data.get("company"),
    )


@tool(args_schema=GetLeadsListInput)
@serialize_pydantic_return
async def get_leads_list(
    leads_list_id: str,
    api_key: str,
    limit: int = 100,
) -> GetLeadsListOutput:
    """Retrieves all the fields of a leads list, including its leads."""
    if not api_key or not api_key.strip():
        return GetLeadsListOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/leads_lists/{leads_list_id}",
                params=_params(api_key, limit=limit),
            )
        if response.status_code != 200:
            return GetLeadsListOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json().get("data", {})
    except httpx.TimeoutException:
        return GetLeadsListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetLeadsListOutput(success=False, error=f"Call failed: {exc}")

    return GetLeadsListOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        leads=data.get("leads", []),
    )


@tool(args_schema=ListLeadsInput)
@serialize_pydantic_return
async def list_leads(
    api_key: str,
    limit: int = 100,
    leads_list_id: str | None = None,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    position: str | None = None,
    company: str | None = None,
    industry: str | None = None,
    website: str | None = None,
    country_code: str | None = None,
    company_size: str | None = None,
    source: str | None = None,
    twitter: str | None = None,
    linkedin_url: str | None = None,
    phone_number: str | None = None,
    sync_status: str | None = None,
    sending_status: str | None = None,
    verification_status: str | None = None,
    last_activity_at: str | None = None,
    last_contacted_at: str | None = None,
    query: str | None = None,
) -> ListLeadsOutput:
    """List all your leads with comprehensive filtering options."""
    if not api_key or not api_key.strip():
        return ListLeadsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/leads",
                params=_params(
                    api_key,
                    limit=limit,
                    leads_list_id=leads_list_id,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    position=position,
                    company=company,
                    industry=industry,
                    website=website,
                    country_code=country_code,
                    company_size=company_size,
                    source=source,
                    twitter=twitter,
                    linkedin_url=linkedin_url,
                    phone_number=phone_number,
                    sync_status=sync_status,
                    sending_status=sending_status,
                    verification_status=verification_status,
                    last_activity_at=last_activity_at,
                    last_contacted_at=last_contacted_at,
                    query=query,
                ),
            )
        if response.status_code != 200:
            return ListLeadsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        resp = response.json()
        data = resp.get("data", {})
        meta = resp.get("meta", {})
    except httpx.TimeoutException:
        return ListLeadsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListLeadsOutput(success=False, error=f"Call failed: {exc}")

    return ListLeadsOutput(
        success=True,
        leads=data.get("leads", []),
        total=meta.get("total"),
    )


@tool(args_schema=ListLeadsListsInput)
@serialize_pydantic_return
async def list_leads_lists(
    api_key: str,
    limit: int = 100,
) -> ListLeadsListsOutput:
    """List all your leads lists, sorted with the most recent first."""
    if not api_key or not api_key.strip():
        return ListLeadsListsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/leads_lists",
                params=_params(api_key, limit=limit),
            )
        if response.status_code != 200:
            return ListLeadsListsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json().get("data", {})
    except httpx.TimeoutException:
        return ListLeadsListsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListLeadsListsOutput(success=False, error=f"Call failed: {exc}")

    return ListLeadsListsOutput(
        success=True,
        leads_lists=data.get("leads_lists", []),
    )


@tool(args_schema=UpdateLeadInput)
@serialize_pydantic_return
async def update_lead(
    lead_id: str,
    api_key: str,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    position: str | None = None,
    company: str | None = None,
    website: str | None = None,
    phone_number: str | None = None,
) -> UpdateLeadOutput:
    """Update an existing lead in your Hunter account."""
    if not api_key or not api_key.strip():
        return UpdateLeadOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {}
    for field_name, value in [
        ("email", email),
        ("first_name", first_name),
        ("last_name", last_name),
        ("position", position),
        ("company", company),
        ("website", website),
        ("phone_number", phone_number),
    ]:
        if value is not None:
            body[field_name] = value
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{_BASE_URL}/leads/{lead_id}",
                params=_params(api_key),
                json=body,
            )
        if response.status_code not in (200, 204):
            return UpdateLeadOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return UpdateLeadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateLeadOutput(success=False, error=f"Call failed: {exc}")

    return UpdateLeadOutput(success=True)
