"""Pydantic response models for the Kalshi integration's @tool functions.

Kalshi authenticates each request with an RSA-PSS request signature
(see ``tools.py``). The runtime injects the signing material
(``key_id`` + ``private_key``) into the action functions. Every output
model carries ``success: bool`` + ``error: str | None`` so both the
happy path and the failure path share one shape.

Field types follow the documented Kalshi Trade API v2 response shapes,
kept permissive (every scalar ``<type> | None = None``, every list
``Field(default_factory=list)``) because the upstream API omits many
fields depending on the market/order state.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AmendOrderOutput",
    "BidAskDistribution",
    "CancelOrderOutput",
    "CreateOrderOutput",
    "Event",
    "EventCandlestick",
    "EventPosition",
    "ExchangeSchedule",
    "GetBalanceOutput",
    "GetCandlesticksOutput",
    "GetEventCandlesticksOutput",
    "GetEventOutput",
    "GetEventsOutput",
    "GetExchangeAnnouncementsOutput",
    "GetExchangeScheduleOutput",
    "GetExchangeStatusOutput",
    "GetFillsOutput",
    "GetMarketOutput",
    "GetMarketsOutput",
    "GetOrderOutput",
    "GetOrderbookOutput",
    "GetOrdersOutput",
    "GetPositionsOutput",
    "GetSeriesByTickerOutput",
    "GetSeriesListOutput",
    "GetSettlementsOutput",
    "GetTradesOutput",
    "Market",
    "MarketCandlestick",
    "MarketPosition",
    "Milestone",
    "Order",
    "Orderbook",
    "OrderbookFp",
    "PriceDistribution",
    "Series",
    "SettlementSource",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class Market(_Base):
    """A single market row (Trade API v2 shape)."""

    ticker: str | None = None
    event_ticker: str | None = None
    market_type: str | None = None
    title: str | None = None
    subtitle: str | None = None
    yes_sub_title: str | None = None
    no_sub_title: str | None = None
    open_time: str | None = None
    close_time: str | None = None
    expected_expiration_time: str | None = None
    expiration_time: str | None = None
    latest_expiration_time: str | None = None
    settlement_timer_seconds: int | None = None
    status: str | None = None
    response_price_units: str | None = None
    notional_value: int | None = None
    tick_size: int | None = None
    yes_bid: int | None = None
    yes_ask: int | None = None
    no_bid: int | None = None
    no_ask: int | None = None
    last_price: int | None = None
    previous_yes_bid: int | None = None
    previous_yes_ask: int | None = None
    previous_price: int | None = None
    volume: int | None = None
    volume_24h: int | None = None
    liquidity: int | None = None
    open_interest: int | None = None
    result: str | None = None
    cap_strike: float | None = None
    floor_strike: float | None = None
    can_close_early: bool | None = None
    expiration_value: str | None = None
    category: str | None = None
    risk_limit_cents: int | None = None
    strike_type: str | None = None
    rules_primary: str | None = None
    rules_secondary: str | None = None
    settlement_source_url: str | None = None
    custom_strike: dict[str, Any] | None = None
    underlying: str | None = None
    settlement_value: int | None = None
    cfd_contract_size: int | None = None
    yes_fee_fp: int | None = None
    no_fee_fp: int | None = None
    last_price_fp: int | None = None
    yes_bid_fp: int | None = None
    yes_ask_fp: int | None = None
    no_bid_fp: int | None = None
    no_ask_fp: int | None = None


class Milestone(_Base):
    """An event milestone (returned by get_events when requested)."""

    id: str | None = None
    category: str | None = None
    type: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    notification_message: str | None = None
    primary_event_tickers: list[str] = Field(default_factory=list)
    related_event_tickers: list[str] = Field(default_factory=list)
    last_updated_ts: str | None = None


class Event(_Base):
    """An event row (Trade API v2 shape)."""

    event_ticker: str | None = None
    series_ticker: str | None = None
    title: str | None = None
    sub_title: str | None = None
    mutually_exclusive: bool | None = None
    category: str | None = None
    collateral_return_type: str | None = None
    strike_date: str | None = None
    strike_period: str | None = None
    available_on_brokers: bool | None = None
    product_metadata: dict[str, Any] | None = None
    markets: list[dict[str, Any]] = Field(default_factory=list)


class Order(_Base):
    """An order row (Trade API v2 portfolio order shape)."""

    order_id: str | None = None
    user_id: str | None = None
    client_order_id: str | None = None
    ticker: str | None = None
    side: str | None = None
    action: str | None = None
    type: str | None = None
    status: str | None = None
    yes_price: int | None = None
    no_price: int | None = None
    yes_price_dollars: str | None = None
    no_price_dollars: str | None = None
    fill_count: int | None = None
    fill_count_fp: str | None = None
    remaining_count: int | None = None
    remaining_count_fp: str | None = None
    initial_count: int | None = None
    initial_count_fp: str | None = None
    taker_fees: int | None = None
    maker_fees: int | None = None
    taker_fees_dollars: str | None = None
    maker_fees_dollars: str | None = None
    taker_fill_cost: int | None = None
    maker_fill_cost: int | None = None
    taker_fill_cost_dollars: str | None = None
    maker_fill_cost_dollars: str | None = None
    queue_position: int | None = None
    expiration_time: str | None = None
    created_time: str | None = None
    last_update_time: str | None = None
    self_trade_prevention_type: str | None = None
    order_group_id: str | None = None
    cancel_order_on_pause: bool | None = None


class AmendedOrder(_Base):
    """The order shape returned by the amend endpoint (old_order/order)."""

    order_id: str | None = None
    user_id: str | None = None
    ticker: str | None = None
    event_ticker: str | None = None
    status: str | None = None
    side: str | None = None
    type: str | None = None
    yes_price: int | None = None
    no_price: int | None = None
    action: str | None = None
    count: int | None = None
    remaining_count: int | None = None
    created_time: str | None = None
    expiration_time: str | None = None
    order_group_id: str | None = None
    client_order_id: str | None = None
    place_count: int | None = None
    decrease_count: int | None = None
    queue_position: int | None = None
    maker_fill_count: int | None = None
    taker_fill_count: int | None = None
    maker_fees: int | None = None
    taker_fees: int | None = None
    last_update_time: str | None = None
    take_profit_order_id: str | None = None
    stop_loss_order_id: str | None = None
    amend_count: int | None = None
    amend_taker_fill_count: int | None = None


class MarketPosition(_Base):
    ticker: str | None = None
    event_ticker: str | None = None
    event_title: str | None = None
    market_title: str | None = None
    position: int | None = None
    market_exposure: int | None = None
    realized_pnl: int | None = None
    total_traded: int | None = None
    resting_orders_count: int | None = None
    fees_paid: int | None = None


class EventPosition(_Base):
    event_ticker: str | None = None
    event_exposure: int | None = None
    realized_pnl: int | None = None
    total_cost: int | None = None


class Fill(_Base):
    fill_id: str | None = None
    trade_id: str | None = None
    order_id: str | None = None
    client_order_id: str | None = None
    ticker: str | None = None
    market_ticker: str | None = None
    side: str | None = None
    action: str | None = None
    count: int | None = None
    count_fp: str | None = None
    price: int | None = None
    yes_price: int | None = None
    no_price: int | None = None
    yes_price_fixed: str | None = None
    no_price_fixed: str | None = None
    is_taker: bool | None = None
    created_time: str | None = None
    ts: int | None = None


class Trade(_Base):
    trade_id: str | None = None
    ticker: str | None = None
    yes_price: int | None = None
    no_price: int | None = None
    count: int | None = None
    count_fp: int | None = None
    created_time: str | None = None
    taker_side: str | None = None


class Settlement(_Base):
    ticker: str | None = None
    event_ticker: str | None = None
    market_result: str | None = None
    yes_count_fp: str | None = None
    yes_total_cost_dollars: str | None = None
    no_count_fp: str | None = None
    no_total_cost_dollars: str | None = None
    revenue: int | None = None
    settled_time: str | None = None
    fee_cost: str | None = None
    value: int | None = None


class SettlementSource(_Base):
    name: str | None = None
    url: str | None = None


class Series(_Base):
    ticker: str | None = None
    title: str | None = None
    frequency: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    settlement_sources: list[SettlementSource] = Field(default_factory=list)
    contract_url: str | None = None
    contract_terms_url: str | None = None
    fee_type: str | None = None
    fee_multiplier: float | None = None
    additional_prohibitions: list[str] = Field(default_factory=list)
    product_metadata: dict[str, Any] | None = None
    volume: int | None = None
    volume_fp: float | None = None
    last_updated_ts: str | None = None


class Announcement(_Base):
    type: str | None = None
    message: str | None = None
    delivery_time: str | None = None
    status: str | None = None


class BidAskDistribution(_Base):
    open: int | None = None
    open_dollars: str | None = None
    low: int | None = None
    low_dollars: str | None = None
    high: int | None = None
    high_dollars: str | None = None
    close: int | None = None
    close_dollars: str | None = None


class PriceDistribution(_Base):
    open: int | None = None
    open_dollars: str | None = None
    low: int | None = None
    low_dollars: str | None = None
    high: int | None = None
    high_dollars: str | None = None
    close: int | None = None
    close_dollars: str | None = None
    mean: int | None = None
    mean_dollars: str | None = None
    previous: int | None = None
    previous_dollars: str | None = None
    min: int | None = None
    min_dollars: str | None = None
    max: int | None = None
    max_dollars: str | None = None


class MarketCandlestick(_Base):
    end_period_ts: int | None = None
    yes_bid: BidAskDistribution | None = None
    yes_ask: BidAskDistribution | None = None
    price: PriceDistribution | None = None
    volume: int | None = None
    volume_fp: str | None = None
    open_interest: int | None = None
    open_interest_fp: str | None = None


class EventCandlestick(_Base):
    end_period_ts: int | None = None
    yes_bid: BidAskDistribution | None = None
    yes_ask: BidAskDistribution | None = None
    price: PriceDistribution | None = None
    volume_fp: str | None = None
    open_interest_fp: str | None = None


class Orderbook(_Base):
    # Tuple arrays: [price_in_cents, count] / [dollars_string, count].
    yes: list[list[Any]] = Field(default_factory=list)
    no: list[list[Any]] = Field(default_factory=list)
    yes_dollars: list[list[Any]] = Field(default_factory=list)
    no_dollars: list[list[Any]] = Field(default_factory=list)


class OrderbookFp(_Base):
    yes_dollars: list[list[Any]] = Field(default_factory=list)
    no_dollars: list[list[Any]] = Field(default_factory=list)


class ExchangeSchedule(_Base):
    standard_hours: list[dict[str, Any]] = Field(default_factory=list)
    maintenance_windows: list[dict[str, Any]] = Field(default_factory=list)


# --- Per-action output models ---------------------------------------------


class GetMarketsOutput(_Base):
    success: bool
    error: str | None = None
    markets: list[Market] = Field(default_factory=list)
    cursor: str | None = None


class GetMarketOutput(_Base):
    success: bool
    error: str | None = None
    market: Market | None = None


class GetEventsOutput(_Base):
    success: bool
    error: str | None = None
    events: list[Event] = Field(default_factory=list)
    milestones: list[Milestone] = Field(default_factory=list)
    cursor: str | None = None


class GetEventOutput(_Base):
    success: bool
    error: str | None = None
    event: Event | None = None


class GetBalanceOutput(_Base):
    success: bool
    error: str | None = None
    balance: int | None = None
    portfolio_value: int | None = None
    updated_ts: int | None = None


class GetPositionsOutput(_Base):
    success: bool
    error: str | None = None
    market_positions: list[MarketPosition] = Field(default_factory=list)
    event_positions: list[EventPosition] = Field(default_factory=list)
    cursor: str | None = None


class GetOrdersOutput(_Base):
    success: bool
    error: str | None = None
    orders: list[Order] = Field(default_factory=list)
    cursor: str | None = None


class GetOrderOutput(_Base):
    success: bool
    error: str | None = None
    order: Order | None = None


class GetOrderbookOutput(_Base):
    success: bool
    error: str | None = None
    orderbook: Orderbook | None = None
    orderbook_fp: OrderbookFp | None = None


class GetTradesOutput(_Base):
    success: bool
    error: str | None = None
    trades: list[Trade] = Field(default_factory=list)
    cursor: str | None = None


class GetCandlesticksOutput(_Base):
    success: bool
    error: str | None = None
    ticker: str | None = None
    candlesticks: list[MarketCandlestick] = Field(default_factory=list)


class GetEventCandlesticksOutput(_Base):
    success: bool
    error: str | None = None
    market_tickers: list[str] = Field(default_factory=list)
    adjusted_end_ts: int | None = None
    market_candlesticks: list[EventCandlestick] = Field(default_factory=list)


class GetFillsOutput(_Base):
    success: bool
    error: str | None = None
    fills: list[Fill] = Field(default_factory=list)
    cursor: str | None = None


class GetSettlementsOutput(_Base):
    success: bool
    error: str | None = None
    settlements: list[Settlement] = Field(default_factory=list)
    cursor: str | None = None


class GetSeriesByTickerOutput(_Base):
    success: bool
    error: str | None = None
    series: Series | None = None


class GetSeriesListOutput(_Base):
    success: bool
    error: str | None = None
    series: list[Series] = Field(default_factory=list)


class GetExchangeStatusOutput(_Base):
    success: bool
    error: str | None = None
    exchange_active: bool | None = None
    trading_active: bool | None = None
    exchange_estimated_resume_time: str | None = None


class GetExchangeScheduleOutput(_Base):
    success: bool
    error: str | None = None
    schedule: ExchangeSchedule | None = None


class GetExchangeAnnouncementsOutput(_Base):
    success: bool
    error: str | None = None
    announcements: list[Announcement] = Field(default_factory=list)


class CreateOrderOutput(_Base):
    success: bool
    error: str | None = None
    order: Order | None = None


class CancelOrderOutput(_Base):
    success: bool
    error: str | None = None
    order: Order | None = None
    reduced_by: int | None = None
    reduced_by_fp: str | None = None


class AmendOrderOutput(_Base):
    success: bool
    error: str | None = None
    old_order: AmendedOrder | None = None
    order: AmendedOrder | None = None
