"""Findymail LangChain ``@tool`` functions.

Eleven async tools wrapping the Findymail REST API (``app.findymail.com``).
Calling convention is *key-based*: the modulex ``ToolExecutor`` injects an
``api_key: str`` directly (resolved from the user's API-key credential).

Error model: non-2xx HTTP responses, timeouts, and unexpected exceptions are
caught and returned as the typed output with ``success=False`` + ``error``
rather than raising.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.findymail.outputs import (
    Contact,
    Employee,
    FindEmailFromLinkedinOutput,
    FindEmailFromNameOutput,
    FindEmailsByDomainOutput,
    FindEmployeesOutput,
    FindPhoneOutput,
    GetCompanyOutput,
    GetCreditsOutput,
    LookupTechnologiesOutput,
    ReverseEmailLookupOutput,
    SearchTechnologiesOutput,
    Technology,
    VerifyEmailOutput,
)

__all__ = [
    "find_email_from_linkedin",
    "find_email_from_name",
    "find_emails_by_domain",
    "find_employees",
    "find_phone",
    "get_company",
    "get_credits",
    "lookup_technologies",
    "reverse_email_lookup",
    "search_technologies",
    "verify_email",
]

_BASE_URL = "https://app.findymail.com/api"
_TIMEOUT = 60.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
        if isinstance(data, dict):
            msg = data.get("message") or data.get("error")
            if msg:
                return f"Findymail API error ({response.status_code}): {msg}"
    except Exception:
        pass
    return f"Findymail API error ({response.status_code}): {response.text}"


def _parse_contact(raw: Any) -> Contact | None:
    if not isinstance(raw, dict):
        return None
    return Contact(
        name=raw.get("name"),
        email=raw.get("email"),
        domain=raw.get("domain"),
    )


def _parse_technologies(raw: Any) -> list[Technology]:
    if not isinstance(raw, list):
        return []
    return [
        Technology(
            name=t.get("name"),
            category=t.get("category"),
            subcategory=t.get("subcategory"),
            last_detected_at=t.get("last_detected_at"),
        )
        for t in raw
        if isinstance(t, dict)
    ]


# --- Input schemas (args_schema for each @tool) ----------------------------


class VerifyEmailInput(BaseModel):
    email: str = Field(description="Email address to verify (e.g., john@example.com)")
    api_key: str = Field(description="Findymail API key (provided by credential system)")


class FindEmailFromNameInput(BaseModel):
    name: str = Field(description="Person's full name (e.g., 'John Doe')")
    domain: str = Field(
        description="Company domain (preferred) or company name (e.g., stripe.com)"
    )
    api_key: str = Field(description="Findymail API key (provided by credential system)")


class FindEmailFromLinkedinInput(BaseModel):
    linkedin_url: str = Field(
        description=(
            "Person's LinkedIn URL or username "
            "(e.g., 'https://linkedin.com/in/johndoe' or 'johndoe')"
        )
    )
    api_key: str = Field(description="Findymail API key (provided by credential system)")


class FindEmailsByDomainInput(BaseModel):
    domain: str = Field(description="Company domain (e.g., stripe.com)")
    roles: list[str] = Field(
        description='Target roles at the company (max 3, e.g., ["CEO", "Founder"])'
    )
    api_key: str = Field(description="Findymail API key (provided by credential system)")


class ReverseEmailLookupInput(BaseModel):
    email: str = Field(description="Work or personal email address to look up")
    api_key: str = Field(description="Findymail API key (provided by credential system)")
    with_profile: bool = Field(
        default=False,
        description="Whether to return enriched profile metadata (default: false)",
    )


class GetCompanyInput(BaseModel):
    api_key: str = Field(description="Findymail API key (provided by credential system)")
    linkedin_url: str | None = Field(
        default=None,
        description="Company LinkedIn URL (e.g., https://www.linkedin.com/company/stripe/)",
    )
    domain: str | None = Field(
        default=None, description="Company domain (e.g., stripe.com)"
    )
    name: str | None = Field(default=None, description="Company name (e.g., Stripe)")


class FindEmployeesInput(BaseModel):
    website: str = Field(description="Company website or domain (e.g., google.com)")
    job_titles: list[str] = Field(
        description=(
            'Target job titles to search for '
            '(max 10, e.g., ["Software Engineer", "CEO"])'
        )
    )
    api_key: str = Field(description="Findymail API key (provided by credential system)")
    count: int | None = Field(
        default=None, description="Number of contacts to return (max 5, default 1)"
    )


class FindPhoneInput(BaseModel):
    linkedin_url: str = Field(
        description=(
            "Person's LinkedIn URL or username "
            "(e.g., 'https://linkedin.com/in/johndoe' or 'johndoe')"
        )
    )
    api_key: str = Field(description="Findymail API key (provided by credential system)")


class SearchTechnologiesInput(BaseModel):
    q: str = Field(description='Search term (min 2 characters, e.g., "React")')
    api_key: str = Field(description="Findymail API key (provided by credential system)")


class LookupTechnologiesInput(BaseModel):
    domain: str = Field(description="Company domain to look up (e.g., stripe.com)")
    api_key: str = Field(description="Findymail API key (provided by credential system)")
    technologies: list[str] | None = Field(
        default=None,
        description='Filter by technology names, case-insensitive (e.g., ["React", "TypeScript"])',
    )


class GetCreditsInput(BaseModel):
    api_key: str = Field(description="Findymail API key (provided by credential system)")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=VerifyEmailInput)
@serialize_pydantic_return
async def verify_email(email: str, api_key: str) -> VerifyEmailOutput:
    """Verifies the deliverability of an email address. Uses one verifier credit."""
    if not api_key or not api_key.strip():
        return VerifyEmailOutput(
            success=False,
            error="Findymail API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {"email": email}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/verify", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return VerifyEmailOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return VerifyEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return VerifyEmailOutput(success=False, error=f"verify_email failed: {exc}")

    return VerifyEmailOutput(
        success=True,
        email=data.get("email"),
        verified=data.get("verified"),
        provider=data.get("provider"),
    )


@tool(args_schema=FindEmailFromNameInput)
@serialize_pydantic_return
async def find_email_from_name(
    name: str, domain: str, api_key: str
) -> FindEmailFromNameOutput:
    """Find someone's email from their name and a company domain or company name.

    Uses one finder credit when a verified email is found.
    """
    if not api_key or not api_key.strip():
        return FindEmailFromNameOutput(
            success=False,
            error="Findymail API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {"name": name, "domain": domain}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/search/name", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return FindEmailFromNameOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return FindEmailFromNameOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindEmailFromNameOutput(
            success=False, error=f"find_email_from_name failed: {exc}"
        )

    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    raw = data.get("contact") or payload.get("contact")
    return FindEmailFromNameOutput(success=True, contact=_parse_contact(raw))


@tool(args_schema=FindEmailFromLinkedinInput)
@serialize_pydantic_return
async def find_email_from_linkedin(
    linkedin_url: str, api_key: str
) -> FindEmailFromLinkedinOutput:
    """Find someone's email from a LinkedIn profile URL or username.

    Uses one finder credit when a verified email is found.
    """
    if not api_key or not api_key.strip():
        return FindEmailFromLinkedinOutput(
            success=False,
            error="Findymail API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {"linkedin_url": linkedin_url}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/search/business-profile",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return FindEmailFromLinkedinOutput(
                success=False, error=_error_message(response)
            )
        data = response.json()
    except httpx.TimeoutException:
        return FindEmailFromLinkedinOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindEmailFromLinkedinOutput(
            success=False, error=f"find_email_from_linkedin failed: {exc}"
        )

    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    raw = data.get("contact") or payload.get("contact")
    return FindEmailFromLinkedinOutput(success=True, contact=_parse_contact(raw))


@tool(args_schema=FindEmailsByDomainInput)
@serialize_pydantic_return
async def find_emails_by_domain(
    domain: str, roles: list[str], api_key: str
) -> FindEmailsByDomainOutput:
    """Find verified contacts at a given domain matching one or more target roles.

    Maximum 3 roles. Limited to 5 concurrent synchronous requests.
    """
    if not api_key or not api_key.strip():
        return FindEmailsByDomainOutput(
            success=False,
            error="Findymail API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {"domain": domain, "roles": roles}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/search/domain", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return FindEmailsByDomainOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return FindEmailsByDomainOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindEmailsByDomainOutput(
            success=False, error=f"find_emails_by_domain failed: {exc}"
        )

    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    raw = data.get("contacts")
    if not isinstance(raw, list):
        raw = payload.get("contacts")
    contacts = [
        c for c in (_parse_contact(item) for item in (raw or [])) if c is not None
    ]
    return FindEmailsByDomainOutput(success=True, contacts=contacts)


@tool(args_schema=ReverseEmailLookupInput)
@serialize_pydantic_return
async def reverse_email_lookup(
    email: str, api_key: str, with_profile: bool = False
) -> ReverseEmailLookupOutput:
    """Find a business profile from an email address.

    Uses 1 finder credit if a profile is found, 2 credits if returning full
    profile data.
    """
    if not api_key or not api_key.strip():
        return ReverseEmailLookupOutput(
            success=False,
            error="Findymail API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {"email": email}
    if with_profile:
        body["with_profile"] = True
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/search/reverse-email",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return ReverseEmailLookupOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return ReverseEmailLookupOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ReverseEmailLookupOutput(
            success=False, error=f"reverse_email_lookup failed: {exc}"
        )

    return ReverseEmailLookupOutput(
        success=True,
        email=data.get("email"),
        linkedin_url=data.get("linkedin_url"),
        full_name=data.get("fullName"),
        username=data.get("username"),
        headline=data.get("headline"),
        job_title=data.get("jobTitle"),
        summary=data.get("summary"),
        city=data.get("city"),
        region=data.get("region"),
        country=data.get("country"),
        company_linkedin_url=data.get("companyLinkedinUrl"),
        company_name=data.get("companyName"),
        company_website=data.get("companyWebsite"),
        is_premium=data.get("isPremium"),
        is_open_profile=data.get("isOpenProfile"),
        skills=data.get("skills") or [],
        jobs=data.get("jobs") or [],
        educations=data.get("educations") or [],
        certificates=data.get("certificates") or [],
    )


@tool(args_schema=GetCompanyInput)
@serialize_pydantic_return
async def get_company(
    api_key: str,
    linkedin_url: str | None = None,
    domain: str | None = None,
    name: str | None = None,
) -> GetCompanyOutput:
    """Retrieve company information from a LinkedIn URL, domain, or company name.

    Provide at least one identifier. Uses 1 finder credit per successful response.
    """
    if not api_key or not api_key.strip():
        return GetCompanyOutput(
            success=False,
            error="Findymail API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {}
    if linkedin_url:
        body["linkedin_url"] = linkedin_url
    if domain:
        body["domain"] = domain
    if name:
        body["name"] = name
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/search/company", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return GetCompanyOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return GetCompanyOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCompanyOutput(success=False, error=f"get_company failed: {exc}")

    return GetCompanyOutput(
        success=True,
        name=data.get("name"),
        domain=data.get("domain"),
        company_size=data.get("company_size"),
        industry=data.get("industry"),
        linkedin_url=data.get("linkedin_url"),
        description=data.get("description"),
    )


@tool(args_schema=FindEmployeesInput)
@serialize_pydantic_return
async def find_employees(
    website: str, job_titles: list[str], api_key: str, count: int | None = None
) -> FindEmployeesOutput:
    """Find employees at a company by website and target job titles.

    Uses 1 credit per found contact. Does not return email addresses.
    """
    if not api_key or not api_key.strip():
        return FindEmployeesOutput(
            success=False,
            error="Findymail API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {"website": website, "job_titles": job_titles}
    if count is not None:
        body["count"] = count
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/search/employees", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return FindEmployeesOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return FindEmployeesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindEmployeesOutput(success=False, error=f"find_employees failed: {exc}")

    raw = data if isinstance(data, list) else data.get("data")
    employees = [
        Employee(
            name=e.get("name"),
            linkedin_url=e.get("linkedinUrl"),
            company_website=e.get("companyWebsite"),
            company_name=e.get("companyName"),
            job_title=e.get("jobTitle"),
        )
        for e in (raw or [])
        if isinstance(e, dict)
    ]
    return FindEmployeesOutput(success=True, employees=employees)


@tool(args_schema=FindPhoneInput)
@serialize_pydantic_return
async def find_phone(linkedin_url: str, api_key: str) -> FindPhoneOutput:
    """Find someone's phone number from a LinkedIn profile URL.

    Uses 10 finder credits if a phone is found. EU citizens are excluded for
    legal reasons.
    """
    if not api_key or not api_key.strip():
        return FindPhoneOutput(
            success=False,
            error="Findymail API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {"linkedin_url": linkedin_url}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/search/phone", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return FindPhoneOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return FindPhoneOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindPhoneOutput(success=False, error=f"find_phone failed: {exc}")

    return FindPhoneOutput(
        success=True,
        phone=data.get("phone"),
        line_type=data.get("line_type"),
    )


@tool(args_schema=SearchTechnologiesInput)
@serialize_pydantic_return
async def search_technologies(q: str, api_key: str) -> SearchTechnologiesOutput:
    """Search the technology catalog by name.

    Returns up to 25 technologies. Free endpoint, rate limited to 10 requests
    per minute.
    """
    if not api_key or not api_key.strip():
        return SearchTechnologiesOutput(
            success=False,
            error="Findymail API key is empty. Please configure a valid credential.",
        )
    params: dict[str, Any] = {"q": q}
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/technologies/search", headers=headers, params=params
            )
        if response.status_code != 200:
            return SearchTechnologiesOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return SearchTechnologiesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchTechnologiesOutput(
            success=False, error=f"search_technologies failed: {exc}"
        )

    return SearchTechnologiesOutput(
        success=True, technologies=_parse_technologies(data.get("data"))
    )


@tool(args_schema=LookupTechnologiesInput)
@serialize_pydantic_return
async def lookup_technologies(
    domain: str, api_key: str, technologies: list[str] | None = None
) -> LookupTechnologiesOutput:
    """Get the technology stack for a company by domain.

    Optionally filter by technology names. 1 finder credit if technologies are
    found, free otherwise.
    """
    if not api_key or not api_key.strip():
        return LookupTechnologiesOutput(
            success=False,
            error="Findymail API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {"domain": domain}
    if technologies:
        body["technologies"] = technologies
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/technologies", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return LookupTechnologiesOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return LookupTechnologiesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return LookupTechnologiesOutput(
            success=False, error=f"lookup_technologies failed: {exc}"
        )

    return LookupTechnologiesOutput(
        success=True,
        domain=data.get("domain"),
        technologies=_parse_technologies(data.get("technologies")),
    )


@tool(args_schema=GetCreditsInput)
@serialize_pydantic_return
async def get_credits(api_key: str) -> GetCreditsOutput:
    """Retrieve the remaining finder and verifier credits for the authenticated account."""
    if not api_key or not api_key.strip():
        return GetCreditsOutput(
            success=False,
            error="Findymail API key is empty. Please configure a valid credential.",
        )
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/credits", headers=headers)
        if response.status_code != 200:
            return GetCreditsOutput(success=False, error=_error_message(response))
        data = response.json()
    except httpx.TimeoutException:
        return GetCreditsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCreditsOutput(success=False, error=f"get_credits failed: {exc}")

    return GetCreditsOutput(
        success=True,
        credits=data.get("credits"),
        verifier_credits=data.get("verifier_credits"),
    )
