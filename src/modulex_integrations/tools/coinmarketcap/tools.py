"""CoinMarketCap LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.coinmarketcap.outputs import (
    CryptocurrencyMapItem,
    CryptocurrencyMetadata,
    CryptocurrencyQuote,
    GetCryptocurrencyMetadataOutput,
    IdMapOutput,
    LatestListingsOutput,
    LatestQuotesOutput,
    ListingItem,
    QuoteData,
)

__all__ = [
    "get_cryptocurrency_metadata",
    "id_map",
    "latest_listings",
    "latest_quotes",
]

_BASE_URL = "https://pro-api.coinmarketcap.com"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "X-CMC_PRO_API_KEY": api_key,
        "Accept": "application/json",
    }


def _parse_quote(raw: dict[str, Any]) -> dict[str, QuoteData]:
    result: dict[str, QuoteData] = {}
    for currency, qdata in (raw or {}).items():
        if isinstance(qdata, dict):
            result[currency] = QuoteData(
                price=qdata.get("price"),
                volume_24h=qdata.get("volume_24h"),
                market_cap=qdata.get("market_cap"),
                percent_change_1h=qdata.get("percent_change_1h"),
                percent_change_24h=qdata.get("percent_change_24h"),
                percent_change_7d=qdata.get("percent_change_7d"),
                last_updated=qdata.get("last_updated"),
            )
    return result


# --- Input schemas --------------------------------------------------------


class GetCryptocurrencyMetadataInput(BaseModel):
    ids: str = Field(description="One or more comma-separated CoinMarketCap cryptocurrency IDs")
    api_key: str = Field(description="CoinMarketCap API key")
    skip_invalid: bool = Field(default=False, description="When true, invalid lookups will be skipped")
    aux: str | None = Field(default=None, description="Comma-separated supplemental data fields to return")


class IdMapInput(BaseModel):
    api_key: str = Field(description="CoinMarketCap API key")
    listing_status: str | None = Field(default=None, description="Filter by status: active, inactive, untracked")
    start: int | None = Field(default=None, description="Offset the start (1-based index)")
    limit: int = Field(default=100, description="Number of results to return")
    sort: str | None = Field(default=None, description="Sort field: cmc_rank or id")
    symbol: str | None = Field(default=None, description="Comma-separated cryptocurrency symbols")
    aux: str | None = Field(default=None, description="Comma-separated supplemental data fields")


class LatestListingsInput(BaseModel):
    api_key: str = Field(description="CoinMarketCap API key")
    start: int | None = Field(default=None, description="Offset the start (1-based index)")
    limit: int | None = Field(default=None, description="Number of results to return")
    volume_24h_min: float | None = Field(default=None, description="Minimum 24 hour USD volume filter")
    convert: str | None = Field(default=None, description="Comma-separated currency symbols for quotes")
    convert_id: str | None = Field(default=None, description="Comma-separated CoinMarketCap IDs for quotes")
    sort: str | None = Field(default=None, description="Sort field")
    sort_dir: str | None = Field(default=None, description="Sort direction: asc or desc")
    cryptocurrency_type: str | None = Field(default=None, description="Type filter: all, coins, tokens")
    aux: str | None = Field(default=None, description="Comma-separated supplemental data fields")


class LatestQuotesInput(BaseModel):
    api_key: str = Field(description="CoinMarketCap API key")
    id: str | None = Field(default=None, description="Comma-separated CoinMarketCap cryptocurrency IDs")
    slug: str | None = Field(default=None, description="Comma-separated cryptocurrency slugs")
    symbol: str | None = Field(default=None, description="Comma-separated cryptocurrency symbols")
    convert: str | None = Field(default=None, description="Comma-separated currency symbols for quotes")
    convert_id: str | None = Field(default=None, description="Comma-separated CoinMarketCap IDs for quotes")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=GetCryptocurrencyMetadataInput)
@serialize_pydantic_return
async def get_cryptocurrency_metadata(
    ids: str,
    api_key: str,
    skip_invalid: bool = False,
    aux: str | None = None,
) -> GetCryptocurrencyMetadataOutput:
    """Returns all static metadata available for one or more cryptocurrencies including name, symbol, logo, description, and URLs"""
    if not api_key or not api_key.strip():
        return GetCryptocurrencyMetadataOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    params: dict[str, Any] = {"id": ids, "skip_invalid": str(skip_invalid).lower()}
    if aux:
        params["aux"] = aux
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v2/cryptocurrency/info",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return GetCryptocurrencyMetadataOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        body = response.json()
    except httpx.TimeoutException:
        return GetCryptocurrencyMetadataOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCryptocurrencyMetadataOutput(success=False, error=f"Call failed: {exc}")

    raw_data = body.get("data", {})
    data: dict[str, CryptocurrencyMetadata] = {}
    for key, item in raw_data.items():
        if isinstance(item, dict):
            data[key] = CryptocurrencyMetadata(
                id=item.get("id"),
                name=item.get("name"),
                symbol=item.get("symbol"),
                slug=item.get("slug"),
                description=item.get("description"),
                logo=item.get("logo"),
                date_added=item.get("date_added"),
                category=item.get("category"),
            )
    return GetCryptocurrencyMetadataOutput(success=True, data=data)


@tool(args_schema=IdMapInput)
@serialize_pydantic_return
async def id_map(
    api_key: str,
    listing_status: str | None = None,
    start: int | None = None,
    limit: int = 100,
    sort: str | None = None,
    symbol: str | None = None,
    aux: str | None = None,
) -> IdMapOutput:
    """Returns a mapping of all cryptocurrencies to unique CoinMarketCap IDs"""
    if not api_key or not api_key.strip():
        return IdMapOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    params: dict[str, Any] = {"limit": limit}
    if listing_status:
        params["listing_status"] = listing_status
    if start is not None:
        params["start"] = start
    if sort:
        params["sort"] = sort
    if symbol:
        params["symbol"] = symbol
    if aux:
        params["aux"] = aux
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v1/cryptocurrency/map",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return IdMapOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        body = response.json()
    except httpx.TimeoutException:
        return IdMapOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return IdMapOutput(success=False, error=f"Call failed: {exc}")

    raw_data = body.get("data", [])
    data = [
        CryptocurrencyMapItem(
            id=item.get("id"),
            name=item.get("name"),
            symbol=item.get("symbol"),
            slug=item.get("slug"),
            is_active=item.get("is_active"),
            first_historical_data=item.get("first_historical_data"),
            last_historical_data=item.get("last_historical_data"),
        )
        for item in raw_data
        if isinstance(item, dict)
    ]
    return IdMapOutput(success=True, data=data)


@tool(args_schema=LatestListingsInput)
@serialize_pydantic_return
async def latest_listings(
    api_key: str,
    start: int | None = None,
    limit: int | None = None,
    volume_24h_min: float | None = None,
    convert: str | None = None,
    convert_id: str | None = None,
    sort: str | None = None,
    sort_dir: str | None = None,
    cryptocurrency_type: str | None = None,
    aux: str | None = None,
) -> LatestListingsOutput:
    """Returns a paginated list of all active cryptocurrencies with latest market data"""
    if not api_key or not api_key.strip():
        return LatestListingsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    params: dict[str, Any] = {}
    if start is not None:
        params["start"] = start
    if limit is not None:
        params["limit"] = limit
    if volume_24h_min is not None:
        params["volume_24h_min"] = volume_24h_min
    if convert:
        params["convert"] = convert
    if convert_id:
        params["convert_id"] = convert_id
    if sort:
        params["sort"] = sort
    if sort_dir:
        params["sort_dir"] = sort_dir
    if cryptocurrency_type:
        params["cryptocurrency_type"] = cryptocurrency_type
    if aux:
        params["aux"] = aux
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v1/cryptocurrency/listings/latest",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return LatestListingsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        body = response.json()
    except httpx.TimeoutException:
        return LatestListingsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return LatestListingsOutput(success=False, error=f"Call failed: {exc}")

    raw_data = body.get("data", [])
    data = [
        ListingItem(
            id=item.get("id"),
            name=item.get("name"),
            symbol=item.get("symbol"),
            slug=item.get("slug"),
            cmc_rank=item.get("cmc_rank"),
            circulating_supply=item.get("circulating_supply"),
            total_supply=item.get("total_supply"),
            max_supply=item.get("max_supply"),
            quote=_parse_quote(item.get("quote", {})),
        )
        for item in raw_data
        if isinstance(item, dict)
    ]
    return LatestListingsOutput(success=True, data=data)


@tool(args_schema=LatestQuotesInput)
@serialize_pydantic_return
async def latest_quotes(
    api_key: str,
    id: str | None = None,
    slug: str | None = None,
    symbol: str | None = None,
    convert: str | None = None,
    convert_id: str | None = None,
) -> LatestQuotesOutput:
    """Returns the latest market quote for one or more cryptocurrencies. At least one of id, slug, or symbol is required."""
    if not api_key or not api_key.strip():
        return LatestQuotesOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    params: dict[str, Any] = {}
    if id:
        params["id"] = id
    if slug:
        params["slug"] = slug
    if symbol:
        params["symbol"] = symbol
    if convert:
        params["convert"] = convert
    if convert_id:
        params["convert_id"] = convert_id
    if not params:
        return LatestQuotesOutput(
            success=False,
            error="At least one of id, slug, or symbol is required.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v1/cryptocurrency/quotes/latest",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return LatestQuotesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        body = response.json()
    except httpx.TimeoutException:
        return LatestQuotesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return LatestQuotesOutput(success=False, error=f"Call failed: {exc}")

    raw_data = body.get("data", {})
    data: dict[str, CryptocurrencyQuote] = {}
    for key, item in raw_data.items():
        if isinstance(item, dict):
            data[key] = CryptocurrencyQuote(
                id=item.get("id"),
                name=item.get("name"),
                symbol=item.get("symbol"),
                slug=item.get("slug"),
                cmc_rank=item.get("cmc_rank"),
                quote=_parse_quote(item.get("quote", {})),
            )
    return LatestQuotesOutput(success=True, data=data)
