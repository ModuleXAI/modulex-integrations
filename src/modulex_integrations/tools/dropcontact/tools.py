"""Dropcontact LangChain ``@tool`` functions.

One async tool wrapping the Dropcontact B2B enrichment REST API. The
calling convention is **key-based**: the modulex ``ToolExecutor``
injects an ``api_key: str`` directly (resolved from the user's API
key credential), which is sent as the ``X-Access-Token`` request
header — not an ``auth_type``/``auth_data`` pair.

Enrichment is asynchronous. ``enrich_contact`` submits the contact,
receives a ``request_id``, then polls the result endpoint every few
seconds until the enrichment is ready or the polling window expires.
The whole submit-then-poll loop is folded into the single tool body.

Error model: any non-2xx response, an error flag in the API JSON, a
timeout, or the polling window expiring is returned as
``success=False`` + ``error`` rather than raising.
"""
from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.dropcontact.outputs import (
    EmailEntry,
    EnrichContactOutput,
)

__all__ = ["enrich_contact"]

_DROPCONTACT_API_BASE = "https://api.dropcontact.com"
_SUBMIT_PATH = "/v1/enrich/all"
_REQUEST_TIMEOUT = 30.0
_POLL_INTERVAL_SECONDS = 5.0
_MAX_POLL_SECONDS = 120.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "X-Access-Token": api_key,
        "Content-Type": "application/json",
    }


# --- Input schemas (args_schema for each @tool) ----------------------------


class EnrichContactInput(BaseModel):
    api_key: str = Field(
        description="Dropcontact API key (provided by credential system)"
    )
    email: str | None = Field(
        default=None, description="Email address of the contact to enrich"
    )
    first_name: str | None = Field(
        default=None, description="First name of the contact"
    )
    last_name: str | None = Field(
        default=None, description="Last name of the contact"
    )
    full_name: str | None = Field(
        default=None,
        description="Full name (alternative to first_name + last_name)",
    )
    company: str | None = Field(default=None, description="Company name")
    website: str | None = Field(
        default=None, description="Company website (e.g. acme.com)"
    )
    num_siren: str | None = Field(
        default=None, description="French company SIREN number"
    )
    phone: str | None = Field(default=None, description="Phone number")
    linkedin: str | None = Field(
        default=None, description="LinkedIn profile URL"
    )
    country: str | None = Field(
        default=None,
        description='Country code (ISO 3166-1 alpha-2, e.g. "US", "FR")',
    )
    siren: bool = Field(
        default=False,
        description="Include SIREN/SIRET enrichment (France only)",
    )
    language: str | None = Field(
        default=None, description='Language for returned data (e.g. "en", "fr")'
    )


# --- @tool functions -------------------------------------------------------


def _map_contact(request_id: str | None, contact: dict[str, Any]) -> EnrichContactOutput:
    """Map a raw enriched-contact object to the flat output model."""
    raw_emails = contact.get("email")
    email_entries = raw_emails if isinstance(raw_emails, list) else []
    emails = [
        EmailEntry(
            email=entry.get("email"),
            qualification=entry.get("qualification"),
        )
        for entry in email_entries
        if isinstance(entry, dict)
    ]
    first_email = emails[0] if emails else None

    return EnrichContactOutput(
        success=True,
        request_id=request_id,
        email_found=bool(first_email and first_email.email),
        email=first_email.email if first_email else None,
        emails=emails,
        qualification=first_email.qualification if first_email else None,
        first_name=contact.get("first_name"),
        last_name=contact.get("last_name"),
        full_name=contact.get("full_name"),
        civility=contact.get("civility"),
        phone=contact.get("phone"),
        mobile_phone=contact.get("mobile_phone"),
        company=contact.get("company"),
        website=contact.get("website"),
        company_linkedin=contact.get("company_linkedin"),
        linkedin=contact.get("linkedin"),
        country=contact.get("country"),
        siren=contact.get("siren"),
        siret=contact.get("siret"),
        siret_address=contact.get("siret_address"),
        siret_zip=contact.get("siret_zip"),
        siret_city=contact.get("siret_city"),
        vat=contact.get("vat"),
        nb_employees=contact.get("nb_employees"),
        employee_count=contact.get("employee_count"),
        naf5_code=contact.get("naf5_code"),
        naf5_des=contact.get("naf5_des"),
        industry=contact.get("industry"),
        job=contact.get("job"),
        job_level=contact.get("job_level"),
        job_function=contact.get("job_function"),
        company_turnover=contact.get("company_turnover"),
        company_results=contact.get("company_results"),
    )


@tool(args_schema=EnrichContactInput)
@serialize_pydantic_return
async def enrich_contact(
    api_key: str,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    full_name: str | None = None,
    company: str | None = None,
    website: str | None = None,
    num_siren: str | None = None,
    phone: str | None = None,
    linkedin: str | None = None,
    country: str | None = None,
    siren: bool = False,
    language: str | None = None,
) -> EnrichContactOutput:
    """Enrich a contact with verified B2B email, phone, company data, and
    LinkedIn info. Submits an async enrichment request, then polls until the
    result is ready (up to 2 minutes). A credit is charged only when a
    verified email is returned. Provide at least one of: email,
    first_name + last_name + company, full_name + company, or a LinkedIn URL.
    """
    if not api_key or not api_key.strip():
        return EnrichContactOutput(
            success=False,
            error="Dropcontact API key is empty. Please configure a valid credential.",
        )

    contact: dict[str, Any] = {}
    if email:
        contact["email"] = email
    if first_name:
        contact["first_name"] = first_name
    if last_name:
        contact["last_name"] = last_name
    if full_name:
        contact["full_name"] = full_name
    if company:
        contact["company"] = company
    if website:
        contact["website"] = website
    if num_siren:
        contact["num_siren"] = num_siren
    if phone:
        contact["phone"] = phone
    if linkedin:
        contact["linkedin"] = linkedin
    if country:
        contact["country"] = country

    if not contact:
        return EnrichContactOutput(
            success=False,
            error=(
                "No contact fields provided. Supply at least one of: email, "
                "first_name + last_name + company, full_name + company, or linkedin."
            ),
        )

    body: dict[str, Any] = {"data": [contact], "siren": siren}
    if language:
        body["language"] = language

    headers = _headers(api_key)

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            submit_response = await client.post(
                f"{_DROPCONTACT_API_BASE}{_SUBMIT_PATH}",
                headers=headers,
                json=body,
            )
            if submit_response.status_code != 200:
                return EnrichContactOutput(
                    success=False,
                    error=(
                        f"Dropcontact API error ({submit_response.status_code}): "
                        f"{submit_response.text}"
                    ),
                )
            submit_json = submit_response.json()
            if submit_json.get("error"):
                reason = submit_json.get("reason") or submit_json.get("error")
                return EnrichContactOutput(
                    success=False,
                    error=f"Dropcontact enrichment failed: {reason}",
                )

            request_id = submit_json.get("request_id")
            if not request_id:
                return EnrichContactOutput(
                    success=False,
                    error="Dropcontact enrichment did not return a request_id.",
                )

            poll_url = f"{_DROPCONTACT_API_BASE}{_SUBMIT_PATH}/{quote(str(request_id), safe='')}"
            elapsed = 0.0
            while elapsed < _MAX_POLL_SECONDS:
                await asyncio.sleep(_POLL_INTERVAL_SECONDS)
                elapsed += _POLL_INTERVAL_SECONDS

                poll_response = await client.get(poll_url, headers=headers)
                if poll_response.status_code != 200:
                    return EnrichContactOutput(
                        success=False,
                        error=(
                            f"Dropcontact poll error ({poll_response.status_code}): "
                            f"{poll_response.text}"
                        ),
                    )

                poll_json = poll_response.json()
                if poll_json.get("error"):
                    reason = poll_json.get("reason") or poll_json.get("error")
                    return EnrichContactOutput(
                        success=False,
                        error=f"Dropcontact enrichment failed: {reason}",
                    )

                # Still processing — keep polling.
                if not poll_json.get("success"):
                    continue

                contacts = poll_json.get("data")
                first_contact = contacts[0] if isinstance(contacts, list) and contacts else {}
                return _map_contact(str(request_id), first_contact)
    except httpx.TimeoutException:
        return EnrichContactOutput(
            success=False, error="Request to Dropcontact timed out."
        )
    except Exception as exc:
        return EnrichContactOutput(
            success=False, error=f"enrich_contact failed: {exc}"
        )

    return EnrichContactOutput(
        success=False,
        error="Dropcontact enrichment did not complete within the polling window.",
    )
