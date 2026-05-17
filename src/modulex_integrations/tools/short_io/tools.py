"""Short.io LangChain ``@tool`` functions."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.short_io.outputs import (
    CreateLinkOutput,
    DeleteLinkOutput,
    ExpireLinkOutput,
    GetDomainStatisticsOutput,
    GetLinkInfoOutput,
    ListDomainsOutput,
    ListLinksOutput,
    ShortIODomain,
    ShortIOLink,
    UpdateLinkOutput,
)

__all__ = [
    "create_link",
    "delete_link",
    "expire_link",
    "get_domain_statistics",
    "get_link_info",
    "list_domains",
    "list_links",
    "update_link",
]

_BASE_URL = "https://api.short.io"
_STATS_BASE_URL = "https://api-v2.short.cm"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    # Short.io expects the raw API key in Authorization, no "Bearer " prefix.
    return {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _filter_none(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def _parse_expires_at(expires_at: str | None) -> int | None:
    """Convert ``yyyy-mm-dd`` string to Unix ms timestamp."""
    if not expires_at:
        return None
    try:
        dt = datetime.strptime(expires_at, "%Y-%m-%d")
    except ValueError:
        return None
    return int(dt.timestamp() * 1000)


def _extract_error(response: httpx.Response) -> str:
    try:
        body = response.json()
        if isinstance(body, dict):
            for key in ("message", "error"):
                msg = body.get(key)
                if msg:
                    return str(msg)
    except Exception:
        pass
    return response.text


def _empty_key_error(name: str) -> str:
    return (
        f"Short.io API key is empty for {name}. "
        "Please configure a valid credential."
    )


class CreateLinkInput(BaseModel):
    api_key: str = Field(description="Short.io API key (provided by credential system)")
    domain: str = Field(description="Domain name for the short link")
    original_url: str = Field(description="The original URL to shorten")
    path: str | None = Field(default=None, description="Custom path")
    title: str | None = Field(default=None, description="Title for the link")
    tags: list[str] | None = Field(default=None, description="Tags for organizing links")
    allow_duplicates: bool | None = Field(default=None, description="Allow duplicates")
    expires_at: str | None = Field(default=None, description="Expiration date yyyy-mm-dd")
    expired_url: str | None = Field(default=None, description="Redirect URL after expiry")
    iphone_url: str | None = Field(default=None, description="iPhone redirect URL")
    android_url: str | None = Field(default=None, description="Android redirect URL")
    password: str | None = Field(default=None, description="Password protection")
    utm_source: str | None = Field(default=None, description="UTM source")
    utm_medium: str | None = Field(default=None, description="UTM medium")
    utm_campaign: str | None = Field(default=None, description="UTM campaign")
    utm_term: str | None = Field(default=None, description="UTM term")
    utm_content: str | None = Field(default=None, description="UTM content")
    cloaking: bool | None = Field(default=None, description="Enable link cloaking")
    redirect_type: int | None = Field(default=None, description="HTTP redirect status")
    folder_id: str | None = Field(default=None, description="Folder ID")


class UpdateLinkInput(BaseModel):
    api_key: str = Field(description="Short.io API key (provided by credential system)")
    link_id: str = Field(description="The ID of the link to update")
    original_url: str | None = Field(default=None, description="New original URL")
    path: str | None = Field(default=None, description="New custom path")
    title: str | None = Field(default=None, description="New title")
    tags: list[str] | None = Field(default=None, description="New tags")
    expires_at: str | None = Field(default=None, description="New expiration yyyy-mm-dd")
    expired_url: str | None = Field(default=None, description="New expired URL")
    iphone_url: str | None = Field(default=None, description="New iPhone URL")
    android_url: str | None = Field(default=None, description="New Android URL")
    password: str | None = Field(default=None, description="New password")
    utm_source: str | None = Field(default=None, description="New UTM source")
    utm_medium: str | None = Field(default=None, description="New UTM medium")
    utm_campaign: str | None = Field(default=None, description="New UTM campaign")
    utm_term: str | None = Field(default=None, description="New UTM term")
    utm_content: str | None = Field(default=None, description="New UTM content")
    cloaking: bool | None = Field(default=None, description="Enable/disable cloaking")
    redirect_type: int | None = Field(default=None, description="New redirect status")


class DeleteLinkInput(BaseModel):
    api_key: str = Field(description="Short.io API key (provided by credential system)")
    link_id: str = Field(description="The ID of the link to delete")


class ExpireLinkInput(BaseModel):
    api_key: str = Field(description="Short.io API key (provided by credential system)")
    link_id: str = Field(description="The ID of the link to expire")
    expires_at: str = Field(description="Expiration date in yyyy-mm-dd format")
    expired_url: str = Field(description="URL to redirect to when link expires")


class GetLinkInfoInput(BaseModel):
    api_key: str = Field(description="Short.io API key (provided by credential system)")
    domain: str = Field(description="Domain of the short link")
    path: str = Field(description="Path of the short link")


class ListLinksInput(BaseModel):
    api_key: str = Field(description="Short.io API key (provided by credential system)")
    domain_id: int = Field(description="Domain ID to list links for")
    limit: int = Field(default=150, description="Maximum links (capped at 150)")


class ListDomainsInput(BaseModel):
    api_key: str = Field(description="Short.io API key (provided by credential system)")


class GetDomainStatisticsInput(BaseModel):
    api_key: str = Field(description="Short.io API key (provided by credential system)")
    domain_id: int = Field(description="Domain ID to get statistics for")
    period: str | None = Field(default="last30", description="Time period")
    clicks_chart_interval: str | None = Field(default=None, description="Chart interval")
    tz_offset: int | None = Field(default=None, description="Timezone offset in minutes")
    start_date: str | None = Field(default=None, description="Custom period start yyyy-mm-dd")
    end_date: str | None = Field(default=None, description="Custom period end yyyy-mm-dd")


def _link_from(data: dict[str, Any]) -> ShortIOLink:
    return ShortIOLink.model_validate(
        {k: v for k, v in data.items() if k in ShortIOLink.model_fields}
    )


@tool(args_schema=CreateLinkInput)
@serialize_pydantic_return
async def create_link(
    api_key: str,
    domain: str,
    original_url: str,
    path: str | None = None,
    title: str | None = None,
    tags: list[str] | None = None,
    allow_duplicates: bool | None = None,
    expires_at: str | None = None,
    expired_url: str | None = None,
    iphone_url: str | None = None,
    android_url: str | None = None,
    password: str | None = None,
    utm_source: str | None = None,
    utm_medium: str | None = None,
    utm_campaign: str | None = None,
    utm_term: str | None = None,
    utm_content: str | None = None,
    cloaking: bool | None = None,
    redirect_type: int | None = None,
    folder_id: str | None = None,
) -> CreateLinkOutput:
    """Create a new short link using Short.io."""
    if not api_key or not api_key.strip():
        return CreateLinkOutput(success=False, error=_empty_key_error("create_link"))

    payload = _filter_none(
        {
            "domain": domain,
            "originalURL": original_url,
            "path": path,
            "title": title,
            "tags": tags,
            "allowDuplicates": allow_duplicates,
            "expiresAt": _parse_expires_at(expires_at),
            "expiredURL": expired_url,
            "iphoneURL": iphone_url,
            "androidURL": android_url,
            "password": password,
            "utmSource": utm_source,
            "utmMedium": utm_medium,
            "utmCampaign": utm_campaign,
            "utmTerm": utm_term,
            "utmContent": utm_content,
            "cloaking": cloaking,
            "redirectType": redirect_type,
            "folderId": folder_id,
        }
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/links", headers=_headers(api_key), json=payload
            )
        if response.status_code not in (200, 201):
            return CreateLinkOutput(
                success=False,
                error=f"API error ({response.status_code}): {_extract_error(response)}",
            )
        body = response.json() or {}
    except Exception as exc:
        return CreateLinkOutput(success=False, error=f"Create link failed: {exc}")

    return CreateLinkOutput(success=True, link=_link_from(body))


@tool(args_schema=UpdateLinkInput)
@serialize_pydantic_return
async def update_link(
    api_key: str,
    link_id: str,
    original_url: str | None = None,
    path: str | None = None,
    title: str | None = None,
    tags: list[str] | None = None,
    expires_at: str | None = None,
    expired_url: str | None = None,
    iphone_url: str | None = None,
    android_url: str | None = None,
    password: str | None = None,
    utm_source: str | None = None,
    utm_medium: str | None = None,
    utm_campaign: str | None = None,
    utm_term: str | None = None,
    utm_content: str | None = None,
    cloaking: bool | None = None,
    redirect_type: int | None = None,
) -> UpdateLinkOutput:
    """Update an existing Short.io short link."""
    if not api_key or not api_key.strip():
        return UpdateLinkOutput(success=False, error=_empty_key_error("update_link"))

    payload = _filter_none(
        {
            "originalURL": original_url,
            "path": path,
            "title": title,
            "tags": tags,
            "expiresAt": _parse_expires_at(expires_at),
            "expiredURL": expired_url,
            "iphoneURL": iphone_url,
            "androidURL": android_url,
            "password": password,
            "utmSource": utm_source,
            "utmMedium": utm_medium,
            "utmCampaign": utm_campaign,
            "utmTerm": utm_term,
            "utmContent": utm_content,
            "cloaking": cloaking,
            "redirectType": redirect_type,
        }
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # Short.io uses POST (not PATCH) for updates.
            response = await client.post(
                f"{_BASE_URL}/links/{link_id}",
                headers=_headers(api_key),
                json=payload,
            )
        if response.status_code != 200:
            return UpdateLinkOutput(
                success=False,
                error=f"API error ({response.status_code}): {_extract_error(response)}",
            )
        body = response.json() or {}
    except Exception as exc:
        return UpdateLinkOutput(success=False, error=f"Update link failed: {exc}")

    return UpdateLinkOutput(success=True, link=_link_from(body))


@tool(args_schema=DeleteLinkInput)
@serialize_pydantic_return
async def delete_link(api_key: str, link_id: str) -> DeleteLinkOutput:
    """Delete a Short.io short link (irreversible)."""
    if not api_key or not api_key.strip():
        return DeleteLinkOutput(success=False, error=_empty_key_error("delete_link"))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/links/{link_id}", headers=_headers(api_key)
            )
        if not (200 <= response.status_code < 300):
            return DeleteLinkOutput(
                success=False,
                error=f"API error ({response.status_code}): {_extract_error(response)}",
            )
        parsed: dict[str, Any] | None = None
        if response.text and response.text.strip():
            try:
                value = response.json()
                if isinstance(value, dict):
                    parsed = value
            except Exception:
                parsed = None
    except Exception as exc:
        return DeleteLinkOutput(success=False, error=f"Delete link failed: {exc}")

    return DeleteLinkOutput(success=True, link_id=link_id, response=parsed)


@tool(args_schema=ExpireLinkInput)
@serialize_pydantic_return
async def expire_link(
    api_key: str, link_id: str, expires_at: str, expired_url: str
) -> ExpireLinkOutput:
    """Set expiration date and fallback URL for a Short.io link."""
    if not api_key or not api_key.strip():
        return ExpireLinkOutput(success=False, error=_empty_key_error("expire_link"))

    payload = {
        "expiresAt": _parse_expires_at(expires_at),
        "expiredURL": expired_url,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/links/{link_id}",
                headers=_headers(api_key),
                json=payload,
            )
        if response.status_code != 200:
            return ExpireLinkOutput(
                success=False,
                error=f"API error ({response.status_code}): {_extract_error(response)}",
            )
        body = response.json() or {}
    except Exception as exc:
        return ExpireLinkOutput(success=False, error=f"Expire link failed: {exc}")

    return ExpireLinkOutput(success=True, link=_link_from(body))


@tool(args_schema=GetLinkInfoInput)
@serialize_pydantic_return
async def get_link_info(api_key: str, domain: str, path: str) -> GetLinkInfoOutput:
    """Get information about a Short.io short link by domain + path."""
    if not api_key or not api_key.strip():
        return GetLinkInfoOutput(success=False, error=_empty_key_error("get_link_info"))

    clean_path = path.lstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/links/expand",
                headers=_headers(api_key),
                params={"domain": domain, "path": clean_path},
            )
        if response.status_code != 200:
            return GetLinkInfoOutput(
                success=False,
                error=f"API error ({response.status_code}): {_extract_error(response)}",
            )
        body = response.json() or {}
    except Exception as exc:
        return GetLinkInfoOutput(success=False, error=f"Get link info failed: {exc}")

    return GetLinkInfoOutput(success=True, link=_link_from(body))


@tool(args_schema=ListLinksInput)
@serialize_pydantic_return
async def list_links(api_key: str, domain_id: int, limit: int = 150) -> ListLinksOutput:
    """List Short.io links for a given domain id."""
    if not api_key or not api_key.strip():
        return ListLinksOutput(success=False, error=_empty_key_error("list_links"))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/api/links",
                headers=_headers(api_key),
                params={"domain_id": domain_id, "limit": min(limit, 150)},
            )
        if response.status_code != 200:
            return ListLinksOutput(
                success=False,
                error=f"API error ({response.status_code}): {_extract_error(response)}",
            )
        body = response.json() or {}
    except Exception as exc:
        return ListLinksOutput(success=False, error=f"List links failed: {exc}")

    raw = body.get("links", []) if isinstance(body, dict) else []
    links = [_link_from(item) for item in raw if isinstance(item, dict)]
    return ListLinksOutput(success=True, links=links, count=len(links))


@tool(args_schema=ListDomainsInput)
@serialize_pydantic_return
async def list_domains(api_key: str) -> ListDomainsOutput:
    """List all domains configured in the Short.io account."""
    if not api_key or not api_key.strip():
        return ListDomainsOutput(success=False, error=_empty_key_error("list_domains"))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/api/domains", headers=_headers(api_key)
            )
        if response.status_code != 200:
            return ListDomainsOutput(
                success=False,
                error=f"API error ({response.status_code}): {_extract_error(response)}",
            )
        body = response.json()
    except Exception as exc:
        return ListDomainsOutput(success=False, error=f"List domains failed: {exc}")

    items = body if isinstance(body, list) else []
    domains = [
        ShortIODomain(
            id=d.get("id"),
            hostname=d.get("hostname"),
            protocol=d.get("protocol"),
            created=d.get("created"),
        )
        for d in items
        if isinstance(d, dict)
    ]
    return ListDomainsOutput(success=True, domains=domains, count=len(domains))


@tool(args_schema=GetDomainStatisticsInput)
@serialize_pydantic_return
async def get_domain_statistics(
    api_key: str,
    domain_id: int,
    period: str | None = "last30",
    clicks_chart_interval: str | None = None,
    tz_offset: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> GetDomainStatisticsOutput:
    """Get click statistics and analytics for a Short.io domain."""
    if not api_key or not api_key.strip():
        return GetDomainStatisticsOutput(
            success=False, error=_empty_key_error("get_domain_statistics")
        )

    params: dict[str, Any] = _filter_none(
        {
            "period": period,
            "clicksChartInterval": clicks_chart_interval,
            "tzOffset": tz_offset,
            "startDate": start_date,
            "endDate": end_date,
        }
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_STATS_BASE_URL}/statistics/domain/{domain_id}",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return GetDomainStatisticsOutput(
                success=False,
                error=f"API error ({response.status_code}): {_extract_error(response)}",
            )
        body = response.json() or {}
    except Exception as exc:
        return GetDomainStatisticsOutput(
            success=False, error=f"Get domain statistics failed: {exc}"
        )

    return GetDomainStatisticsOutput(success=True, statistics=body)
