"""Tests for the Kalshi integration.

One happy-path test per action (mock JSON reflecting the documented
Trade API v2 response shape) + a manifest-shape trio + a failure-path
test (non-2xx -> success=False) + an empty-credential test.

Authenticated actions sign each request with an RSA private key; the
tests generate a throwaway RSA key so the signing path actually runs.
"""

from __future__ import annotations

from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from modulex_integrations.tools.kalshi import (
    TOOLS,
    amend_order,
    cancel_order,
    create_order,
    get_balance,
    get_candlesticks,
    get_event,
    get_event_candlesticks,
    get_events,
    get_exchange_announcements,
    get_exchange_schedule,
    get_exchange_status,
    get_fills,
    get_market,
    get_markets,
    get_order,
    get_orderbook,
    get_orders,
    get_positions,
    get_series_by_ticker,
    get_series_list,
    get_settlements,
    get_trades,
    manifest,
)
from modulex_integrations.tools.kalshi.outputs import (
    AmendOrderOutput,
    CancelOrderOutput,
    CreateOrderOutput,
    GetBalanceOutput,
    GetCandlesticksOutput,
    GetEventCandlesticksOutput,
    GetEventOutput,
    GetEventsOutput,
    GetExchangeAnnouncementsOutput,
    GetExchangeScheduleOutput,
    GetExchangeStatusOutput,
    GetFillsOutput,
    GetMarketOutput,
    GetMarketsOutput,
    GetOrderbookOutput,
    GetOrderOutput,
    GetOrdersOutput,
    GetPositionsOutput,
    GetSeriesByTickerOutput,
    GetSeriesListOutput,
    GetSettlementsOutput,
    GetTradesOutput,
)

API = "https://api.elections.kalshi.com/trade-api/v2"

_PRIVATE_KEY_PEM = (
    rsa.generate_private_key(public_exponent=65537, key_size=2048)
    .private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    .decode("ascii")
)

_AUTH = {"key_id": "test-key-id", "private_key": _PRIVATE_KEY_PEM}


def _auth(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_22_actions(self) -> None:
        assert len(manifest.actions) == 22

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_auth_injects_two_credential_fields(self) -> None:
        (auth,) = manifest.auth_schemas
        injected = {e.name for e in auth.setup_environment_variables if e.inject_into_auth_data}
        assert injected == {"KALSHI_KEY_ID", "KALSHI_PRIVATE_KEY"}


# --- Public market-data happy paths ----------------------------------------


@pytest.mark.asyncio
async def test_get_markets(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/markets",
        json={
            "markets": [{"ticker": "KXBTC-24DEC31", "status": "open", "yes_bid": 55}],
            "cursor": "c1",
        },
    )
    result = GetMarketsOutput.model_validate(await get_markets.ainvoke({}))
    assert result.success is True
    assert result.markets[0].ticker == "KXBTC-24DEC31"
    assert result.markets[0].yes_bid == 55
    assert result.cursor == "c1"


@pytest.mark.asyncio
async def test_get_market(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/markets/KXBTC-24DEC31",
        json={"market": {"ticker": "KXBTC-24DEC31", "title": "Bitcoin", "status": "open"}},
    )
    result = GetMarketOutput.model_validate(await get_market.ainvoke({"ticker": "KXBTC-24DEC31"}))
    assert result.success is True
    assert result.market is not None
    assert result.market.title == "Bitcoin"


@pytest.mark.asyncio
async def test_get_events(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/events",
        json={
            "events": [
                {"event_ticker": "KXBTC-24DEC31", "title": "BTC", "mutually_exclusive": False}
            ],
            "milestones": [{"id": "m1", "title": "Halving"}],
            "cursor": None,
        },
    )
    result = GetEventsOutput.model_validate(await get_events.ainvoke({}))
    assert result.success is True
    assert result.events[0].event_ticker == "KXBTC-24DEC31"
    assert result.milestones[0].id == "m1"


@pytest.mark.asyncio
async def test_get_event(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/events/KXBTC-24DEC31",
        json={"event": {"event_ticker": "KXBTC-24DEC31", "category": "Crypto", "markets": []}},
    )
    result = GetEventOutput.model_validate(
        await get_event.ainvoke({"event_ticker": "KXBTC-24DEC31"})
    )
    assert result.success is True
    assert result.event is not None
    assert result.event.category == "Crypto"


@pytest.mark.asyncio
async def test_get_orderbook(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/markets/KXBTC-24DEC31/orderbook",
        json={
            "orderbook": {"yes": [[55, 100]], "no": [[44, 50]]},
            "orderbook_fp": {"yes_dollars": [["0.55", "100.00"]]},
        },
    )
    result = GetOrderbookOutput.model_validate(
        await get_orderbook.ainvoke({"ticker": "KXBTC-24DEC31"})
    )
    assert result.success is True
    assert result.orderbook is not None
    assert result.orderbook.yes == [[55, 100]]
    assert result.orderbook_fp is not None
    assert result.orderbook_fp.yes_dollars == [["0.55", "100.00"]]


@pytest.mark.asyncio
async def test_get_trades(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/markets/trades",
        json={
            "trades": [{"trade_id": "t1", "ticker": "KXBTC-24DEC31", "count": 3}],
            "cursor": None,
        },
    )
    result = GetTradesOutput.model_validate(await get_trades.ainvoke({}))
    assert result.success is True
    assert result.trades[0].trade_id == "t1"
    assert result.trades[0].count == 3


@pytest.mark.asyncio
async def test_get_candlesticks(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/series/KXBTC/markets/KXBTC-24DEC31/candlesticks?start_ts=1&end_ts=2&period_interval=60",
        json={
            "ticker": "KXBTC-24DEC31",
            "candlesticks": [
                {
                    "end_period_ts": 100,
                    "yes_bid": {"open": 50, "close": 55},
                    "yes_ask": {"open": 51},
                    "price": {"open": 52, "mean": 53},
                    "volume": 1000,
                }
            ],
        },
    )
    result = GetCandlesticksOutput.model_validate(
        await get_candlesticks.ainvoke(
            {
                "series_ticker": "KXBTC",
                "ticker": "KXBTC-24DEC31",
                "start_ts": 1,
                "end_ts": 2,
                "period_interval": 60,
            }
        )
    )
    assert result.success is True
    assert result.ticker == "KXBTC-24DEC31"
    assert result.candlesticks[0].yes_bid is not None
    assert result.candlesticks[0].yes_bid.close == 55
    assert result.candlesticks[0].price is not None
    assert result.candlesticks[0].price.mean == 53


@pytest.mark.asyncio
async def test_get_event_candlesticks(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/series/KXBTC/events/KXBTC-24DEC31/candlesticks?start_ts=1&end_ts=2&period_interval=60",
        json={
            "market_tickers": ["KXBTC-24DEC31"],
            "adjusted_end_ts": 2,
            "market_candlesticks": [{"end_period_ts": 100, "volume_fp": "10.00"}],
        },
    )
    result = GetEventCandlesticksOutput.model_validate(
        await get_event_candlesticks.ainvoke(
            {
                "series_ticker": "KXBTC",
                "event_ticker": "KXBTC-24DEC31",
                "start_ts": 1,
                "end_ts": 2,
                "period_interval": 60,
            }
        )
    )
    assert result.success is True
    assert result.market_tickers == ["KXBTC-24DEC31"]
    assert result.adjusted_end_ts == 2
    assert result.market_candlesticks[0].volume_fp == "10.00"


@pytest.mark.asyncio
async def test_get_series_by_ticker(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/series/KXBTC",
        json={"series": {"ticker": "KXBTC", "title": "Bitcoin", "tags": ["crypto"]}},
    )
    result = GetSeriesByTickerOutput.model_validate(
        await get_series_by_ticker.ainvoke({"series_ticker": "KXBTC"})
    )
    assert result.success is True
    assert result.series is not None
    assert result.series.ticker == "KXBTC"
    assert result.series.tags == ["crypto"]


@pytest.mark.asyncio
async def test_get_series_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/series",
        json={"series": [{"ticker": "KXBTC", "category": "Crypto"}]},
    )
    result = GetSeriesListOutput.model_validate(await get_series_list.ainvoke({}))
    assert result.success is True
    assert result.series[0].category == "Crypto"


@pytest.mark.asyncio
async def test_get_exchange_status(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/exchange/status",
        json={
            "exchange_active": True,
            "trading_active": True,
            "exchange_estimated_resume_time": None,
        },
    )
    result = GetExchangeStatusOutput.model_validate(await get_exchange_status.ainvoke({}))
    assert result.success is True
    assert result.exchange_active is True
    assert result.trading_active is True


@pytest.mark.asyncio
async def test_get_exchange_schedule(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/exchange/schedule",
        json={"schedule": {"standard_hours": [{"monday": []}], "maintenance_windows": []}},
    )
    result = GetExchangeScheduleOutput.model_validate(await get_exchange_schedule.ainvoke({}))
    assert result.success is True
    assert result.schedule is not None
    assert result.schedule.standard_hours == [{"monday": []}]


@pytest.mark.asyncio
async def test_get_exchange_announcements(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/exchange/announcements",
        json={"announcements": [{"type": "info", "message": "Hello", "status": "active"}]},
    )
    result = GetExchangeAnnouncementsOutput.model_validate(
        await get_exchange_announcements.ainvoke({})
    )
    assert result.success is True
    assert result.announcements[0].message == "Hello"


# --- Authenticated happy paths ---------------------------------------------


@pytest.mark.asyncio
async def test_get_balance(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/portfolio/balance",
        json={"balance": 10000, "portfolio_value": 12000, "updated_ts": 1704067200},
    )
    result = GetBalanceOutput.model_validate(await get_balance.ainvoke(_auth()))
    assert result.success is True
    assert result.balance == 10000
    assert result.portfolio_value == 12000

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["KALSHI-ACCESS-KEY"] == "test-key-id"
    assert "KALSHI-ACCESS-SIGNATURE" in sent.headers
    assert "KALSHI-ACCESS-TIMESTAMP" in sent.headers


@pytest.mark.asyncio
async def test_get_positions(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/portfolio/positions",
        json={
            "market_positions": [{"ticker": "KXBTC-24DEC31", "position": 5}],
            "event_positions": [{"event_ticker": "KXBTC-24DEC31", "event_exposure": 100}],
            "cursor": None,
        },
    )
    result = GetPositionsOutput.model_validate(await get_positions.ainvoke(_auth()))
    assert result.success is True
    assert result.market_positions[0].position == 5
    assert result.event_positions[0].event_exposure == 100


@pytest.mark.asyncio
async def test_get_orders(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/portfolio/orders",
        json={
            "orders": [{"order_id": "o1", "ticker": "KXBTC-24DEC31", "status": "resting"}],
            "cursor": None,
        },
    )
    result = GetOrdersOutput.model_validate(await get_orders.ainvoke(_auth()))
    assert result.success is True
    assert result.orders[0].order_id == "o1"


@pytest.mark.asyncio
async def test_get_order(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/portfolio/orders/o1",
        json={"order": {"order_id": "o1", "status": "resting", "yes_price": 55}},
    )
    result = GetOrderOutput.model_validate(await get_order.ainvoke(_auth(order_id="o1")))
    assert result.success is True
    assert result.order is not None
    assert result.order.yes_price == 55


@pytest.mark.asyncio
async def test_get_fills(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/portfolio/fills",
        json={"fills": [{"trade_id": "t1", "ticker": "KXBTC-24DEC31", "count": 2}], "cursor": None},
    )
    result = GetFillsOutput.model_validate(await get_fills.ainvoke(_auth()))
    assert result.success is True
    assert result.fills[0].trade_id == "t1"


@pytest.mark.asyncio
async def test_get_settlements(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/portfolio/settlements",
        json={
            "settlements": [{"ticker": "KXBTC-24DEC31", "market_result": "yes", "revenue": 100}],
            "cursor": None,
        },
    )
    result = GetSettlementsOutput.model_validate(await get_settlements.ainvoke(_auth()))
    assert result.success is True
    assert result.settlements[0].market_result == "yes"
    assert result.settlements[0].revenue == 100


@pytest.mark.asyncio
async def test_create_order(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/portfolio/orders",
        json={"order": {"order_id": "o2", "ticker": "KXBTC-24DEC31", "status": "resting"}},
    )
    result = CreateOrderOutput.model_validate(
        await create_order.ainvoke(
            _auth(ticker="KXBTC-24DEC31", side="yes", action="buy", count=10, yes_price=55)
        )
    )
    assert result.success is True
    assert result.order is not None
    assert result.order.order_id == "o2"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["KALSHI-ACCESS-KEY"] == "test-key-id"


@pytest.mark.asyncio
async def test_cancel_order(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/portfolio/orders/o1",
        json={
            "order": {"order_id": "o1", "status": "canceled"},
            "reduced_by": 5,
            "reduced_by_fp": "5.00",
        },
    )
    result = CancelOrderOutput.model_validate(await cancel_order.ainvoke(_auth(order_id="o1")))
    assert result.success is True
    assert result.order is not None
    assert result.order.status == "canceled"
    assert result.reduced_by == 5


@pytest.mark.asyncio
async def test_amend_order(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/portfolio/orders/o1/amend",
        json={
            "old_order": {"order_id": "o1", "count": 10},
            "order": {"order_id": "o1", "count": 20},
        },
    )
    result = AmendOrderOutput.model_validate(
        await amend_order.ainvoke(
            _auth(order_id="o1", ticker="KXBTC-24DEC31", side="yes", action="buy", count=20)
        )
    )
    assert result.success is True
    assert result.old_order is not None
    assert result.old_order.count == 10
    assert result.order is not None
    assert result.order.count == 20


# --- Failure path + empty-credential path ----------------------------------


@pytest.mark.asyncio
async def test_get_market_non_2xx_returns_error(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/markets/BAD",
        status_code=404,
        json={"error": {"message": "not found"}},
    )
    result = GetMarketOutput.model_validate(await get_market.ainvoke({"ticker": "BAD"}))
    assert result.success is False
    assert result.error is not None
    assert "404" in result.error
    assert result.market is None


@pytest.mark.asyncio
async def test_get_balance_empty_credential() -> None:
    result = GetBalanceOutput.model_validate(
        await get_balance.ainvoke({"key_id": "", "private_key": ""})
    )
    assert result.success is False
    assert result.error is not None
    assert "Key ID" in result.error


@pytest.mark.asyncio
async def test_create_order_empty_private_key() -> None:
    result = CreateOrderOutput.model_validate(
        await create_order.ainvoke(
            {
                "key_id": "k",
                "private_key": "   ",
                "ticker": "KXBTC-24DEC31",
                "side": "yes",
                "action": "buy",
                "count": 1,
            }
        )
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_get_order_invalid_private_key(httpx_mock):  # type: ignore[no-untyped-def]
    # A non-empty but unparseable private key should surface as an error
    # without raising (the signing step fails gracefully).
    result = GetOrderOutput.model_validate(
        await get_order.ainvoke(
            {"key_id": "k", "private_key": "not-a-real-pem-key", "order_id": "o1"}
        )
    )
    assert result.success is False
    assert result.error is not None
