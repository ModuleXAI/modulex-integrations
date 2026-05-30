"""Happy-path tests for every coinmarketcap @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.coinmarketcap import (
    TOOLS,
    get_cryptocurrency_metadata,
    id_map,
    latest_listings,
    latest_quotes,
    manifest,
)
from modulex_integrations.tools.coinmarketcap.outputs import (
    GetCryptocurrencyMetadataOutput,
    IdMapOutput,
    LatestListingsOutput,
    LatestQuotesOutput,
)

API = "https://pro-api.coinmarketcap.com"

_API_KEY = "fake-api-key"


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
async def test_get_cryptocurrency_metadata(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/cryptocurrency/info?id=1&skip_invalid=false",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "data": {
                "1": {
                    "id": 1,
                    "name": "Bitcoin",
                    "symbol": "BTC",
                    "slug": "bitcoin",
                    "description": "Bitcoin is a cryptocurrency.",
                    "logo": "https://s2.coinmarketcap.com/static/img/coins/64x64/1.png",
                    "date_added": "2013-04-28T00:00:00.000Z",
                    "category": "coin",
                }
            }
        },
    )

    result_dict = await get_cryptocurrency_metadata.ainvoke(_args(ids="1"))

    assert isinstance(result_dict, dict)
    result = GetCryptocurrencyMetadataOutput.model_validate(result_dict)
    assert result.success is True
    assert "1" in result.data
    assert result.data["1"].name == "Bitcoin"


@pytest.mark.asyncio
async def test_id_map(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/cryptocurrency/map?limit=100",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "data": [
                {
                    "id": 1,
                    "name": "Bitcoin",
                    "symbol": "BTC",
                    "slug": "bitcoin",
                    "is_active": 1,
                    "first_historical_data": "2013-04-28T18:47:21.000Z",
                    "last_historical_data": "2024-01-01T00:00:00.000Z",
                }
            ]
        },
    )

    result_dict = await id_map.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = IdMapOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.data) == 1
    assert result.data[0].symbol == "BTC"


@pytest.mark.asyncio
async def test_latest_listings(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/cryptocurrency/listings/latest",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "data": [
                {
                    "id": 1,
                    "name": "Bitcoin",
                    "symbol": "BTC",
                    "slug": "bitcoin",
                    "cmc_rank": 1,
                    "circulating_supply": 19500000.0,
                    "total_supply": 19500000.0,
                    "max_supply": 21000000.0,
                    "quote": {
                        "USD": {
                            "price": 50000.0,
                            "volume_24h": 30000000000.0,
                            "market_cap": 975000000000.0,
                            "percent_change_1h": 0.5,
                            "percent_change_24h": 2.1,
                            "percent_change_7d": -1.3,
                            "last_updated": "2024-01-01T00:00:00.000Z",
                        }
                    },
                }
            ]
        },
    )

    result_dict = await latest_listings.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = LatestListingsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.data) == 1
    assert result.data[0].symbol == "BTC"
    assert result.data[0].quote["USD"].price == 50000.0


@pytest.mark.asyncio
async def test_latest_quotes(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/cryptocurrency/quotes/latest?symbol=BTC",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "data": {
                "BTC": {
                    "id": 1,
                    "name": "Bitcoin",
                    "symbol": "BTC",
                    "slug": "bitcoin",
                    "cmc_rank": 1,
                    "quote": {
                        "USD": {
                            "price": 50000.0,
                            "volume_24h": 30000000000.0,
                            "market_cap": 975000000000.0,
                            "percent_change_1h": 0.5,
                            "percent_change_24h": 2.1,
                            "percent_change_7d": -1.3,
                            "last_updated": "2024-01-01T00:00:00.000Z",
                        }
                    },
                }
            }
        },
    )

    result_dict = await latest_quotes.ainvoke(_args(symbol="BTC"))

    assert isinstance(result_dict, dict)
    result = LatestQuotesOutput.model_validate(result_dict)
    assert result.success is True
    assert "BTC" in result.data
    assert result.data["BTC"].quote["USD"].price == 50000.0


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_empty_credential_returns_error():  # type: ignore[no-untyped-def]
    """Pattern B: empty API key must return success=False without hitting the wire."""
    result_dict = await get_cryptocurrency_metadata.ainvoke(
        {"ids": "1", "api_key": ""}
    )

    assert isinstance(result_dict, dict)
    result = GetCryptocurrencyMetadataOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
