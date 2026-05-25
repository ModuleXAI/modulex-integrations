"""Google Maps Platform LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_maps_platform.outputs import (
    GetPlaceDetailsOutput,
    SearchPlacesOutput,
)

__all__ = [
    "get_place_details",
    "search_places",
]

_BASE_URL = "https://places.googleapis.com/v1/places"

_TIMEOUT = 30.0

_SIMPLIFIED_FIELDS = [
    "places.id",
    "places.displayName",
    "places.primaryType",
    "places.businessStatus",
    "places.rating",
    "places.userRatingCount",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.currentOpeningHours",
    "places.location",
    "places.addressDescriptor",
]

_DETAIL_SIMPLIFIED_FIELDS = [
    "id",
    "displayName",
    "primaryType",
    "businessStatus",
    "rating",
    "userRatingCount",
    "formattedAddress",
    "nationalPhoneNumber",
    "websiteUri",
    "currentOpeningHours",
    "location",
    "addressDescriptor",
]

_FULL_FIELDS = [
    "places.id",
    "places.displayName",
    "places.types",
    "places.primaryType",
    "places.businessStatus",
    "places.formattedAddress",
    "places.addressComponents",
    "places.location",
    "places.rating",
    "places.userRatingCount",
    "places.nationalPhoneNumber",
    "places.internationalPhoneNumber",
    "places.websiteUri",
    "places.googleMapsUri",
    "places.currentOpeningHours",
    "places.priceLevel",
    "places.editorialSummary",
    "places.reviews",
    "places.photos",
    "places.accessibilityOptions",
    "places.parkingOptions",
    "places.paymentOptions",
    "places.addressDescriptor",
]

_DETAIL_FULL_FIELDS = [
    "id",
    "displayName",
    "types",
    "primaryType",
    "businessStatus",
    "formattedAddress",
    "addressComponents",
    "location",
    "rating",
    "userRatingCount",
    "nationalPhoneNumber",
    "internationalPhoneNumber",
    "websiteUri",
    "googleMapsUri",
    "currentOpeningHours",
    "priceLevel",
    "editorialSummary",
    "reviews",
    "photos",
    "accessibilityOptions",
    "parkingOptions",
    "paymentOptions",
    "addressDescriptor",
]


def _headers(api_key: str) -> dict[str, str]:
    return {
        "X-Goog-Api-Key": api_key,
        "Content-Type": "application/json",
    }


# --- Input schemas ------------------------------------------------------------


class SearchPlacesInput(BaseModel):
    text_query: str = Field(description="The text string on which to search")
    api_key: str = Field(description="Google Maps API key (provided by credential system)")
    included_type: str | None = Field(default=None, description="Restrict results to places matching this type")
    include_pure_service_area_businesses: bool | None = Field(default=None, description="If true, include businesses without a physical location")
    language_code: str | None = Field(default=None, description="BCP-47 language code for results")
    location_bias: dict[str, Any] | None = Field(default=None, description="Area to bias search results toward")
    location_restriction: str | None = Field(default=None, description="Area to restrict search results to")
    ev_options: dict[str, Any] | None = Field(default=None, description="EV charging connector and rate parameters")
    min_rating: float | None = Field(default=None, description="Minimum average user rating (0.0 to 5.0)")
    open_now: bool | None = Field(default=None, description="If true, return only currently open places")
    price_levels: list[str] | None = Field(default=None, description="Restrict to places at certain price levels")
    rank_preference: str | None = Field(default=None, description="Rank by RELEVANCE or DISTANCE")
    region_code: str | None = Field(default=None, description="Two-character CLDR region code")
    strict_type_filtering: bool | None = Field(default=None, description="Only return places matching included_type")
    simplified: bool | None = Field(default=None, description="If true, return a reduced set of fields")


class GetPlaceDetailsInput(BaseModel):
    place_id: str = Field(description="Textual identifier that uniquely identifies a place")
    api_key: str = Field(description="Google Maps API key (provided by credential system)")
    simplified: bool | None = Field(default=None, description="If true, return a reduced set of fields")


# --- @tool functions ----------------------------------------------------------


@tool(args_schema=SearchPlacesInput)
@serialize_pydantic_return
async def search_places(
    text_query: str,
    api_key: str,
    included_type: str | None = None,
    include_pure_service_area_businesses: bool | None = None,
    language_code: str | None = None,
    location_bias: dict[str, Any] | None = None,
    location_restriction: str | None = None,
    ev_options: dict[str, Any] | None = None,
    min_rating: float | None = None,
    open_now: bool | None = None,
    price_levels: list[str] | None = None,
    rank_preference: str | None = None,
    region_code: str | None = None,
    strict_type_filtering: bool | None = None,
    simplified: bool | None = None,
) -> SearchPlacesOutput:
    """Search for places based on a text query with optional filters like type, rating, price level, and location bias or restriction"""
    if not api_key or not api_key.strip():
        return SearchPlacesOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    field_mask = ",".join(_SIMPLIFIED_FIELDS if simplified else _FULL_FIELDS)
    headers = _headers(api_key)
    headers["X-Goog-FieldMask"] = field_mask

    body: dict[str, Any] = {"textQuery": text_query}
    if included_type is not None:
        body["includedType"] = included_type
    if include_pure_service_area_businesses is not None:
        body["includePureServiceAreaBusinesses"] = include_pure_service_area_businesses
    if language_code is not None:
        body["languageCode"] = language_code
    if location_bias is not None:
        body["locationBias"] = location_bias
    if location_restriction is not None:
        body["locationRestriction"] = location_restriction
    if ev_options is not None:
        body["evOptions"] = ev_options
    if min_rating is not None:
        body["minRating"] = min_rating
    if open_now is not None:
        body["openNow"] = open_now
    if price_levels is not None:
        body["priceLevels"] = price_levels
    if rank_preference is not None:
        body["rankPreference"] = rank_preference
    if region_code is not None:
        body["regionCode"] = region_code
    if strict_type_filtering is not None:
        body["strictTypeFiltering"] = strict_type_filtering

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}:searchText",
                headers=headers,
                json=body,
            )
        if response.status_code != 200:
            return SearchPlacesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchPlacesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchPlacesOutput(success=False, error=f"Call failed: {exc}")

    return SearchPlacesOutput(
        success=True,
        places=data.get("places", []),
    )


@tool(args_schema=GetPlaceDetailsInput)
@serialize_pydantic_return
async def get_place_details(
    place_id: str,
    api_key: str,
    simplified: bool | None = None,
) -> GetPlaceDetailsOutput:
    """Retrieve detailed information for a specific place using its Place ID"""
    if not api_key or not api_key.strip():
        return GetPlaceDetailsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    field_mask = ",".join(_DETAIL_SIMPLIFIED_FIELDS if simplified else _DETAIL_FULL_FIELDS)
    headers = _headers(api_key)
    headers["X-Goog-FieldMask"] = field_mask

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/{place_id}",
                headers=headers,
            )
        if response.status_code != 200:
            return GetPlaceDetailsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetPlaceDetailsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetPlaceDetailsOutput(success=False, error=f"Call failed: {exc}")

    return GetPlaceDetailsOutput(
        success=True,
        data=data,
    )
