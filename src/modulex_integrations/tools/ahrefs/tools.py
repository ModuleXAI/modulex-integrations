"""Ahrefs LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.ahrefs.outputs import (
    BacklinkItem,
    GetBacklinksOnePerDomainOutput,
    GetBacklinksOutput,
    GetReferringDomainsOutput,
    ReferringDomainItem,
)

__all__ = [
    "get_backlinks",
    "get_backlinks_one_per_domain",
    "get_referring_domains",
]

_BASE_URL = "https://api.ahrefs.com/v3"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Ahrefs API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas ------------------------------------------------------------


class GetBacklinksInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    target: str = Field(description="Domain or URL to get backlinks for")
    select: list[str] = Field(description="List of columns to return (e.g. url_from, url_to, ahrefs_rank)")
    mode: str = Field(default="domain", description="Mode of operation: exact, domain, subdomains, or prefix")
    limit: int = Field(default=1000, description="Number of results to return")


class GetBacklinksOnePerDomainInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    target: str = Field(description="Domain or URL to get backlinks for")
    select: list[str] = Field(description="List of columns to return (e.g. url_from, url_to, ahrefs_rank)")
    mode: str = Field(default="domain", description="Mode of operation: exact, domain, subdomains, or prefix")
    limit: int = Field(default=1000, description="Number of results to return")


class GetReferringDomainsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    target: str = Field(description="Domain or URL to get referring domains for")
    select: list[str] = Field(description="List of columns to return for referring domains")
    mode: str = Field(default="domain", description="Mode of operation: exact, domain, subdomains, or prefix")
    limit: int = Field(default=1000, description="Number of results to return")


# --- @tool functions ----------------------------------------------------------


@tool(args_schema=GetBacklinksInput)
@serialize_pydantic_return
async def get_backlinks(
    auth_type: str,
    auth_data: dict[str, Any],
    target: str,
    select: list[str],
    mode: str = "domain",
    limit: int = 1000,
) -> GetBacklinksOutput:
    """Get the backlinks for a domain or URL with details for the referring pages (e.g., anchor and page title)."""
    if not auth_data.get("access_token"):
        return GetBacklinksOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/site-explorer/all-backlinks",
                headers=headers,
                params={
                    "target": target,
                    "select": ",".join(select),
                    "mode": mode,
                    "limit": limit,
                    "output": "json",
                },
            )
        if response.status_code != 200:
            return GetBacklinksOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetBacklinksOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetBacklinksOutput(success=False, error=f"Call failed: {exc}")

    backlinks_raw = data.get("backlinks", [])
    backlinks = [
        BacklinkItem(
            url_from=item.get("url_from"),
            url_to=item.get("url_to"),
            ahrefs_rank=item.get("ahrefs_rank"),
            anchor=item.get("anchor"),
            page_title=item.get("page_title"),
            first_seen=item.get("first_seen"),
            last_seen=item.get("last_seen"),
            domain_rating=item.get("domain_rating"),
            extra={k: v for k, v in item.items() if k not in ("url_from", "url_to", "ahrefs_rank", "anchor", "page_title", "first_seen", "last_seen", "domain_rating")} or None,
        )
        for item in backlinks_raw
    ]
    return GetBacklinksOutput(
        success=True,
        backlinks=backlinks,
        total=len(backlinks),
    )


@tool(args_schema=GetBacklinksOnePerDomainInput)
@serialize_pydantic_return
async def get_backlinks_one_per_domain(
    auth_type: str,
    auth_data: dict[str, Any],
    target: str,
    select: list[str],
    mode: str = "domain",
    limit: int = 1000,
) -> GetBacklinksOnePerDomainOutput:
    """Get one backlink with the highest ahrefs_rank per referring domain for a target URL or domain."""
    if not auth_data.get("access_token"):
        return GetBacklinksOnePerDomainOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/site-explorer/all-backlinks",
                headers=headers,
                params={
                    "target": target,
                    "select": ",".join(select),
                    "mode": mode,
                    "limit": limit,
                    "aggregation": "1_per_domain",
                    "output": "json",
                },
            )
        if response.status_code != 200:
            return GetBacklinksOnePerDomainOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetBacklinksOnePerDomainOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetBacklinksOnePerDomainOutput(success=False, error=f"Call failed: {exc}")

    backlinks_raw = data.get("backlinks", [])
    backlinks = [
        BacklinkItem(
            url_from=item.get("url_from"),
            url_to=item.get("url_to"),
            ahrefs_rank=item.get("ahrefs_rank"),
            anchor=item.get("anchor"),
            page_title=item.get("page_title"),
            first_seen=item.get("first_seen"),
            last_seen=item.get("last_seen"),
            domain_rating=item.get("domain_rating"),
            extra={k: v for k, v in item.items() if k not in ("url_from", "url_to", "ahrefs_rank", "anchor", "page_title", "first_seen", "last_seen", "domain_rating")} or None,
        )
        for item in backlinks_raw
    ]
    return GetBacklinksOnePerDomainOutput(
        success=True,
        backlinks=backlinks,
        total=len(backlinks),
    )


@tool(args_schema=GetReferringDomainsInput)
@serialize_pydantic_return
async def get_referring_domains(
    auth_type: str,
    auth_data: dict[str, Any],
    target: str,
    select: list[str],
    mode: str = "domain",
    limit: int = 1000,
) -> GetReferringDomainsOutput:
    """Get the referring domains that contain backlinks to the target URL or domain."""
    if not auth_data.get("access_token"):
        return GetReferringDomainsOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/site-explorer/refdomains",
                headers=headers,
                params={
                    "target": target,
                    "select": ",".join(select),
                    "mode": mode,
                    "limit": limit,
                    "output": "json",
                },
            )
        if response.status_code != 200:
            return GetReferringDomainsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetReferringDomainsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetReferringDomainsOutput(success=False, error=f"Call failed: {exc}")

    refdomains_raw = data.get("refdomains", [])
    refdomains = [
        ReferringDomainItem(
            domain=item.get("domain"),
            domain_rating=item.get("domain_rating"),
            backlinks=item.get("backlinks"),
            first_seen=item.get("first_seen"),
            last_seen=item.get("last_seen"),
            extra={k: v for k, v in item.items() if k not in ("domain", "domain_rating", "backlinks", "first_seen", "last_seen")} or None,
        )
        for item in refdomains_raw
    ]
    return GetReferringDomainsOutput(
        success=True,
        refdomains=refdomains,
        total=len(refdomains),
    )
