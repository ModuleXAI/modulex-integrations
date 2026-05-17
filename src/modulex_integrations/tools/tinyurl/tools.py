"""TinyURL LangChain ``@tool`` functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.tinyurl.outputs import (
    CreateShortenedLinkOutput,
    RetrieveLinkAnalyticsOutput,
    UpdateLinkMetadataOutput,
)

__all__ = [
    "create_shortened_link",
    "retrieve_link_analytics",
    "update_link_metadata",
]

_BASE_URL = "https://api.tinyurl.com"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _filter_none(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def _extract_error(response: httpx.Response) -> str:
    """Pull a useful error message out of TinyURL's variable error envelope."""
    try:
        body = response.json()
        if isinstance(body, dict):
            errors = body.get("errors")
            if isinstance(errors, list) and errors:
                return str(errors[0])
            msg = body.get("message")
            if msg:
                return str(msg)
    except Exception:
        pass
    return response.text


class CreateShortenedLinkInput(BaseModel):
    api_key: str = Field(description="TinyURL API token (provided by credential system)")
    url: str = Field(description="The long URL that will be shortened")
    domain: str = Field(default="tinyurl.com", description="Domain for the TinyURL")
    alias: str | None = Field(default=None, description="Custom alias (auto if absent)")
    tags: list[str] | None = Field(default=None, description="Tags (paid only)")
    expires_at: str | None = Field(default=None, description="ISO8601 datetime. Paid only")
    description: str | None = Field(default=None, description="Description for the alias")


class RetrieveLinkAnalyticsInput(BaseModel):
    api_key: str = Field(description="TinyURL API token (provided by credential system)")
    domain: str = Field(default="tinyurl.com", description="Domain of the TinyURL")
    alias: str = Field(description="Alias of the TinyURL")
    from_date: str = Field(description="Start ISO8601 datetime")
    to_date: str | None = Field(default=None, description="End datetime (defaults to now)")
    tag: str | None = Field(default=None, description="Tag filter")


class UpdateLinkMetadataInput(BaseModel):
    api_key: str = Field(description="TinyURL API token (provided by credential system)")
    domain: str = Field(description="Current domain of the TinyURL")
    alias: str = Field(description="Current alias of the TinyURL")
    new_domain: str | None = Field(default=None, description="New domain")
    new_alias: str | None = Field(default=None, description="New alias")
    new_stats: bool | None = Field(default=None, description="Toggle analytics collection")
    new_tags: list[str] | None = Field(default=None, description="New tags (overwrite). Paid only")
    new_expires_at: str | None = Field(
        default=None, description="New expiration ISO8601. Paid only"
    )
    new_description: str | None = Field(default=None, description="New description")


@tool(args_schema=CreateShortenedLinkInput)
@serialize_pydantic_return
async def create_shortened_link(
    api_key: str,
    url: str,
    domain: str = "tinyurl.com",
    alias: str | None = None,
    tags: list[str] | None = None,
    expires_at: str | None = None,
    description: str | None = None,
) -> CreateShortenedLinkOutput:
    """Create a new shortened URL using TinyURL."""
    if not api_key or not api_key.strip():
        return CreateShortenedLinkOutput(
            success=False,
            error="TinyURL API token is empty. Please configure a valid credential.",
        )

    payload = _filter_none(
        {
            "url": url,
            "domain": domain,
            "alias": alias,
            "tags": ",".join(tags) if tags else None,
            "expires_at": expires_at,
            "description": description,
        }
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/create", headers=_headers(api_key), json=payload
            )
        if response.status_code not in (200, 201):
            return CreateShortenedLinkOutput(
                success=False,
                error=f"API error ({response.status_code}): {_extract_error(response)}",
            )
        data = (response.json() or {}).get("data") or {}
    except Exception as exc:
        return CreateShortenedLinkOutput(
            success=False, error=f"Create shortened link failed: {exc}"
        )

    return CreateShortenedLinkOutput(
        success=True,
        tiny_url=data.get("tiny_url"),
        url=data.get("url"),
        domain=data.get("domain"),
        alias=data.get("alias"),
        created_at=data.get("created_at"),
    )


@tool(args_schema=RetrieveLinkAnalyticsInput)
@serialize_pydantic_return
async def retrieve_link_analytics(
    api_key: str,
    domain: str,
    alias: str,
    from_date: str,
    to_date: str | None = None,
    tag: str | None = None,
) -> RetrieveLinkAnalyticsOutput:
    """Retrieve analytics for a specific TinyURL link (paid accounts only)."""
    if not api_key or not api_key.strip():
        return RetrieveLinkAnalyticsOutput(
            success=False,
            error="TinyURL API token is empty. Please configure a valid credential.",
        )

    params = _filter_none({"from": from_date, "to": to_date, "alias": alias, "tag": tag})

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/analytics", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return RetrieveLinkAnalyticsOutput(
                success=False,
                error=(
                    f"API error ({response.status_code}): {_extract_error(response)}. "
                    "Note: Analytics is only available for paid accounts."
                ),
            )
        body = response.json() or {}
    except Exception as exc:
        return RetrieveLinkAnalyticsOutput(
            success=False, error=f"Retrieve link analytics failed: {exc}"
        )

    # TinyURL's analytics shape varies; we extract documented fields and
    # leave the unstructured per-country/device/referrer rows as raw dicts.
    return RetrieveLinkAnalyticsOutput(
        success=True,
        total_clicks=body.get("total_clicks"),
        date_range=body.get("date_range"),
        clicks_by_country=body.get("clicks_by_country") or [],
        clicks_by_device=body.get("clicks_by_device") or [],
        clicks_by_referrer=body.get("clicks_by_referrer") or [],
    )


@tool(args_schema=UpdateLinkMetadataInput)
@serialize_pydantic_return
async def update_link_metadata(
    api_key: str,
    domain: str,
    alias: str,
    new_domain: str | None = None,
    new_alias: str | None = None,
    new_stats: bool | None = None,
    new_tags: list[str] | None = None,
    new_expires_at: str | None = None,
    new_description: str | None = None,
) -> UpdateLinkMetadataOutput:
    """Update the metadata of an existing TinyURL."""
    if not api_key or not api_key.strip():
        return UpdateLinkMetadataOutput(
            success=False,
            error="TinyURL API token is empty. Please configure a valid credential.",
        )

    payload = _filter_none(
        {
            "domain": domain,
            "alias": alias,
            "new_domain": new_domain,
            "new_alias": new_alias,
            "new_stats": new_stats,
            "new_tags": new_tags,
            "new_expires_at": new_expires_at,
            "new_description": new_description,
        }
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/update", headers=_headers(api_key), json=payload
            )
        if response.status_code != 200:
            return UpdateLinkMetadataOutput(
                success=False,
                error=f"API error ({response.status_code}): {_extract_error(response)}",
            )
        data = (response.json() or {}).get("data") or {}
    except Exception as exc:
        return UpdateLinkMetadataOutput(
            success=False, error=f"Update link metadata failed: {exc}"
        )

    return UpdateLinkMetadataOutput(
        success=True,
        tiny_url=data.get("tiny_url"),
        url=data.get("url"),
        domain=data.get("domain"),
        alias=data.get("alias"),
        updated_at=data.get("updated_at"),
        analytics_enabled=data.get("analytics_enabled"),
    )
