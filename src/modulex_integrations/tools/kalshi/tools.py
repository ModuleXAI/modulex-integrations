"""Kalshi LangChain ``@tool`` functions.

Twenty-two async tools wrapping the Kalshi Trade API v2
(``https://api.elections.kalshi.com/trade-api/v2``).

Authentication is **request signing**, not a static bearer token. Every
request carries three headers:

* ``KALSHI-ACCESS-KEY`` — the API key id.
* ``KALSHI-ACCESS-TIMESTAMP`` — the current Unix time in milliseconds.
* ``KALSHI-ACCESS-SIGNATURE`` — a base64 RSA-PSS (SHA-256, MGF1-SHA256,
  salt length = digest length) signature over the string
  ``timestamp + METHOD + path``, where ``path`` is the full request
  path including the ``/trade-api/v2`` prefix and EXCLUDING the query
  string.

The signing material (``key_id`` + ``private_key``) is resolved by the
runtime from the configured credential and injected into each function
by parameter name. The PEM private key is normalized before use so that
keys pasted with escaped newlines or wrapped lines still load.

Error model: non-2xx responses, timeouts, signing failures, and
unexpected exceptions are caught and returned as ``success=False`` +
``error`` rather than raising.
"""

from __future__ import annotations

import base64
import time
from typing import Any
from urllib.parse import quote

import httpx
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.kalshi.outputs import (
    AmendedOrder,
    AmendOrderOutput,
    Announcement,
    BidAskDistribution,
    CancelOrderOutput,
    CreateOrderOutput,
    Event,
    EventCandlestick,
    EventPosition,
    ExchangeSchedule,
    Fill,
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
    Market,
    MarketCandlestick,
    MarketPosition,
    Milestone,
    Order,
    Orderbook,
    OrderbookFp,
    PriceDistribution,
    Series,
    Settlement,
    SettlementSource,
    Trade,
)

__all__ = [
    "amend_order",
    "cancel_order",
    "create_order",
    "get_balance",
    "get_candlesticks",
    "get_event",
    "get_event_candlesticks",
    "get_events",
    "get_exchange_announcements",
    "get_exchange_schedule",
    "get_exchange_status",
    "get_fills",
    "get_market",
    "get_markets",
    "get_order",
    "get_orderbook",
    "get_orders",
    "get_positions",
    "get_series_by_ticker",
    "get_series_list",
    "get_settlements",
    "get_trades",
]

_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
_API_PREFIX = "/trade-api/v2"
_TIMEOUT = 30.0


# --- Auth helpers ----------------------------------------------------------


def _normalize_pem_key(private_key: str) -> str:
    """Normalize a user-supplied PEM private key.

    Handles literal ``\\n`` escape sequences and keys whose base64 body
    was collapsed onto a single line, reconstructing standard 64-char
    PEM lines. If no PEM header is present, the raw base64 is wrapped in
    a PKCS#8 ``PRIVATE KEY`` envelope.
    """
    key = private_key.strip().replace("\\n", "\n")

    begin = key.find("-----BEGIN")
    end = key.find("-----END")
    if begin != -1 and end != -1:
        header_end = key.find("-----", begin + len("-----BEGIN")) + len("-----")
        key_type = key[begin + len("-----BEGIN ") : header_end - len("-----")].strip()
        body = "".join(key[header_end:end].split())
        lines = [body[i : i + 64] for i in range(0, len(body), 64)]
        return f"-----BEGIN {key_type}-----\n" + "\n".join(lines) + f"\n-----END {key_type}-----"

    body = "".join(key.split())
    lines = [body[i : i + 64] for i in range(0, len(body), 64)]
    return "-----BEGIN PRIVATE KEY-----\n" + "\n".join(lines) + "\n-----END PRIVATE KEY-----"


def _build_auth_headers(key_id: str, private_key: str, method: str, path: str) -> dict[str, str]:
    """Build the signed Kalshi auth headers for one request.

    The signed message is ``timestamp_ms + METHOD + path`` where ``path``
    includes the ``/trade-api/v2`` prefix and excludes any query string.
    Signature is RSA-PSS over SHA-256 with MGF1-SHA256 and a salt length
    equal to the digest length.

    Verified against the Kalshi API docs (docs.kalshi.com getting_started
    api_keys; trading-api.readme.io).
    """
    timestamp = str(int(time.time() * 1000))
    path_without_query = path.split("?")[0]
    message = (timestamp + method.upper() + path_without_query).encode("utf-8")

    pem = _normalize_pem_key(private_key).encode("utf-8")
    loaded = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(loaded, rsa.RSAPrivateKey):
        raise ValueError("Kalshi private key must be an RSA key.")

    signature = loaded.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )

    return {
        "KALSHI-ACCESS-KEY": key_id,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode("ascii"),
        "Content-Type": "application/json",
    }


def _public_headers() -> dict[str, str]:
    return {"Content-Type": "application/json"}


def _credential_missing(key_id: str, private_key: str) -> str | None:
    if not key_id or not key_id.strip():
        return "Kalshi API Key ID is missing. Configure it in your credentials."
    if not private_key or not private_key.strip():
        return "Kalshi private key is missing. Configure it in your credentials."
    return None


# --- Input schemas (args_schema for each @tool) ----------------------------


class _AuthInput(BaseModel):
    key_id: str = Field(description="Kalshi API Key ID (provided by credential system)")
    private_key: str = Field(
        description="Kalshi RSA private key in PEM format (provided by credential system)"
    )


class GetMarketsInput(BaseModel):
    status: str | None = Field(
        default=None, description='Filter by market status: "unopened", "open", "closed", "settled"'
    )
    series_ticker: str | None = Field(default=None, description="Filter by series ticker")
    event_ticker: str | None = Field(default=None, description="Filter by event ticker")
    min_created_ts: int | None = Field(
        default=None, description="Minimum created timestamp (Unix seconds)"
    )
    max_created_ts: int | None = Field(
        default=None, description="Maximum created timestamp (Unix seconds)"
    )
    min_updated_ts: int | None = Field(
        default=None, description="Minimum updated timestamp (Unix seconds)"
    )
    min_close_ts: int | None = Field(
        default=None, description="Minimum close timestamp (Unix seconds)"
    )
    max_close_ts: int | None = Field(
        default=None, description="Maximum close timestamp (Unix seconds)"
    )
    min_settled_ts: int | None = Field(
        default=None, description="Minimum settled timestamp (Unix seconds)"
    )
    max_settled_ts: int | None = Field(
        default=None, description="Maximum settled timestamp (Unix seconds)"
    )
    tickers: str | None = Field(default=None, description="Comma-separated list of market tickers")
    mve_filter: str | None = Field(
        default=None, description='Multivariate event filter: "only" or "exclude"'
    )
    limit: int | None = Field(default=None, description="Number of results to return (1-1000)")
    cursor: str | None = Field(default=None, description="Pagination cursor")


class GetMarketInput(BaseModel):
    ticker: str = Field(description="Market ticker identifier (e.g., 'KXBTC-24DEC31')")


class GetEventsInput(BaseModel):
    status: str | None = Field(
        default=None, description='Filter by event status: "open", "closed", "settled"'
    )
    series_ticker: str | None = Field(default=None, description="Filter by series ticker")
    with_nested_markets: str | None = Field(
        default=None, description='Include nested markets: "true" or "false"'
    )
    with_milestones: str | None = Field(
        default=None, description='Include milestones: "true" or "false"'
    )
    min_close_ts: int | None = Field(
        default=None, description="Minimum close timestamp (Unix seconds)"
    )
    limit: int | None = Field(default=None, description="Number of results to return (1-200)")
    cursor: str | None = Field(default=None, description="Pagination cursor")


class GetEventInput(BaseModel):
    event_ticker: str = Field(description="Event ticker identifier")
    with_nested_markets: str | None = Field(
        default=None, description='Include nested markets: "true" or "false"'
    )


class GetBalanceInput(_AuthInput):
    pass


class GetPositionsInput(_AuthInput):
    ticker: str | None = Field(default=None, description="Filter by market ticker")
    event_ticker: str | None = Field(
        default=None, description="Filter by event ticker (max 10, comma-separated)"
    )
    count_filter: str | None = Field(
        default=None,
        description='Restrict to non-zero fields (comma-separated): "position", "total_traded"',
    )
    subaccount: str | None = Field(default=None, description="Subaccount identifier")
    limit: int | None = Field(default=None, description="Number of results to return (1-1000)")
    cursor: str | None = Field(default=None, description="Pagination cursor")


class GetOrdersInput(_AuthInput):
    ticker: str | None = Field(default=None, description="Filter by market ticker")
    event_ticker: str | None = Field(
        default=None, description="Filter by event ticker (max 10, comma-separated)"
    )
    status: str | None = Field(
        default=None, description='Filter by status: "resting", "canceled", "executed"'
    )
    min_ts: str | None = Field(
        default=None, description="Minimum timestamp filter (Unix timestamp)"
    )
    max_ts: str | None = Field(
        default=None, description="Maximum timestamp filter (Unix timestamp)"
    )
    subaccount: str | None = Field(default=None, description="Subaccount identifier")
    limit: int | None = Field(default=None, description="Number of results to return (1-1000)")
    cursor: str | None = Field(default=None, description="Pagination cursor")


class GetOrderInput(_AuthInput):
    order_id: str = Field(description="Order ID to retrieve")


class GetOrderbookInput(BaseModel):
    ticker: str = Field(description="Market ticker identifier")
    depth: int | None = Field(default=None, description="Number of price levels to return")


class GetTradesInput(BaseModel):
    ticker: str | None = Field(default=None, description="Filter by market ticker")
    min_ts: int | None = Field(default=None, description="Minimum timestamp (Unix seconds)")
    max_ts: int | None = Field(default=None, description="Maximum timestamp (Unix seconds)")
    limit: int | None = Field(default=None, description="Number of results to return (1-1000)")
    cursor: str | None = Field(default=None, description="Pagination cursor")


class GetCandlesticksInput(BaseModel):
    series_ticker: str = Field(description="Series ticker identifier")
    ticker: str = Field(description="Market ticker identifier")
    start_ts: int = Field(description="Start timestamp (Unix seconds)")
    end_ts: int = Field(description="End timestamp (Unix seconds)")
    period_interval: int = Field(description="Period interval: 1 (minute), 60 (hour), 1440 (day)")


class GetEventCandlesticksInput(BaseModel):
    series_ticker: str = Field(description="Series ticker identifier")
    event_ticker: str = Field(description="Event ticker identifier")
    start_ts: int = Field(description="Start timestamp (Unix seconds)")
    end_ts: int = Field(description="End timestamp (Unix seconds)")
    period_interval: int = Field(description="Period interval: 1 (minute), 60 (hour), 1440 (day)")


class GetFillsInput(_AuthInput):
    ticker: str | None = Field(default=None, description="Filter by market ticker")
    order_id: str | None = Field(default=None, description="Filter by order ID")
    min_ts: int | None = Field(default=None, description="Minimum timestamp (Unix seconds)")
    max_ts: int | None = Field(default=None, description="Maximum timestamp (Unix seconds)")
    subaccount: str | None = Field(default=None, description="Subaccount identifier")
    limit: int | None = Field(default=None, description="Number of results to return (1-1000)")
    cursor: str | None = Field(default=None, description="Pagination cursor")


class GetSettlementsInput(_AuthInput):
    ticker: str | None = Field(default=None, description="Filter by market ticker")
    event_ticker: str | None = Field(default=None, description="Filter by event ticker")
    min_ts: int | None = Field(default=None, description="Minimum settled timestamp (Unix seconds)")
    max_ts: int | None = Field(default=None, description="Maximum settled timestamp (Unix seconds)")
    subaccount: str | None = Field(default=None, description="Subaccount number (0 primary, 1-63)")
    limit: int | None = Field(default=None, description="Number of results to return (1-1000)")
    cursor: str | None = Field(default=None, description="Pagination cursor")


class GetSeriesByTickerInput(BaseModel):
    series_ticker: str = Field(description="Series ticker identifier")
    include_volume: str | None = Field(
        default=None, description='Include volume data: "true" or "false"'
    )


class GetSeriesListInput(BaseModel):
    category: str | None = Field(default=None, description="Filter by category")
    tags: str | None = Field(default=None, description="Filter by comma-separated tags")
    include_product_metadata: str | None = Field(
        default=None, description='Include product metadata: "true" or "false"'
    )
    include_volume: str | None = Field(
        default=None, description='Include volume data: "true" or "false"'
    )
    min_updated_ts: int | None = Field(
        default=None, description="Minimum updated timestamp (Unix seconds)"
    )


class GetExchangeStatusInput(BaseModel):
    pass


class GetExchangeScheduleInput(BaseModel):
    pass


class GetExchangeAnnouncementsInput(BaseModel):
    pass


class CreateOrderInput(_AuthInput):
    ticker: str = Field(description="Market ticker identifier")
    side: str = Field(description='Order side: "yes" or "no"')
    action: str = Field(description='Action type: "buy" or "sell"')
    count: int | None = Field(
        default=None, description="Number of contracts to trade (provide count or count_fp)"
    )
    type: str | None = Field(
        default=None, description='Order type: "limit" or "market" (default "limit")'
    )
    yes_price: int | None = Field(default=None, description="Yes price in cents (1-99)")
    no_price: int | None = Field(default=None, description="No price in cents (1-99)")
    yes_price_dollars: str | None = Field(
        default=None, description="Yes price in dollars (e.g., '0.56')"
    )
    no_price_dollars: str | None = Field(
        default=None, description="No price in dollars (e.g., '0.56')"
    )
    client_order_id: str | None = Field(default=None, description="Custom order identifier")
    expiration_ts: int | None = Field(
        default=None, description="Unix timestamp for order expiration"
    )
    time_in_force: str | None = Field(
        default=None,
        description="Time in force: 'fill_or_kill', 'good_till_canceled', 'immediate_or_cancel'",
    )
    buy_max_cost: int | None = Field(
        default=None, description="Maximum cost in cents (auto-enables fill_or_kill)"
    )
    post_only: bool | None = Field(default=None, description="Maker-only order")
    reduce_only: bool | None = Field(default=None, description="Position reduction only")
    self_trade_prevention_type: str | None = Field(
        default=None, description="Self-trade prevention: 'taker_at_cross' or 'maker'"
    )
    order_group_id: str | None = Field(default=None, description="Associated order group ID")
    count_fp: str | None = Field(
        default=None, description="Count in fixed-point for fractional contracts"
    )
    cancel_order_on_pause: bool | None = Field(
        default=None, description="Cancel order on market pause"
    )
    subaccount: str | None = Field(default=None, description="Subaccount to use for the order")


class CancelOrderInput(_AuthInput):
    order_id: str = Field(description="Order ID to cancel")


class AmendOrderInput(_AuthInput):
    order_id: str = Field(description="Order ID to amend")
    ticker: str = Field(description="Market ticker identifier")
    side: str = Field(description='Order side: "yes" or "no"')
    action: str = Field(description='Action type: "buy" or "sell"')
    client_order_id: str | None = Field(
        default=None, description="Original client-specified order ID"
    )
    updated_client_order_id: str | None = Field(
        default=None, description="New client-specified order ID"
    )
    count: int | None = Field(default=None, description="Updated quantity for the order")
    yes_price: int | None = Field(default=None, description="Updated yes price in cents (1-99)")
    no_price: int | None = Field(default=None, description="Updated no price in cents (1-99)")
    yes_price_dollars: str | None = Field(default=None, description="Updated yes price in dollars")
    no_price_dollars: str | None = Field(default=None, description="Updated no price in dollars")
    count_fp: str | None = Field(
        default=None, description="Count in fixed-point for fractional contracts"
    )


# --- Parse helpers ---------------------------------------------------------


def _pick(src: dict[str, Any], model: type[BaseModel]) -> dict[str, Any]:
    """Project ``src`` onto a model's field names, dropping ``None`` so
    list fields fall back to their ``default_factory`` instead of failing
    validation on an explicit ``None``."""
    out: dict[str, Any] = {}
    for key in model.model_fields:
        value = src.get(key)
        if value is not None:
            out[key] = value
    return out


def _market(m: dict[str, Any]) -> Market:
    return Market.model_validate(_pick(m, Market))


def _event(e: dict[str, Any]) -> Event:
    return Event(
        event_ticker=e.get("event_ticker"),
        series_ticker=e.get("series_ticker"),
        title=e.get("title"),
        sub_title=e.get("sub_title"),
        mutually_exclusive=e.get("mutually_exclusive"),
        category=e.get("category"),
        collateral_return_type=e.get("collateral_return_type"),
        strike_date=e.get("strike_date"),
        strike_period=e.get("strike_period"),
        available_on_brokers=e.get("available_on_brokers"),
        product_metadata=e.get("product_metadata"),
        markets=e.get("markets") or [],
    )


def _order(o: dict[str, Any]) -> Order:
    return Order.model_validate(_pick(o, Order))


def _amended_order(o: dict[str, Any]) -> AmendedOrder:
    return AmendedOrder.model_validate(_pick(o, AmendedOrder))


def _bid_ask(obj: dict[str, Any] | None) -> BidAskDistribution:
    return BidAskDistribution.model_validate(_pick(obj or {}, BidAskDistribution))


def _price(obj: dict[str, Any] | None) -> PriceDistribution:
    return PriceDistribution.model_validate(_pick(obj or {}, PriceDistribution))


def _series(s: dict[str, Any]) -> Series:
    sources = [
        SettlementSource(name=src.get("name"), url=src.get("url"))
        for src in (s.get("settlement_sources") or [])
    ]
    return Series(
        ticker=s.get("ticker"),
        title=s.get("title"),
        frequency=s.get("frequency"),
        category=s.get("category"),
        tags=s.get("tags") or [],
        settlement_sources=sources,
        contract_url=s.get("contract_url"),
        contract_terms_url=s.get("contract_terms_url"),
        fee_type=s.get("fee_type"),
        fee_multiplier=s.get("fee_multiplier"),
        additional_prohibitions=s.get("additional_prohibitions") or [],
        product_metadata=s.get("product_metadata"),
        volume=s.get("volume"),
        volume_fp=s.get("volume_fp"),
        last_updated_ts=s.get("last_updated_ts"),
    )


# --- Market data tools -----------------------------------------------------


@tool(args_schema=GetMarketsInput)
@serialize_pydantic_return
async def get_markets(
    status: str | None = None,
    series_ticker: str | None = None,
    event_ticker: str | None = None,
    min_created_ts: int | None = None,
    max_created_ts: int | None = None,
    min_updated_ts: int | None = None,
    min_close_ts: int | None = None,
    max_close_ts: int | None = None,
    min_settled_ts: int | None = None,
    max_settled_ts: int | None = None,
    tickers: str | None = None,
    mve_filter: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> GetMarketsOutput:
    """Retrieve a list of prediction markets from Kalshi with full filtering options."""
    params: dict[str, Any] = {}
    if status:
        params["status"] = status
    if series_ticker:
        params["series_ticker"] = series_ticker
    if event_ticker:
        params["event_ticker"] = event_ticker
    if min_created_ts is not None:
        params["min_created_ts"] = min_created_ts
    if max_created_ts is not None:
        params["max_created_ts"] = max_created_ts
    if min_updated_ts is not None:
        params["min_updated_ts"] = min_updated_ts
    if min_close_ts is not None:
        params["min_close_ts"] = min_close_ts
    if max_close_ts is not None:
        params["max_close_ts"] = max_close_ts
    if min_settled_ts is not None:
        params["min_settled_ts"] = min_settled_ts
    if max_settled_ts is not None:
        params["max_settled_ts"] = max_settled_ts
    if tickers:
        params["tickers"] = tickers
    if mve_filter:
        params["mve_filter"] = mve_filter
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/markets", headers=_public_headers(), params=params
            )
        if response.status_code != 200:
            return GetMarketsOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetMarketsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMarketsOutput(success=False, error=f"get_markets failed: {exc}")

    return GetMarketsOutput(
        success=True,
        markets=[_market(m) for m in (data.get("markets") or [])],
        cursor=data.get("cursor"),
    )


@tool(args_schema=GetMarketInput)
@serialize_pydantic_return
async def get_market(ticker: str) -> GetMarketOutput:
    """Retrieve details of a specific prediction market by ticker."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/markets/{quote(ticker.strip(), safe='')}",
                headers=_public_headers(),
            )
        if response.status_code != 200:
            return GetMarketOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetMarketOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMarketOutput(success=False, error=f"get_market failed: {exc}")

    return GetMarketOutput(success=True, market=_market(data.get("market") or {}))


@tool(args_schema=GetEventsInput)
@serialize_pydantic_return
async def get_events(
    status: str | None = None,
    series_ticker: str | None = None,
    with_nested_markets: str | None = None,
    with_milestones: str | None = None,
    min_close_ts: int | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> GetEventsOutput:
    """Retrieve a list of events from Kalshi with optional filtering."""
    params: dict[str, Any] = {}
    if status:
        params["status"] = status
    if series_ticker:
        params["series_ticker"] = series_ticker
    if with_nested_markets:
        params["with_nested_markets"] = with_nested_markets
    if with_milestones:
        params["with_milestones"] = with_milestones
    if min_close_ts is not None:
        params["min_close_ts"] = min_close_ts
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/events", headers=_public_headers(), params=params
            )
        if response.status_code != 200:
            return GetEventsOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetEventsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetEventsOutput(success=False, error=f"get_events failed: {exc}")

    milestones = [
        Milestone.model_validate(_pick(m, Milestone)) for m in (data.get("milestones") or [])
    ]
    return GetEventsOutput(
        success=True,
        events=[_event(e) for e in (data.get("events") or [])],
        milestones=milestones,
        cursor=data.get("cursor"),
    )


@tool(args_schema=GetEventInput)
@serialize_pydantic_return
async def get_event(event_ticker: str, with_nested_markets: str | None = None) -> GetEventOutput:
    """Retrieve details of a specific event by ticker."""
    params: dict[str, Any] = {}
    if with_nested_markets:
        params["with_nested_markets"] = with_nested_markets

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/events/{quote(event_ticker.strip(), safe='')}",
                headers=_public_headers(),
                params=params,
            )
        if response.status_code != 200:
            return GetEventOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetEventOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetEventOutput(success=False, error=f"get_event failed: {exc}")

    return GetEventOutput(success=True, event=_event(data.get("event") or {}))


@tool(args_schema=GetOrderbookInput)
@serialize_pydantic_return
async def get_orderbook(ticker: str, depth: int | None = None) -> GetOrderbookOutput:
    """Retrieve the orderbook (yes and no bids) for a specific market."""
    params: dict[str, Any] = {}
    if depth is not None:
        params["depth"] = depth

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/markets/{quote(ticker.strip(), safe='')}/orderbook",
                headers=_public_headers(),
                params=params,
            )
        if response.status_code != 200:
            return GetOrderbookOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetOrderbookOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetOrderbookOutput(success=False, error=f"get_orderbook failed: {exc}")

    ob = data.get("orderbook") or {}
    ob_fp = data.get("orderbook_fp") or {}
    return GetOrderbookOutput(
        success=True,
        orderbook=Orderbook(
            yes=ob.get("yes") or [],
            no=ob.get("no") or [],
            yes_dollars=ob.get("yes_dollars") or [],
            no_dollars=ob.get("no_dollars") or [],
        ),
        orderbook_fp=OrderbookFp(
            yes_dollars=ob_fp.get("yes_dollars") or [],
            no_dollars=ob_fp.get("no_dollars") or [],
        ),
    )


@tool(args_schema=GetTradesInput)
@serialize_pydantic_return
async def get_trades(
    ticker: str | None = None,
    min_ts: int | None = None,
    max_ts: int | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> GetTradesOutput:
    """Retrieve recent public trades across markets with optional filtering."""
    params: dict[str, Any] = {}
    if ticker:
        params["ticker"] = ticker
    if min_ts is not None:
        params["min_ts"] = min_ts
    if max_ts is not None:
        params["max_ts"] = max_ts
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/markets/trades", headers=_public_headers(), params=params
            )
        if response.status_code != 200:
            return GetTradesOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetTradesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetTradesOutput(success=False, error=f"get_trades failed: {exc}")

    trades = [Trade.model_validate(_pick(t, Trade)) for t in (data.get("trades") or [])]
    return GetTradesOutput(success=True, trades=trades, cursor=data.get("cursor"))


@tool(args_schema=GetCandlesticksInput)
@serialize_pydantic_return
async def get_candlesticks(
    series_ticker: str,
    ticker: str,
    start_ts: int,
    end_ts: int,
    period_interval: int,
) -> GetCandlesticksOutput:
    """Retrieve OHLC candlestick data for a specific market."""
    params: dict[str, Any] = {
        "start_ts": start_ts,
        "end_ts": end_ts,
        "period_interval": period_interval,
    }
    url = (
        f"{_BASE_URL}/series/{quote(series_ticker.strip(), safe='')}"
        f"/markets/{quote(ticker.strip(), safe='')}/candlesticks"
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=_public_headers(), params=params)
        if response.status_code != 200:
            return GetCandlesticksOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetCandlesticksOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCandlesticksOutput(success=False, error=f"get_candlesticks failed: {exc}")

    candlesticks = [
        MarketCandlestick(
            end_period_ts=c.get("end_period_ts"),
            yes_bid=_bid_ask(c.get("yes_bid")),
            yes_ask=_bid_ask(c.get("yes_ask")),
            price=_price(c.get("price")),
            volume=c.get("volume"),
            volume_fp=c.get("volume_fp"),
            open_interest=c.get("open_interest"),
            open_interest_fp=c.get("open_interest_fp"),
        )
        for c in (data.get("candlesticks") or [])
    ]
    return GetCandlesticksOutput(success=True, ticker=data.get("ticker"), candlesticks=candlesticks)


@tool(args_schema=GetEventCandlesticksInput)
@serialize_pydantic_return
async def get_event_candlesticks(
    series_ticker: str,
    event_ticker: str,
    start_ts: int,
    end_ts: int,
    period_interval: int,
) -> GetEventCandlesticksOutput:
    """Retrieve OHLC candlestick data aggregated across all markets in an event."""
    params: dict[str, Any] = {
        "start_ts": start_ts,
        "end_ts": end_ts,
        "period_interval": period_interval,
    }
    url = (
        f"{_BASE_URL}/series/{quote(series_ticker.strip(), safe='')}"
        f"/events/{quote(event_ticker.strip(), safe='')}/candlesticks"
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=_public_headers(), params=params)
        if response.status_code != 200:
            return GetEventCandlesticksOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetEventCandlesticksOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetEventCandlesticksOutput(
            success=False, error=f"get_event_candlesticks failed: {exc}"
        )

    candlesticks = [
        EventCandlestick(
            end_period_ts=c.get("end_period_ts"),
            yes_bid=_bid_ask(c.get("yes_bid")),
            yes_ask=_bid_ask(c.get("yes_ask")),
            price=_price(c.get("price")),
            volume_fp=c.get("volume_fp"),
            open_interest_fp=c.get("open_interest_fp"),
        )
        for c in (data.get("market_candlesticks") or [])
    ]
    return GetEventCandlesticksOutput(
        success=True,
        market_tickers=data.get("market_tickers") or [],
        adjusted_end_ts=data.get("adjusted_end_ts"),
        market_candlesticks=candlesticks,
    )


@tool(args_schema=GetSeriesByTickerInput)
@serialize_pydantic_return
async def get_series_by_ticker(
    series_ticker: str, include_volume: str | None = None
) -> GetSeriesByTickerOutput:
    """Retrieve details of a specific market series by ticker."""
    params: dict[str, Any] = {}
    if include_volume:
        params["include_volume"] = include_volume

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/series/{quote(series_ticker.strip(), safe='')}",
                headers=_public_headers(),
                params=params,
            )
        if response.status_code != 200:
            return GetSeriesByTickerOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetSeriesByTickerOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSeriesByTickerOutput(success=False, error=f"get_series_by_ticker failed: {exc}")

    series = data.get("series") if isinstance(data.get("series"), dict) else data
    return GetSeriesByTickerOutput(success=True, series=_series(series or {}))


@tool(args_schema=GetSeriesListInput)
@serialize_pydantic_return
async def get_series_list(
    category: str | None = None,
    tags: str | None = None,
    include_product_metadata: str | None = None,
    include_volume: str | None = None,
    min_updated_ts: int | None = None,
) -> GetSeriesListOutput:
    """Retrieve a list of market series from Kalshi with optional filtering."""
    params: dict[str, Any] = {}
    if category:
        params["category"] = category
    if tags:
        params["tags"] = tags
    if include_product_metadata:
        params["include_product_metadata"] = include_product_metadata
    if include_volume:
        params["include_volume"] = include_volume
    if min_updated_ts is not None:
        params["min_updated_ts"] = min_updated_ts

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/series", headers=_public_headers(), params=params
            )
        if response.status_code != 200:
            return GetSeriesListOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetSeriesListOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSeriesListOutput(success=False, error=f"get_series_list failed: {exc}")

    return GetSeriesListOutput(
        success=True, series=[_series(s) for s in (data.get("series") or [])]
    )


@tool(args_schema=GetExchangeStatusInput)
@serialize_pydantic_return
async def get_exchange_status() -> GetExchangeStatusOutput:
    """Retrieve the current status of the Kalshi exchange (trading and exchange activity)."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/exchange/status", headers=_public_headers())
        if response.status_code != 200:
            return GetExchangeStatusOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetExchangeStatusOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetExchangeStatusOutput(success=False, error=f"get_exchange_status failed: {exc}")

    return GetExchangeStatusOutput(
        success=True,
        exchange_active=data.get("exchange_active"),
        trading_active=data.get("trading_active"),
        exchange_estimated_resume_time=data.get("exchange_estimated_resume_time"),
    )


@tool(args_schema=GetExchangeScheduleInput)
@serialize_pydantic_return
async def get_exchange_schedule() -> GetExchangeScheduleOutput:
    """Retrieve the Kalshi exchange trading schedule and maintenance windows."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/exchange/schedule", headers=_public_headers())
        if response.status_code != 200:
            return GetExchangeScheduleOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetExchangeScheduleOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetExchangeScheduleOutput(
            success=False, error=f"get_exchange_schedule failed: {exc}"
        )

    schedule = data.get("schedule") or {}
    return GetExchangeScheduleOutput(
        success=True,
        schedule=ExchangeSchedule(
            standard_hours=schedule.get("standard_hours") or [],
            maintenance_windows=schedule.get("maintenance_windows") or [],
        ),
    )


@tool(args_schema=GetExchangeAnnouncementsInput)
@serialize_pydantic_return
async def get_exchange_announcements() -> GetExchangeAnnouncementsOutput:
    """Retrieve exchange-wide announcements from Kalshi."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/exchange/announcements", headers=_public_headers()
            )
        if response.status_code != 200:
            return GetExchangeAnnouncementsOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetExchangeAnnouncementsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetExchangeAnnouncementsOutput(
            success=False, error=f"get_exchange_announcements failed: {exc}"
        )

    announcements = [
        Announcement.model_validate(_pick(a, Announcement))
        for a in (data.get("announcements") or [])
    ]
    return GetExchangeAnnouncementsOutput(success=True, announcements=announcements)


# --- Authenticated portfolio tools -----------------------------------------


@tool(args_schema=GetBalanceInput)
@serialize_pydantic_return
async def get_balance(key_id: str, private_key: str) -> GetBalanceOutput:
    """Retrieve your account balance and portfolio value from Kalshi."""
    missing = _credential_missing(key_id, private_key)
    if missing:
        return GetBalanceOutput(success=False, error=missing)

    path = f"{_API_PREFIX}/portfolio/balance"
    try:
        headers = _build_auth_headers(key_id, private_key, "GET", path)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/portfolio/balance", headers=headers)
        if response.status_code != 200:
            return GetBalanceOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        return GetBalanceOutput(success=False, error=f"Invalid Kalshi private key: {exc}")
    except httpx.TimeoutException:
        return GetBalanceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetBalanceOutput(success=False, error=f"get_balance failed: {exc}")

    return GetBalanceOutput(
        success=True,
        balance=data.get("balance"),
        portfolio_value=data.get("portfolio_value"),
        updated_ts=data.get("updated_ts"),
    )


@tool(args_schema=GetPositionsInput)
@serialize_pydantic_return
async def get_positions(
    key_id: str,
    private_key: str,
    ticker: str | None = None,
    event_ticker: str | None = None,
    count_filter: str | None = None,
    subaccount: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> GetPositionsOutput:
    """Retrieve your open positions from Kalshi."""
    missing = _credential_missing(key_id, private_key)
    if missing:
        return GetPositionsOutput(success=False, error=missing)

    params: dict[str, Any] = {}
    if ticker:
        params["ticker"] = ticker
    if event_ticker:
        params["event_ticker"] = event_ticker
    if count_filter:
        params["count_filter"] = count_filter
    if subaccount:
        params["subaccount"] = subaccount
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor

    path = f"{_API_PREFIX}/portfolio/positions"
    try:
        headers = _build_auth_headers(key_id, private_key, "GET", path)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/portfolio/positions", headers=headers, params=params
            )
        if response.status_code != 200:
            return GetPositionsOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        return GetPositionsOutput(success=False, error=f"Invalid Kalshi private key: {exc}")
    except httpx.TimeoutException:
        return GetPositionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetPositionsOutput(success=False, error=f"get_positions failed: {exc}")

    market_positions = [
        MarketPosition.model_validate(_pick(p, MarketPosition))
        for p in (data.get("market_positions") or [])
    ]
    event_positions = [
        EventPosition.model_validate(_pick(p, EventPosition))
        for p in (data.get("event_positions") or [])
    ]
    return GetPositionsOutput(
        success=True,
        market_positions=market_positions,
        event_positions=event_positions,
        cursor=data.get("cursor"),
    )


@tool(args_schema=GetOrdersInput)
@serialize_pydantic_return
async def get_orders(
    key_id: str,
    private_key: str,
    ticker: str | None = None,
    event_ticker: str | None = None,
    status: str | None = None,
    min_ts: str | None = None,
    max_ts: str | None = None,
    subaccount: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> GetOrdersOutput:
    """Retrieve your orders from Kalshi with optional filtering."""
    missing = _credential_missing(key_id, private_key)
    if missing:
        return GetOrdersOutput(success=False, error=missing)

    params: dict[str, Any] = {}
    if ticker:
        params["ticker"] = ticker
    if event_ticker:
        params["event_ticker"] = event_ticker
    if status:
        params["status"] = status
    if min_ts:
        params["min_ts"] = min_ts
    if max_ts:
        params["max_ts"] = max_ts
    if subaccount:
        params["subaccount"] = subaccount
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor

    path = f"{_API_PREFIX}/portfolio/orders"
    try:
        headers = _build_auth_headers(key_id, private_key, "GET", path)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/portfolio/orders", headers=headers, params=params
            )
        if response.status_code != 200:
            return GetOrdersOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        return GetOrdersOutput(success=False, error=f"Invalid Kalshi private key: {exc}")
    except httpx.TimeoutException:
        return GetOrdersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetOrdersOutput(success=False, error=f"get_orders failed: {exc}")

    return GetOrdersOutput(
        success=True,
        orders=[_order(o) for o in (data.get("orders") or [])],
        cursor=data.get("cursor"),
    )


@tool(args_schema=GetOrderInput)
@serialize_pydantic_return
async def get_order(key_id: str, private_key: str, order_id: str) -> GetOrderOutput:
    """Retrieve details of a specific order by ID from Kalshi."""
    missing = _credential_missing(key_id, private_key)
    if missing:
        return GetOrderOutput(success=False, error=missing)

    order_id = order_id.strip()
    path = f"{_API_PREFIX}/portfolio/orders/{order_id}"
    try:
        headers = _build_auth_headers(key_id, private_key, "GET", path)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/portfolio/orders/{quote(order_id, safe='')}", headers=headers
            )
        if response.status_code != 200:
            return GetOrderOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        return GetOrderOutput(success=False, error=f"Invalid Kalshi private key: {exc}")
    except httpx.TimeoutException:
        return GetOrderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetOrderOutput(success=False, error=f"get_order failed: {exc}")

    return GetOrderOutput(success=True, order=_order(data.get("order") or {}))


@tool(args_schema=GetFillsInput)
@serialize_pydantic_return
async def get_fills(
    key_id: str,
    private_key: str,
    ticker: str | None = None,
    order_id: str | None = None,
    min_ts: int | None = None,
    max_ts: int | None = None,
    subaccount: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> GetFillsOutput:
    """Retrieve your portfolio's fills/trades from Kalshi."""
    missing = _credential_missing(key_id, private_key)
    if missing:
        return GetFillsOutput(success=False, error=missing)

    params: dict[str, Any] = {}
    if ticker:
        params["ticker"] = ticker
    if order_id:
        params["order_id"] = order_id
    if min_ts is not None:
        params["min_ts"] = min_ts
    if max_ts is not None:
        params["max_ts"] = max_ts
    if subaccount:
        params["subaccount"] = subaccount
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor

    path = f"{_API_PREFIX}/portfolio/fills"
    try:
        headers = _build_auth_headers(key_id, private_key, "GET", path)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/portfolio/fills", headers=headers, params=params
            )
        if response.status_code != 200:
            return GetFillsOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        return GetFillsOutput(success=False, error=f"Invalid Kalshi private key: {exc}")
    except httpx.TimeoutException:
        return GetFillsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetFillsOutput(success=False, error=f"get_fills failed: {exc}")

    fills = [Fill.model_validate(_pick(f, Fill)) for f in (data.get("fills") or [])]
    return GetFillsOutput(success=True, fills=fills, cursor=data.get("cursor"))


@tool(args_schema=GetSettlementsInput)
@serialize_pydantic_return
async def get_settlements(
    key_id: str,
    private_key: str,
    ticker: str | None = None,
    event_ticker: str | None = None,
    min_ts: int | None = None,
    max_ts: int | None = None,
    subaccount: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> GetSettlementsOutput:
    """Retrieve your portfolio settlement history from Kalshi."""
    missing = _credential_missing(key_id, private_key)
    if missing:
        return GetSettlementsOutput(success=False, error=missing)

    params: dict[str, Any] = {}
    if ticker:
        params["ticker"] = ticker
    if event_ticker:
        params["event_ticker"] = event_ticker
    if min_ts is not None:
        params["min_ts"] = min_ts
    if max_ts is not None:
        params["max_ts"] = max_ts
    if subaccount:
        params["subaccount"] = subaccount
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor

    path = f"{_API_PREFIX}/portfolio/settlements"
    try:
        headers = _build_auth_headers(key_id, private_key, "GET", path)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/portfolio/settlements", headers=headers, params=params
            )
        if response.status_code != 200:
            return GetSettlementsOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        return GetSettlementsOutput(success=False, error=f"Invalid Kalshi private key: {exc}")
    except httpx.TimeoutException:
        return GetSettlementsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSettlementsOutput(success=False, error=f"get_settlements failed: {exc}")

    settlements = [
        Settlement.model_validate(_pick(s, Settlement)) for s in (data.get("settlements") or [])
    ]
    return GetSettlementsOutput(success=True, settlements=settlements, cursor=data.get("cursor"))


# --- Trading tools ---------------------------------------------------------


@tool(args_schema=CreateOrderInput)
@serialize_pydantic_return
async def create_order(
    key_id: str,
    private_key: str,
    ticker: str,
    side: str,
    action: str,
    count: int | None = None,
    type: str | None = None,
    yes_price: int | None = None,
    no_price: int | None = None,
    yes_price_dollars: str | None = None,
    no_price_dollars: str | None = None,
    client_order_id: str | None = None,
    expiration_ts: int | None = None,
    time_in_force: str | None = None,
    buy_max_cost: int | None = None,
    post_only: bool | None = None,
    reduce_only: bool | None = None,
    self_trade_prevention_type: str | None = None,
    order_group_id: str | None = None,
    count_fp: str | None = None,
    cancel_order_on_pause: bool | None = None,
    subaccount: str | None = None,
) -> CreateOrderOutput:
    """Create a new order on a Kalshi prediction market."""
    missing = _credential_missing(key_id, private_key)
    if missing:
        return CreateOrderOutput(success=False, error=missing)

    body: dict[str, Any] = {
        "ticker": ticker,
        "side": side.lower(),
        "action": action.lower(),
    }
    if count is not None:
        body["count"] = count
    if count_fp:
        body["count_fp"] = count_fp
    if type:
        body["type"] = type.lower()
    if yes_price is not None:
        body["yes_price"] = yes_price
    if no_price is not None:
        body["no_price"] = no_price
    if yes_price_dollars:
        body["yes_price_dollars"] = yes_price_dollars
    if no_price_dollars:
        body["no_price_dollars"] = no_price_dollars
    if client_order_id:
        body["client_order_id"] = client_order_id
    if expiration_ts is not None:
        body["expiration_ts"] = expiration_ts
    if time_in_force:
        body["time_in_force"] = time_in_force
    if buy_max_cost is not None:
        body["buy_max_cost"] = buy_max_cost
    if post_only is not None:
        body["post_only"] = post_only
    if reduce_only is not None:
        body["reduce_only"] = reduce_only
    if self_trade_prevention_type:
        body["self_trade_prevention_type"] = self_trade_prevention_type
    if order_group_id:
        body["order_group_id"] = order_group_id
    if cancel_order_on_pause is not None:
        body["cancel_order_on_pause"] = cancel_order_on_pause
    if subaccount:
        body["subaccount"] = subaccount

    path = f"{_API_PREFIX}/portfolio/orders"
    try:
        headers = _build_auth_headers(key_id, private_key, "POST", path)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/portfolio/orders", headers=headers, json=body
            )
        if response.status_code not in (200, 201):
            return CreateOrderOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        return CreateOrderOutput(success=False, error=f"Invalid Kalshi private key: {exc}")
    except httpx.TimeoutException:
        return CreateOrderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateOrderOutput(success=False, error=f"create_order failed: {exc}")

    return CreateOrderOutput(success=True, order=_order(data.get("order") or {}))


@tool(args_schema=CancelOrderInput)
@serialize_pydantic_return
async def cancel_order(key_id: str, private_key: str, order_id: str) -> CancelOrderOutput:
    """Cancel an existing order on Kalshi."""
    missing = _credential_missing(key_id, private_key)
    if missing:
        return CancelOrderOutput(success=False, error=missing)

    order_id = order_id.strip()
    path = f"{_API_PREFIX}/portfolio/orders/{order_id}"
    try:
        headers = _build_auth_headers(key_id, private_key, "DELETE", path)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/portfolio/orders/{quote(order_id, safe='')}", headers=headers
            )
        if response.status_code != 200:
            return CancelOrderOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        return CancelOrderOutput(success=False, error=f"Invalid Kalshi private key: {exc}")
    except httpx.TimeoutException:
        return CancelOrderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CancelOrderOutput(success=False, error=f"cancel_order failed: {exc}")

    return CancelOrderOutput(
        success=True,
        order=_order(data.get("order") or {}),
        reduced_by=data.get("reduced_by"),
        reduced_by_fp=data.get("reduced_by_fp"),
    )


@tool(args_schema=AmendOrderInput)
@serialize_pydantic_return
async def amend_order(
    key_id: str,
    private_key: str,
    order_id: str,
    ticker: str,
    side: str,
    action: str,
    client_order_id: str | None = None,
    updated_client_order_id: str | None = None,
    count: int | None = None,
    yes_price: int | None = None,
    no_price: int | None = None,
    yes_price_dollars: str | None = None,
    no_price_dollars: str | None = None,
    count_fp: str | None = None,
) -> AmendOrderOutput:
    """Modify the price or quantity of an existing order on Kalshi."""
    missing = _credential_missing(key_id, private_key)
    if missing:
        return AmendOrderOutput(success=False, error=missing)

    order_id = order_id.strip()
    body: dict[str, Any] = {
        "ticker": ticker,
        "side": side.lower(),
        "action": action.lower(),
    }
    if client_order_id:
        body["client_order_id"] = client_order_id
    if updated_client_order_id:
        body["updated_client_order_id"] = updated_client_order_id
    if count is not None:
        body["count"] = count
    if yes_price is not None:
        body["yes_price"] = yes_price
    if no_price is not None:
        body["no_price"] = no_price
    if yes_price_dollars:
        body["yes_price_dollars"] = yes_price_dollars
    if no_price_dollars:
        body["no_price_dollars"] = no_price_dollars
    if count_fp:
        body["count_fp"] = count_fp

    path = f"{_API_PREFIX}/portfolio/orders/{order_id}/amend"
    try:
        headers = _build_auth_headers(key_id, private_key, "POST", path)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/portfolio/orders/{quote(order_id, safe='')}/amend",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return AmendOrderOutput(
                success=False,
                error=f"Kalshi API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        return AmendOrderOutput(success=False, error=f"Invalid Kalshi private key: {exc}")
    except httpx.TimeoutException:
        return AmendOrderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AmendOrderOutput(success=False, error=f"amend_order failed: {exc}")

    return AmendOrderOutput(
        success=True,
        old_order=_amended_order(data.get("old_order") or {}),
        order=_amended_order(data.get("order") or {}),
    )
