"""Yelp LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.yelp.outputs import (
    BusinessSummary,
    GetBusinessDetailsOutput,
    ListBusinessReviewsOutput,
    ReviewSummary,
    SearchBusinessesByPhoneNumberOutput,
    SearchBusinessesOutput,
)

__all__ = [
    "get_business_details",
    "list_business_reviews",
    "search_businesses",
    "search_businesses_by_phone_number",
]

_BASE_URL = "https://api.yelp.com/v3"
_TIMEOUT = 30.0
_PAGE_SIZE = 50


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class SearchBusinessesInput(BaseModel):
    location: str | None = Field(default=None, description="Geographic area to search. Required if latitude and longitude are not provided.")
    latitude: str | None = Field(default=None, description="Latitude of the location to search from.")
    longitude: str | None = Field(default=None, description="Longitude of the location to search from.")
    term: str | None = Field(default=None, description="Search term, e.g. 'food' or 'restaurants'.")
    max_results: int = Field(default=200, description="Maximum number of businesses to return (max 1000).")
    categories: str | None = Field(default=None, description="Comma-separated category aliases to filter results.")
    price: str | None = Field(default=None, description="Comma-separated pricing levels: 1, 2, 3, 4.")
    attributes: str | None = Field(default=None, description="Comma-separated additional filters.")
    api_key: str = Field(description="Yelp Fusion API key")


class GetBusinessDetailsInput(BaseModel):
    business_id_or_alias: str = Field(description="A unique identifier for a Yelp Business (ID or alias).")
    device_platform: str | None = Field(default=None, description="Platform for mobile_link: android, ios, mobile-generic.")
    locale: str | None = Field(default=None, description="Locale code (e.g. en_US).")
    api_key: str = Field(description="Yelp Fusion API key")


class ListBusinessReviewsInput(BaseModel):
    business_id_or_alias: str = Field(description="A unique identifier for a Yelp Business (ID or alias).")
    locale: str | None = Field(default=None, description="Locale code (e.g. en_US).")
    sort_by: str | None = Field(default=None, description="Sort order: yelp_sort or newest.")
    api_key: str = Field(description="Yelp Fusion API key")


class SearchBusinessesByPhoneNumberInput(BaseModel):
    phone: str = Field(description="Phone number starting with + and country code, e.g. +14159083801.")
    locale: str | None = Field(default=None, description="Locale code (e.g. en_US).")
    api_key: str = Field(description="Yelp Fusion API key")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=SearchBusinessesInput)
@serialize_pydantic_return
async def search_businesses(
    api_key: str,
    location: str | None = None,
    latitude: str | None = None,
    longitude: str | None = None,
    term: str | None = None,
    max_results: int = 200,
    categories: str | None = None,
    price: str | None = None,
    attributes: str | None = None,
) -> SearchBusinessesOutput:
    """Search businesses matching given criteria such as location, term, categories, price, and attributes"""
    if not api_key or not api_key.strip():
        return SearchBusinessesOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    if not location and not (latitude and longitude):
        return SearchBusinessesOutput(
            success=False,
            error="Either 'location' or both 'latitude' and 'longitude' must be provided.",
        )

    all_businesses: list[dict[str, Any]] = []
    total = 0
    offset = 0
    limit = min(max_results, _PAGE_SIZE)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while len(all_businesses) < max_results:
                params: dict[str, Any] = {"limit": limit, "offset": offset}
                if location:
                    params["location"] = location
                if latitude:
                    params["latitude"] = latitude
                if longitude:
                    params["longitude"] = longitude
                if term:
                    params["term"] = term
                if categories:
                    params["categories"] = categories
                if price:
                    params["price"] = price
                if attributes:
                    params["attributes"] = attributes

                response = await client.get(
                    f"{_BASE_URL}/businesses/search",
                    headers=_headers(api_key),
                    params=params,
                )
                if response.status_code != 200:
                    return SearchBusinessesOutput(
                        success=False,
                        error=f"API error ({response.status_code}): {response.text}",
                    )
                data = response.json()
                total = data.get("total", 0)
                businesses = data.get("businesses", [])
                if not businesses:
                    break
                all_businesses.extend(businesses)
                offset += len(businesses)
                if offset >= total or len(businesses) < limit:
                    break
    except httpx.TimeoutException:
        return SearchBusinessesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchBusinessesOutput(success=False, error=f"Call failed: {exc}")

    trimmed = all_businesses[:max_results]
    return SearchBusinessesOutput(
        success=True,
        businesses=[
            BusinessSummary(
                id=b.get("id"),
                alias=b.get("alias"),
                name=b.get("name"),
                image_url=b.get("image_url"),
                url=b.get("url"),
                review_count=b.get("review_count"),
                categories=b.get("categories", []),
                rating=b.get("rating"),
                coordinates=b.get("coordinates"),
                location=b.get("location"),
                phone=b.get("phone"),
                display_phone=b.get("display_phone"),
                distance=b.get("distance"),
            )
            for b in trimmed
        ],
        total=total,
    )


@tool(args_schema=GetBusinessDetailsInput)
@serialize_pydantic_return
async def get_business_details(
    business_id_or_alias: str,
    api_key: str,
    device_platform: str | None = None,
    locale: str | None = None,
) -> GetBusinessDetailsOutput:
    """Get detailed information about a specific business by its Yelp ID or alias"""
    if not api_key or not api_key.strip():
        return GetBusinessDetailsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    params: dict[str, str] = {}
    if device_platform:
        params["device_platform"] = device_platform
    if locale:
        params["locale"] = locale

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/businesses/{business_id_or_alias}",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return GetBusinessDetailsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetBusinessDetailsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetBusinessDetailsOutput(success=False, error=f"Call failed: {exc}")

    return GetBusinessDetailsOutput(success=True, business=data)


@tool(args_schema=ListBusinessReviewsInput)
@serialize_pydantic_return
async def list_business_reviews(
    business_id_or_alias: str,
    api_key: str,
    locale: str | None = None,
    sort_by: str | None = None,
) -> ListBusinessReviewsOutput:
    """List the reviews for a specific business"""
    if not api_key or not api_key.strip():
        return ListBusinessReviewsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    params: dict[str, str] = {}
    if locale:
        params["locale"] = locale
    if sort_by:
        params["sort_by"] = sort_by

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/businesses/{business_id_or_alias}/reviews",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListBusinessReviewsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListBusinessReviewsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListBusinessReviewsOutput(success=False, error=f"Call failed: {exc}")

    reviews_raw = data.get("reviews", [])
    return ListBusinessReviewsOutput(
        success=True,
        reviews=[
            ReviewSummary(
                id=r.get("id"),
                url=r.get("url"),
                text=r.get("text"),
                rating=r.get("rating"),
                time_created=r.get("time_created"),
                user=r.get("user"),
            )
            for r in reviews_raw
        ],
        total=data.get("total", 0),
        possible_languages=data.get("possible_languages", []),
    )


@tool(args_schema=SearchBusinessesByPhoneNumberInput)
@serialize_pydantic_return
async def search_businesses_by_phone_number(
    phone: str,
    api_key: str,
    locale: str | None = None,
) -> SearchBusinessesByPhoneNumberOutput:
    """Search for businesses by phone number"""
    if not api_key or not api_key.strip():
        return SearchBusinessesByPhoneNumberOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    params: dict[str, str] = {"phone": phone}
    if locale:
        params["locale"] = locale

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/businesses/search/phone",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return SearchBusinessesByPhoneNumberOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchBusinessesByPhoneNumberOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchBusinessesByPhoneNumberOutput(success=False, error=f"Call failed: {exc}")

    businesses_raw = data.get("businesses", [])
    return SearchBusinessesByPhoneNumberOutput(
        success=True,
        businesses=[
            BusinessSummary(
                id=b.get("id"),
                alias=b.get("alias"),
                name=b.get("name"),
                image_url=b.get("image_url"),
                url=b.get("url"),
                review_count=b.get("review_count"),
                categories=b.get("categories", []),
                rating=b.get("rating"),
                coordinates=b.get("coordinates"),
                location=b.get("location"),
                phone=b.get("phone"),
                display_phone=b.get("display_phone"),
                distance=b.get("distance"),
            )
            for b in businesses_raw
        ],
    )
