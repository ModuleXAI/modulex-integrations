"""Happy-path tests for every google_maps_platform @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_maps_platform import (
    TOOLS,
    get_place_details,
    manifest,
    search_places,
)
from modulex_integrations.tools.google_maps_platform.outputs import (
    GetPlaceDetailsOutput,
    SearchPlacesOutput,
)

API = "https://places.googleapis.com/v1/places"

_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity ----------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_2_actions(self) -> None:
        assert len(manifest.actions) == 2

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests ----------------------------------------------


@pytest.mark.asyncio
async def test_search_places(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}:searchText",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "places": [
                {
                    "id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                    "displayName": {"text": "Sydney Opera House"},
                    "formattedAddress": "Bennelong Point, Sydney NSW 2000",
                }
            ]
        },
    )

    result_dict = await search_places.ainvoke(_args(text_query="Sydney Opera House"))

    assert isinstance(result_dict, dict)
    result = SearchPlacesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.places) == 1
    assert result.places[0]["id"] == "ChIJN1t_tDeuEmsRUsoyG83frY4"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["X-Goog-Api-Key"] == _API_KEY


@pytest.mark.asyncio
async def test_get_place_details(httpx_mock):  # type: ignore[no-untyped-def]
    place_id = "ChIJN1t_tDeuEmsRUsoyG83frY4"
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/{place_id}",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": place_id,
            "displayName": {"text": "Sydney Opera House"},
            "rating": 4.6,
            "formattedAddress": "Bennelong Point, Sydney NSW 2000",
        },
    )

    result_dict = await get_place_details.ainvoke(_args(place_id=place_id))

    assert isinstance(result_dict, dict)
    result = GetPlaceDetailsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None
    assert result.data["id"] == place_id

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["X-Goog-Api-Key"] == _API_KEY


@pytest.mark.asyncio
async def test_search_places_validates_empty_api_key() -> None:
    result_dict = await search_places.ainvoke({"text_query": "test", "api_key": ""})
    result = SearchPlacesOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")


@pytest.mark.asyncio
async def test_get_place_details_validates_empty_api_key() -> None:
    result_dict = await get_place_details.ainvoke({"place_id": "test", "api_key": ""})
    result = GetPlaceDetailsOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")
