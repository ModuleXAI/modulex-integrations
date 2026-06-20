"""Sixtyfour AI LangChain ``@tool`` functions.

Four async tools wrapping the Sixtyfour AI REST API for contact discovery
and lead/company enrichment. The modulex ``ToolExecutor`` injects an
``api_key: str`` directly (resolved from the user's ``api_key``
credential); the key is sent in the ``x-api-key`` request header.

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses, timeouts,
and unexpected exceptions. Non-2xx HTTP responses do *not* raise.

The enrichment endpoints perform deep research and are long-running
(typical P95 ~5 min, up to ~10 min for complex records), so they use
generous client timeouts.
"""
from __future__ import annotations

import json
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.sixtyfour.outputs import (
    EmailEntry,
    EnrichCompanyOutput,
    EnrichLeadOutput,
    FindEmailOutput,
    FindPhoneOutput,
)

__all__ = ["enrich_company", "enrich_lead", "find_email", "find_phone"]

_API_BASE = "https://api.sixtyfour.ai"
_CONTACT_TIMEOUT = 120.0
_ENRICH_TIMEOUT = 900.0  # deep research: docs recommend >= 15 min for sync calls


# --- Auth + parsing helpers ------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }


def _parse_emails(email_field: Any) -> list[EmailEntry]:
    """Normalize the email field into a list of ``EmailEntry``.

    The API returns each email either as a ``[address, status, type]`` triple
    or as a bare string; both shapes are flattened to the same model.
    """
    if not isinstance(email_field, list):
        return []
    entries: list[EmailEntry] = []
    for entry in email_field:
        if isinstance(entry, list):
            address = entry[0] if len(entry) > 0 else ""
            status = entry[1] if len(entry) > 1 else "UNKNOWN"
            etype = entry[2] if len(entry) > 2 else "UNKNOWN"
            entries.append(EmailEntry(address=address, status=status, type=etype))
        else:
            entries.append(EmailEntry(address=str(entry), status="UNKNOWN", type="UNKNOWN"))
    return entries


def _parse_phone(phone_field: Any) -> str | None:
    """Normalize the phone field into a single comma-joined string."""
    if isinstance(phone_field, str):
        return phone_field or None
    if isinstance(phone_field, list):
        numbers = [
            str(p.get("number")) for p in phone_field
            if isinstance(p, dict) and p.get("number") is not None
        ]
        return ", ".join(numbers) if numbers else None
    return None


def _coerce_json_object(value: Any, field_name: str) -> Any:
    """Parse a JSON string into an object, or pass through a dict/list."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"{field_name} must be valid JSON") from exc
    return value


# --- Input schemas (args_schema for each @tool) ----------------------------


class FindPhoneInput(BaseModel):
    name: str = Field(description="Full name of the person")
    api_key: str = Field(
        description="Sixtyfour AI API key (provided by credential system)"
    )
    company: str | None = Field(default=None, description="Company name")
    linkedin_url: str | None = Field(default=None, description="LinkedIn profile URL")
    domain: str | None = Field(default=None, description="Company website domain")
    email: str | None = Field(default=None, description="Email address")


class FindEmailInput(BaseModel):
    name: str = Field(description="Full name of the person")
    api_key: str = Field(
        description="Sixtyfour AI API key (provided by credential system)"
    )
    company: str | None = Field(default=None, description="Company name")
    linkedin_url: str | None = Field(default=None, description="LinkedIn profile URL")
    domain: str | None = Field(default=None, description="Company website domain")
    phone: str | None = Field(default=None, description="Phone number")
    title: str | None = Field(default=None, description="Job title")
    mode: str | None = Field(
        default=None,
        description="Email discovery mode: 'PROFESSIONAL' (default) or 'PERSONAL'",
    )


class EnrichLeadInput(BaseModel):
    lead_info: str = Field(
        description=(
            "Lead information as a JSON object with key-value pairs "
            '(e.g. {"name": "John Doe", "company": "Acme Inc", "title": "CEO"})'
        )
    )
    struct: str = Field(
        description=(
            "Fields to collect as a JSON object. Keys are field names, values are "
            'descriptions (e.g. {"email": "Email address", "phone": "Phone number"})'
        )
    )
    api_key: str = Field(
        description="Sixtyfour AI API key (provided by credential system)"
    )
    research_plan: str | None = Field(
        default=None, description="Optional research plan to guide enrichment strategy"
    )


class EnrichCompanyInput(BaseModel):
    target_company: str = Field(
        description=(
            "Company data as a JSON object "
            '(e.g. {"name": "Acme Inc", "domain": "acme.com"})'
        )
    )
    struct: str = Field(
        description=(
            "Fields to collect as a JSON object. Keys are field names, values are "
            'descriptions (e.g. {"website": "Company website URL", '
            '"num_employees": "Employee count"})'
        )
    )
    api_key: str = Field(
        description="Sixtyfour AI API key (provided by credential system)"
    )
    find_people: bool | None = Field(
        default=None,
        description="Whether to find people associated with the company",
    )
    full_org_chart: bool | None = Field(
        default=None,
        description="Whether to retrieve the full organizational chart",
    )
    research_plan: str | None = Field(
        default=None,
        description="Optional strategy describing how the agent should search for information",
    )
    people_focus_prompt: str | None = Field(
        default=None,
        description="Description of people to find (roles, responsibilities)",
    )
    lead_struct: str | None = Field(
        default=None,
        description="Custom schema for returned lead data as a JSON object",
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=FindPhoneInput)
@serialize_pydantic_return
async def find_phone(
    name: str,
    api_key: str,
    company: str | None = None,
    linkedin_url: str | None = None,
    domain: str | None = None,
    email: str | None = None,
) -> FindPhoneOutput:
    """Find phone numbers for a lead using Sixtyfour AI."""
    if not api_key or not api_key.strip():
        return FindPhoneOutput(
            success=False,
            error="Sixtyfour AI API key is empty. Please configure a valid credential.",
        )

    lead: dict[str, Any] = {"name": name}
    if company:
        lead["company"] = company
    if linkedin_url:
        lead["linkedin_url"] = linkedin_url
    if domain:
        lead["domain"] = domain
    if email:
        lead["email"] = email
    body: dict[str, Any] = {"lead": lead}

    try:
        async with httpx.AsyncClient(timeout=_CONTACT_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/find-phone", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return FindPhoneOutput(
                success=False,
                error=f"Sixtyfour AI API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return FindPhoneOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindPhoneOutput(success=False, error=f"Find phone failed: {exc}")

    return FindPhoneOutput(
        success=True,
        name=data.get("name"),
        company=data.get("company"),
        phone=_parse_phone(data.get("phone")),
        linkedin_url=data.get("linkedin_url"),
    )


@tool(args_schema=FindEmailInput)
@serialize_pydantic_return
async def find_email(
    name: str,
    api_key: str,
    company: str | None = None,
    linkedin_url: str | None = None,
    domain: str | None = None,
    phone: str | None = None,
    title: str | None = None,
    mode: str | None = None,
) -> FindEmailOutput:
    """Find email addresses for a lead using Sixtyfour AI."""
    if not api_key or not api_key.strip():
        return FindEmailOutput(
            success=False,
            error="Sixtyfour AI API key is empty. Please configure a valid credential.",
        )

    lead: dict[str, Any] = {"name": name}
    if company:
        lead["company"] = company
    if linkedin_url:
        lead["linkedin"] = linkedin_url
    if domain:
        lead["domain"] = domain
    if phone:
        lead["phone"] = phone
    if title:
        lead["title"] = title
    body: dict[str, Any] = {"lead": lead}
    if mode:
        body["mode"] = mode

    try:
        async with httpx.AsyncClient(timeout=_CONTACT_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/find-email", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return FindEmailOutput(
                success=False,
                error=f"Sixtyfour AI API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return FindEmailOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindEmailOutput(success=False, error=f"Find email failed: {exc}")

    return FindEmailOutput(
        success=True,
        name=data.get("name"),
        company=data.get("company"),
        title=data.get("title"),
        phone=data.get("phone"),
        linkedin_url=data.get("linkedin"),
        emails=_parse_emails(data.get("email")),
        personal_emails=_parse_emails(data.get("personal_email")),
    )


@tool(args_schema=EnrichLeadInput)
@serialize_pydantic_return
async def enrich_lead(
    lead_info: str,
    struct: str,
    api_key: str,
    research_plan: str | None = None,
) -> EnrichLeadOutput:
    """Enrich a lead with contact details, social profiles, and company data using Sixtyfour AI."""
    if not api_key or not api_key.strip():
        return EnrichLeadOutput(
            success=False,
            error="Sixtyfour AI API key is empty. Please configure a valid credential.",
        )

    try:
        body: dict[str, Any] = {
            "lead_info": _coerce_json_object(lead_info, "lead_info"),
            "struct": _coerce_json_object(struct, "struct"),
        }
    except ValueError as exc:
        return EnrichLeadOutput(success=False, error=str(exc))
    if research_plan:
        body["research_plan"] = research_plan

    try:
        async with httpx.AsyncClient(timeout=_ENRICH_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/enrich-lead", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return EnrichLeadOutput(
                success=False,
                error=f"Sixtyfour AI API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return EnrichLeadOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return EnrichLeadOutput(success=False, error=f"Enrich lead failed: {exc}")

    return EnrichLeadOutput(
        success=True,
        notes=data.get("notes"),
        structured_data=data.get("structured_data") or {},
        references=data.get("references") or {},
        confidence_score=data.get("confidence_score"),
    )


@tool(args_schema=EnrichCompanyInput)
@serialize_pydantic_return
async def enrich_company(
    target_company: str,
    struct: str,
    api_key: str,
    find_people: bool | None = None,
    full_org_chart: bool | None = None,
    research_plan: str | None = None,
    people_focus_prompt: str | None = None,
    lead_struct: str | None = None,
) -> EnrichCompanyOutput:
    """Enrich company data and find associated people using Sixtyfour AI."""
    if not api_key or not api_key.strip():
        return EnrichCompanyOutput(
            success=False,
            error="Sixtyfour AI API key is empty. Please configure a valid credential.",
        )

    try:
        body: dict[str, Any] = {
            "target_company": _coerce_json_object(target_company, "target_company"),
            "struct": _coerce_json_object(struct, "struct"),
        }
        if lead_struct is not None:
            body["lead_struct"] = _coerce_json_object(lead_struct, "lead_struct")
    except ValueError as exc:
        return EnrichCompanyOutput(success=False, error=str(exc))
    if find_people is not None:
        body["find_people"] = find_people
    if full_org_chart is not None:
        body["full_org_chart"] = full_org_chart
    if research_plan:
        body["research_plan"] = research_plan
    if people_focus_prompt:
        body["people_focus_prompt"] = people_focus_prompt

    try:
        async with httpx.AsyncClient(timeout=_ENRICH_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/enrich-company", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return EnrichCompanyOutput(
                success=False,
                error=f"Sixtyfour AI API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return EnrichCompanyOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return EnrichCompanyOutput(success=False, error=f"Enrich company failed: {exc}")

    return EnrichCompanyOutput(
        success=True,
        notes=data.get("notes"),
        structured_data=data.get("structured_data") or {},
        references=data.get("references") or {},
        confidence_score=data.get("confidence_score"),
        org_chart=data.get("org_chart"),
    )
