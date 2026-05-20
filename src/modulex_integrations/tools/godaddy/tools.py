"""GoDaddy LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.godaddy.outputs import (
    CheckDomainAvailabilityOutput,
    DomainSummary,
    ListDomainsOutput,
    ListTldsOptionsOutput,
    RenewDomainOutput,
    SuggestDomainsOutput,
    TldInfo,
)

__all__ = [
    "check_domain_availability",
    "list_domains",
    "list_tlds_options",
    "renew_domain",
    "suggest_domains",
]

_DEFAULT_BASE_URL = "https://api.godaddy.com"
_TIMEOUT = 30.0


def _get_headers(auth_data: dict[str, Any]) -> dict[str, str]:
    """Build GoDaddy sso-key authorization headers."""
    api_key = auth_data.get("api_key", "")
    api_secret = auth_data.get("api_secret", "")
    return {
        "Authorization": f"sso-key {api_key}:{api_secret}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _base_url(auth_data: dict[str, Any]) -> str:
    """Resolve base URL from auth_data, defaulting to production."""
    url = auth_data.get("api_url", "") or _DEFAULT_BASE_URL
    return url.rstrip("/")


# --- Input schemas --------------------------------------------------------


class CheckDomainAvailabilityInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    domain: str = Field(description="The domain name to check availability for")
    check_type: str | None = Field(default=None, description="Optimize for time (FAST) or accuracy (FULL)")
    for_transfer: bool | None = Field(default=None, description="Whether to include domains available for transfer")


class ListDomainsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    statuses: list[str] | None = Field(default=None, description="Filter by status")
    status_groups: list[str] | None = Field(default=None, description="Filter by status group")
    limit: int | None = Field(default=None, description="Maximum number of domains to return")
    marker: str | None = Field(default=None, description="Marker domain for pagination offset")
    includes: list[str] | None = Field(default=None, description="Optional details to include")
    modified_date: str | None = Field(default=None, description="Only include results modified since this date")


class ListTldsOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class RenewDomainInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    domain: str = Field(description="The domain name to renew")
    period: int | None = Field(default=None, description="Number of years to extend the domain (1-10)")


class SuggestDomainsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str = Field(description="Domain name or keywords for suggestions")
    country: str | None = Field(default=None, description="Two-letter ISO country code")
    city: str | None = Field(default=None, description="City name as a hint for target region")
    sources: list[str] | None = Field(default=None, description="Sources to query")
    tlds: list[str] | None = Field(default=None, description="TLDs to include in suggestions")
    length_max: int | None = Field(default=None, description="Maximum length of second-level domain")
    length_min: int | None = Field(default=None, description="Minimum length of second-level domain")
    limit: int | None = Field(default=None, description="Maximum number of suggestions to return")
    wait_ms: int | None = Field(default=None, description="Maximum time in milliseconds to wait")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CheckDomainAvailabilityInput)
@serialize_pydantic_return
async def check_domain_availability(
    auth_type: str,
    auth_data: dict[str, Any],
    domain: str,
    check_type: str | None = None,
    for_transfer: bool | None = None,
) -> CheckDomainAvailabilityOutput:
    """Check the availability of a domain for purchase or transfer."""
    api_key = auth_data.get("api_key", "")
    api_secret = auth_data.get("api_secret", "")
    if not api_key or not api_secret:
        return CheckDomainAvailabilityOutput(
            success=False,
            error="GoDaddy requires both api_key and api_secret credentials.",
        )

    headers = _get_headers(auth_data)
    base = _base_url(auth_data)
    params: dict[str, Any] = {"domain": domain}
    if check_type is not None:
        params["checkType"] = check_type
    if for_transfer is not None:
        params["forTransfer"] = for_transfer

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base}/v1/domains/available",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return CheckDomainAvailabilityOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CheckDomainAvailabilityOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CheckDomainAvailabilityOutput(success=False, error=f"Call failed: {exc}")

    return CheckDomainAvailabilityOutput(
        success=True,
        available=data.get("available"),
        domain=data.get("domain"),
        definitive=data.get("definitive"),
        price=data.get("price"),
        currency=data.get("currency"),
        period=data.get("period"),
    )


@tool(args_schema=ListDomainsInput)
@serialize_pydantic_return
async def list_domains(
    auth_type: str,
    auth_data: dict[str, Any],
    statuses: list[str] | None = None,
    status_groups: list[str] | None = None,
    limit: int | None = None,
    marker: str | None = None,
    includes: list[str] | None = None,
    modified_date: str | None = None,
) -> ListDomainsOutput:
    """List domains owned by the authenticated GoDaddy account."""
    api_key = auth_data.get("api_key", "")
    api_secret = auth_data.get("api_secret", "")
    if not api_key or not api_secret:
        return ListDomainsOutput(
            success=False,
            error="GoDaddy requires both api_key and api_secret credentials.",
        )

    headers = _get_headers(auth_data)
    base = _base_url(auth_data)
    params: dict[str, Any] = {}
    if statuses is not None:
        params["statuses"] = ",".join(statuses)
    if status_groups is not None:
        params["statusGroups"] = ",".join(status_groups)
    if limit is not None:
        params["limit"] = limit
    if marker is not None:
        params["marker"] = marker
    if includes is not None:
        params["includes"] = ",".join(includes)
    if modified_date is not None:
        params["modifiedDate"] = modified_date

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base}/v1/domains",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListDomainsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListDomainsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDomainsOutput(success=False, error=f"Call failed: {exc}")

    domains = [
        DomainSummary(
            domain=d.get("domain"),
            status=d.get("status"),
            expires=d.get("expires"),
            created_at=d.get("createdAt"),
            renewable=d.get("renewable"),
        )
        for d in (data if isinstance(data, list) else [])
    ]
    return ListDomainsOutput(success=True, domains=domains)


@tool(args_schema=ListTldsOptionsInput)
@serialize_pydantic_return
async def list_tlds_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListTldsOptionsOutput:
    """Retrieve the list of available top-level domains (TLDs)."""
    api_key = auth_data.get("api_key", "")
    api_secret = auth_data.get("api_secret", "")
    if not api_key or not api_secret:
        return ListTldsOptionsOutput(
            success=False,
            error="GoDaddy requires both api_key and api_secret credentials.",
        )

    headers = _get_headers(auth_data)
    base = _base_url(auth_data)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base}/v1/domains/tlds",
                headers=headers,
            )
        if response.status_code != 200:
            return ListTldsOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListTldsOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTldsOptionsOutput(success=False, error=f"Call failed: {exc}")

    tlds = [
        TldInfo(name=t.get("name"), type=t.get("type"))
        for t in (data if isinstance(data, list) else [])
    ]
    return ListTldsOptionsOutput(success=True, tlds=tlds)


@tool(args_schema=RenewDomainInput)
@serialize_pydantic_return
async def renew_domain(
    auth_type: str,
    auth_data: dict[str, Any],
    domain: str,
    period: int | None = None,
) -> RenewDomainOutput:
    """Renew a domain registration in GoDaddy."""
    api_key = auth_data.get("api_key", "")
    api_secret = auth_data.get("api_secret", "")
    if not api_key or not api_secret:
        return RenewDomainOutput(
            success=False,
            error="GoDaddy requires both api_key and api_secret credentials.",
        )

    headers = _get_headers(auth_data)
    base = _base_url(auth_data)
    body: dict[str, Any] = {}
    if period is not None:
        body["period"] = period

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{base}/v1/domains/{domain}/renew",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return RenewDomainOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return RenewDomainOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RenewDomainOutput(success=False, error=f"Call failed: {exc}")

    return RenewDomainOutput(
        success=True,
        order_id=data.get("orderId"),
        item_count=data.get("itemCount"),
        total=data.get("total"),
        currency=data.get("currency"),
    )


@tool(args_schema=SuggestDomainsInput)
@serialize_pydantic_return
async def suggest_domains(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    country: str | None = None,
    city: str | None = None,
    sources: list[str] | None = None,
    tlds: list[str] | None = None,
    length_max: int | None = None,
    length_min: int | None = None,
    limit: int | None = None,
    wait_ms: int | None = None,
) -> SuggestDomainsOutput:
    """Suggest available domain names based on given criteria."""
    api_key = auth_data.get("api_key", "")
    api_secret = auth_data.get("api_secret", "")
    if not api_key or not api_secret:
        return SuggestDomainsOutput(
            success=False,
            error="GoDaddy requires both api_key and api_secret credentials.",
        )

    headers = _get_headers(auth_data)
    base = _base_url(auth_data)
    params: dict[str, Any] = {"query": query}
    if country is not None:
        params["country"] = country
    if city is not None:
        params["city"] = city
    if sources is not None:
        params["sources"] = ",".join(sources)
    if tlds is not None:
        params["tlds"] = ",".join(tlds)
    if length_max is not None:
        params["lengthMax"] = length_max
    if length_min is not None:
        params["lengthMin"] = length_min
    if limit is not None:
        params["limit"] = limit
    if wait_ms is not None:
        params["waitMs"] = wait_ms

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base}/v1/domains/suggest",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return SuggestDomainsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SuggestDomainsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SuggestDomainsOutput(success=False, error=f"Call failed: {exc}")

    suggestions = data if isinstance(data, list) else []
    return SuggestDomainsOutput(success=True, suggestions=suggestions)
