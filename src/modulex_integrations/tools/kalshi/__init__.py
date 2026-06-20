"""Kalshi integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""

from modulex_integrations.tools.kalshi.manifest import manifest
from modulex_integrations.tools.kalshi.tools import (
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
)

TOOLS = (
    get_markets,
    get_market,
    get_events,
    get_event,
    get_balance,
    get_positions,
    get_orders,
    get_order,
    get_orderbook,
    get_trades,
    get_candlesticks,
    get_event_candlesticks,
    get_fills,
    get_settlements,
    get_series_by_ticker,
    get_series_list,
    get_exchange_status,
    get_exchange_schedule,
    get_exchange_announcements,
    create_order,
    cancel_order,
    amend_order,
)

__all__ = [
    "TOOLS",
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
    "manifest",
]
