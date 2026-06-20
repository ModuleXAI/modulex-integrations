"""Brandfetch LangChain ``@tool`` functions.

Two async tools wrapping the Brandfetch REST API. The calling
convention is *key-based*: the modulex ``ToolExecutor`` injects an
``api_key: str`` directly (resolved from the user's credential), not an
``auth_type``/``auth_data`` pair.

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions. Non-2xx HTTP responses do *not*
raise.
"""
from __future__ import annotations

from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.brandfetch.outputs import (
    BrandColor,
    BrandFont,
    BrandLink,
    BrandLogo,
    BrandLogoFormat,
    GetBrandOutput,
    SearchOutput,
    SearchResultItem,
)

__all__ = ["get_brand", "search"]

_BRANDFETCH_API_BASE = "https://api.brandfetch.io/v2"
_REQUEST_TIMEOUT = 30.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }


# --- Input schemas (args_schema for each @tool) ----------------------------


class GetBrandInput(BaseModel):
    identifier: str = Field(
        description=(
            "Brand identifier: domain (nike.com), stock ticker (NKE), "
            "ISIN (US6541061031), or crypto symbol (BTC)"
        )
    )
    api_key: str = Field(description="Brandfetch API key (provided by credential system)")


class SearchInput(BaseModel):
    name: str = Field(description="Company or brand name to search for")
    api_key: str = Field(description="Brandfetch API key (provided by credential system)")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=GetBrandInput)
@serialize_pydantic_return
async def get_brand(identifier: str, api_key: str) -> GetBrandOutput:
    """Retrieve brand assets including logos, colors, fonts, and company info by
    domain, ticker, ISIN, or crypto symbol."""
    if not api_key or not api_key.strip():
        return GetBrandOutput(
            success=False,
            error="Brandfetch API key is empty. Please configure a valid Brandfetch credential.",
        )
    if not identifier or not identifier.strip():
        return GetBrandOutput(success=False, error="An identifier is required.")

    url = f"{_BRANDFETCH_API_BASE}/brands/{quote(identifier.strip(), safe='')}"

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers=_headers(api_key))
        if response.status_code != 200:
            return GetBrandOutput(
                success=False,
                error=f"Brandfetch API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetBrandOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetBrandOutput(success=False, error=f"Get brand failed: {exc}")

    return GetBrandOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        domain=data.get("domain"),
        claimed=data.get("claimed"),
        description=data.get("description"),
        long_description=data.get("longDescription"),
        links=[
            BrandLink(name=link.get("name"), url=link.get("url"))
            for link in data.get("links") or []
        ],
        logos=[
            BrandLogo(
                type=logo.get("type"),
                theme=logo.get("theme"),
                formats=[
                    BrandLogoFormat(
                        src=fmt.get("src"),
                        format=fmt.get("format"),
                        width=fmt.get("width"),
                        height=fmt.get("height"),
                        background=fmt.get("background"),
                        size=fmt.get("size"),
                    )
                    for fmt in logo.get("formats") or []
                ],
            )
            for logo in data.get("logos") or []
        ],
        colors=[
            BrandColor(
                hex=color.get("hex"),
                type=color.get("type"),
                brightness=color.get("brightness"),
            )
            for color in data.get("colors") or []
        ],
        fonts=[
            BrandFont(
                name=font.get("name"),
                type=font.get("type"),
                origin=font.get("origin"),
                origin_id=font.get("originId"),
                weights=font.get("weights") or [],
            )
            for font in data.get("fonts") or []
        ],
        company=data.get("company"),
        quality_score=data.get("qualityScore"),
        is_nsfw=data.get("isNsfw"),
    )


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(name: str, api_key: str) -> SearchOutput:
    """Search for brands by name and find their domains and logos."""
    if not api_key or not api_key.strip():
        return SearchOutput(
            success=False,
            error="Brandfetch API key is empty. Please configure a valid Brandfetch credential.",
        )
    if not name or not name.strip():
        return SearchOutput(success=False, error="A brand name is required.")

    # NOTE: The Brand Search API is documented to authenticate via a public
    # client-id query parameter (``?c={clientId}``). Brandfetch also accepts
    # the same Bearer API key used by the Brand API on this endpoint, which is
    # the auth path used here (one credential, key-based runtime convention).
    # TODO (unverified): whether ``/v2/search`` accepts ``Authorization: Bearer``
    #   indefinitely vs. requiring the ``?c={clientId}`` query param per
    #   https://docs.brandfetch.com/llms-full.txt — the Bearer path mirrors the
    #   upstream source and keeps a single injected credential.
    url = f"{_BRANDFETCH_API_BASE}/search/{quote(name.strip(), safe='')}"

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers=_headers(api_key))
        if response.status_code != 200:
            return SearchOutput(
                success=False,
                error=f"Brandfetch API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchOutput(success=False, error=f"Search failed: {exc}")

    results = data if isinstance(data, list) else []

    return SearchOutput(
        success=True,
        results=[
            SearchResultItem(
                brand_id=item.get("brandId"),
                name=item.get("name"),
                domain=item.get("domain"),
                claimed=item.get("claimed"),
                icon=item.get("icon"),
            )
            for item in results
        ],
        total_results=len(results),
    )
