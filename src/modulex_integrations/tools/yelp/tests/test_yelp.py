"""Happy-path tests for every yelp @tool, plus a manifest sanity check."""
from __future__ import annotations

import re
from typing import Any

import pytest

from modulex_integrations.tools.yelp import (
    TOOLS,
    get_business_details,
    list_business_reviews,
    manifest,
    search_businesses,
    search_businesses_by_phone_number,
)
from modulex_integrations.tools.yelp.outputs import (
    GetBusinessDetailsOutput,
    ListBusinessReviewsOutput,
    SearchBusinessesByPhoneNumberOutput,
    SearchBusinessesOutput,
)

API = "https://api.yelp.com/v3"

_API_KEY = "fake-yelp-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_search_businesses(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"^{re.escape(API)}/businesses/search\?"),
        json={
            "total": 1,
            "businesses": [
                {
                    "id": "abc123",
                    "alias": "test-biz-sf",
                    "name": "Test Biz",
                    "rating": 4.5,
                    "review_count": 100,
                    "categories": [{"alias": "restaurants", "title": "Restaurants"}],
                    "coordinates": {"latitude": 37.7749, "longitude": -122.4194},
                    "location": {"city": "San Francisco", "state": "CA"},
                    "phone": "+14151234567",
                    "display_phone": "(415) 123-4567",
                }
            ],
        },
    )

    result_dict = await search_businesses.ainvoke(
        _args(location="San Francisco", max_results=50)
    )

    assert isinstance(result_dict, dict)
    result = SearchBusinessesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.businesses) == 1
    assert result.businesses[0].name == "Test Biz"
    assert result.total == 1


@pytest.mark.asyncio
async def test_search_businesses_validates_empty_api_key() -> None:
    result_dict = await search_businesses.ainvoke(
        {"location": "NYC", "api_key": ""}
    )
    result = SearchBusinessesOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")


@pytest.mark.asyncio
async def test_get_business_details(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/businesses/test-biz-sf",
        json={
            # TODO: fill in a representative response shape from the Yelp Fusion API docs
            "id": "abc123",
            "alias": "test-biz-sf",
            "name": "Test Biz",
            "rating": 4.5,
            "review_count": 100,
            "url": "https://www.yelp.com/biz/test-biz-sf",
        },
    )

    result_dict = await get_business_details.ainvoke(
        _args(business_id_or_alias="test-biz-sf")
    )

    assert isinstance(result_dict, dict)
    result = GetBusinessDetailsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.business is not None
    assert result.business["name"] == "Test Biz"


@pytest.mark.asyncio
async def test_list_business_reviews(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/businesses/test-biz-sf/reviews",
        json={
            # TODO: fill in a representative response shape from the Yelp Fusion API docs
            "total": 1,
            "possible_languages": ["en"],
            "reviews": [
                {
                    "id": "rev123",
                    "url": "https://www.yelp.com/biz/test-biz-sf?hrid=rev123",
                    "text": "Great place!",
                    "rating": 5,
                    "time_created": "2024-01-15 12:00:00",
                    "user": {"id": "user1", "name": "John D."},
                }
            ],
        },
    )

    result_dict = await list_business_reviews.ainvoke(
        _args(business_id_or_alias="test-biz-sf")
    )

    assert isinstance(result_dict, dict)
    result = ListBusinessReviewsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.reviews) == 1
    assert result.reviews[0].rating == 5
    assert result.total == 1


@pytest.mark.asyncio
async def test_search_businesses_by_phone_number(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"^{re.escape(API)}/businesses/search/phone\?"),
        json={
            "businesses": [
                {
                    "id": "abc123",
                    "alias": "test-biz-sf",
                    "name": "Test Biz",
                    "phone": "+14151234567",
                }
            ],
        },
    )

    result_dict = await search_businesses_by_phone_number.ainvoke(
        _args(phone="+14151234567")
    )

    assert isinstance(result_dict, dict)
    result = SearchBusinessesByPhoneNumberOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.businesses) == 1
    assert result.businesses[0].phone == "+14151234567"
