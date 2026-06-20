"""Kalshi integration manifest.

Kalshi authenticates with an API key id plus an RSA private key used to
sign each request (RSA-PSS over ``timestamp + METHOD + path``). Both
values are modeled as injected ``auth_data`` fields (``KALSHI_KEY_ID``,
``KALSHI_PRIVATE_KEY``) on a single ``ApiKeyAuthSchema``; the runtime
resolves them into the action functions as ``key_id`` / ``private_key``.

No credential ``test_endpoint`` is declared: validating a Kalshi
credential requires producing a fresh RSA-PSS signature per request,
which the declarative test-endpoint mechanism cannot synthesize.
"""

from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
)

__all__ = ["manifest"]


_AUTH_PARAMS = {
    "key_id": ParameterDef(
        type="string",
        description="Kalshi API Key ID (provided by the credential system)",
        required=True,
    ),
    "private_key": ParameterDef(
        type="string",
        description="Kalshi RSA private key in PEM format (provided by the credential system)",
        required=True,
    ),
}

_LIMIT = ParameterDef(type="integer", description="Number of results to return (1-1000)")
_CURSOR = ParameterDef(type="string", description="Pagination cursor from a previous response")


manifest = IntegrationManifest(
    name="kalshi",
    display_name="Kalshi",
    description=(
        "Access Kalshi prediction markets and trade event contracts: retrieve "
        "markets, events, series, orderbooks, trades, candlesticks, account "
        "balance, positions, orders, fills, settlements, exchange status, and "
        "place, cancel, or amend orders."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:kalshi-themed",
    app_url="https://kalshi.com",
    categories=["Finance & Payments", "prediction-markets", "data-analytics"],
    actions=[
        ActionDefinition(
            name="get_markets",
            description="Retrieve a list of prediction markets with full filtering options.",
            parameters={
                "status": ParameterDef(
                    type="string",
                    description='Filter by market status: "unopened", "open", "closed", "settled"',
                ),
                "series_ticker": ParameterDef(type="string", description="Filter by series ticker"),
                "event_ticker": ParameterDef(type="string", description="Filter by event ticker"),
                "min_created_ts": ParameterDef(
                    type="integer", description="Min created timestamp (Unix seconds)"
                ),
                "max_created_ts": ParameterDef(
                    type="integer", description="Max created timestamp (Unix seconds)"
                ),
                "min_updated_ts": ParameterDef(
                    type="integer", description="Min updated timestamp (Unix seconds)"
                ),
                "min_close_ts": ParameterDef(
                    type="integer", description="Min close timestamp (Unix seconds)"
                ),
                "max_close_ts": ParameterDef(
                    type="integer", description="Max close timestamp (Unix seconds)"
                ),
                "min_settled_ts": ParameterDef(
                    type="integer", description="Min settled timestamp (Unix seconds)"
                ),
                "max_settled_ts": ParameterDef(
                    type="integer", description="Max settled timestamp (Unix seconds)"
                ),
                "tickers": ParameterDef(
                    type="string", description="Comma-separated list of market tickers"
                ),
                "mve_filter": ParameterDef(
                    type="string", description='Multivariate event filter: "only" or "exclude"'
                ),
                "limit": _LIMIT,
                "cursor": _CURSOR,
            },
        ),
        ActionDefinition(
            name="get_market",
            description="Retrieve details of a specific prediction market by ticker.",
            parameters={
                "ticker": ParameterDef(
                    type="string",
                    description="Market ticker identifier (e.g., 'KXBTC-24DEC31')",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_events",
            description="Retrieve a list of events with optional filtering.",
            parameters={
                "status": ParameterDef(
                    type="string", description='Filter by event status: "open", "closed", "settled"'
                ),
                "series_ticker": ParameterDef(type="string", description="Filter by series ticker"),
                "with_nested_markets": ParameterDef(
                    type="string", description='Include nested markets: "true" or "false"'
                ),
                "with_milestones": ParameterDef(
                    type="string", description='Include milestones: "true" or "false"'
                ),
                "min_close_ts": ParameterDef(
                    type="integer", description="Min close timestamp (Unix seconds)"
                ),
                "limit": ParameterDef(
                    type="integer", description="Number of results to return (1-200)"
                ),
                "cursor": _CURSOR,
            },
        ),
        ActionDefinition(
            name="get_event",
            description="Retrieve details of a specific event by ticker.",
            parameters={
                "event_ticker": ParameterDef(
                    type="string", description="Event ticker identifier", required=True
                ),
                "with_nested_markets": ParameterDef(
                    type="string", description='Include nested markets: "true" or "false"'
                ),
            },
        ),
        ActionDefinition(
            name="get_balance",
            description="Retrieve your account balance and portfolio value.",
            parameters=dict(_AUTH_PARAMS),
        ),
        ActionDefinition(
            name="get_positions",
            description="Retrieve your open positions.",
            parameters={
                **_AUTH_PARAMS,
                "ticker": ParameterDef(type="string", description="Filter by market ticker"),
                "event_ticker": ParameterDef(
                    type="string", description="Filter by event ticker (max 10, comma-separated)"
                ),
                "count_filter": ParameterDef(
                    type="string",
                    description='Comma-separated non-zero fields: position, total_traded',
                ),
                "subaccount": ParameterDef(type="string", description="Subaccount identifier"),
                "limit": _LIMIT,
                "cursor": _CURSOR,
            },
        ),
        ActionDefinition(
            name="get_orders",
            description="Retrieve your orders with optional filtering.",
            parameters={
                **_AUTH_PARAMS,
                "ticker": ParameterDef(type="string", description="Filter by market ticker"),
                "event_ticker": ParameterDef(
                    type="string", description="Filter by event ticker (max 10, comma-separated)"
                ),
                "status": ParameterDef(
                    type="string", description='Filter by status: "resting", "canceled", "executed"'
                ),
                "min_ts": ParameterDef(
                    type="string", description="Minimum timestamp filter (Unix timestamp)"
                ),
                "max_ts": ParameterDef(
                    type="string", description="Maximum timestamp filter (Unix timestamp)"
                ),
                "subaccount": ParameterDef(type="string", description="Subaccount identifier"),
                "limit": _LIMIT,
                "cursor": _CURSOR,
            },
        ),
        ActionDefinition(
            name="get_order",
            description="Retrieve details of a specific order by ID.",
            parameters={
                **_AUTH_PARAMS,
                "order_id": ParameterDef(
                    type="string", description="Order ID to retrieve", required=True
                ),
            },
        ),
        ActionDefinition(
            name="get_orderbook",
            description="Retrieve the orderbook (yes and no bids) for a specific market.",
            parameters={
                "ticker": ParameterDef(
                    type="string", description="Market ticker identifier", required=True
                ),
                "depth": ParameterDef(
                    type="integer", description="Number of price levels to return"
                ),
            },
        ),
        ActionDefinition(
            name="get_trades",
            description="Retrieve recent public trades across markets with optional filtering.",
            parameters={
                "ticker": ParameterDef(type="string", description="Filter by market ticker"),
                "min_ts": ParameterDef(
                    type="integer", description="Minimum timestamp (Unix seconds)"
                ),
                "max_ts": ParameterDef(
                    type="integer", description="Maximum timestamp (Unix seconds)"
                ),
                "limit": _LIMIT,
                "cursor": _CURSOR,
            },
        ),
        ActionDefinition(
            name="get_candlesticks",
            description="Retrieve OHLC candlestick data for a specific market.",
            parameters={
                "series_ticker": ParameterDef(
                    type="string", description="Series ticker identifier", required=True
                ),
                "ticker": ParameterDef(
                    type="string", description="Market ticker identifier", required=True
                ),
                "start_ts": ParameterDef(
                    type="integer", description="Start timestamp (Unix seconds)", required=True
                ),
                "end_ts": ParameterDef(
                    type="integer", description="End timestamp (Unix seconds)", required=True
                ),
                "period_interval": ParameterDef(
                    type="integer",
                    description="Period interval: 1 (minute), 60 (hour), 1440 (day)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_event_candlesticks",
            description="Retrieve OHLC candlestick data aggregated across all markets in an event.",
            parameters={
                "series_ticker": ParameterDef(
                    type="string", description="Series ticker identifier", required=True
                ),
                "event_ticker": ParameterDef(
                    type="string", description="Event ticker identifier", required=True
                ),
                "start_ts": ParameterDef(
                    type="integer", description="Start timestamp (Unix seconds)", required=True
                ),
                "end_ts": ParameterDef(
                    type="integer", description="End timestamp (Unix seconds)", required=True
                ),
                "period_interval": ParameterDef(
                    type="integer",
                    description="Period interval: 1 (minute), 60 (hour), 1440 (day)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_fills",
            description="Retrieve your portfolio's fills/trades.",
            parameters={
                **_AUTH_PARAMS,
                "ticker": ParameterDef(type="string", description="Filter by market ticker"),
                "order_id": ParameterDef(type="string", description="Filter by order ID"),
                "min_ts": ParameterDef(
                    type="integer", description="Minimum timestamp (Unix seconds)"
                ),
                "max_ts": ParameterDef(
                    type="integer", description="Maximum timestamp (Unix seconds)"
                ),
                "subaccount": ParameterDef(type="string", description="Subaccount identifier"),
                "limit": _LIMIT,
                "cursor": _CURSOR,
            },
        ),
        ActionDefinition(
            name="get_settlements",
            description="Retrieve your portfolio settlement history.",
            parameters={
                **_AUTH_PARAMS,
                "ticker": ParameterDef(type="string", description="Filter by market ticker"),
                "event_ticker": ParameterDef(type="string", description="Filter by event ticker"),
                "min_ts": ParameterDef(
                    type="integer", description="Min settled timestamp (Unix seconds)"
                ),
                "max_ts": ParameterDef(
                    type="integer", description="Max settled timestamp (Unix seconds)"
                ),
                "subaccount": ParameterDef(
                    type="string", description="Subaccount number (0 primary, 1-63)"
                ),
                "limit": _LIMIT,
                "cursor": _CURSOR,
            },
        ),
        ActionDefinition(
            name="get_series_by_ticker",
            description="Retrieve details of a specific market series by ticker.",
            parameters={
                "series_ticker": ParameterDef(
                    type="string", description="Series ticker identifier", required=True
                ),
                "include_volume": ParameterDef(
                    type="string", description='Include volume data: "true" or "false"'
                ),
            },
        ),
        ActionDefinition(
            name="get_series_list",
            description="Retrieve a list of market series with optional filtering.",
            parameters={
                "category": ParameterDef(type="string", description="Filter by category"),
                "tags": ParameterDef(type="string", description="Filter by comma-separated tags"),
                "include_product_metadata": ParameterDef(
                    type="string", description='Include product metadata: "true" or "false"'
                ),
                "include_volume": ParameterDef(
                    type="string", description='Include volume data: "true" or "false"'
                ),
                "min_updated_ts": ParameterDef(
                    type="integer", description="Min updated timestamp (Unix seconds)"
                ),
            },
        ),
        ActionDefinition(
            name="get_exchange_status",
            description="Retrieve the current status of the Kalshi exchange.",
        ),
        ActionDefinition(
            name="get_exchange_schedule",
            description="Retrieve the exchange trading schedule and maintenance windows.",
        ),
        ActionDefinition(
            name="get_exchange_announcements",
            description="Retrieve exchange-wide announcements.",
        ),
        ActionDefinition(
            name="create_order",
            description="Create a new order on a Kalshi prediction market.",
            parameters={
                **_AUTH_PARAMS,
                "ticker": ParameterDef(
                    type="string", description="Market ticker identifier", required=True
                ),
                "side": ParameterDef(
                    type="string", description='Order side: "yes" or "no"', required=True
                ),
                "action": ParameterDef(
                    type="string", description='Action type: "buy" or "sell"', required=True
                ),
                "count": ParameterDef(
                    type="integer",
                    description="Number of contracts to trade (provide count or count_fp)",
                ),
                "type": ParameterDef(
                    type="string", description='Order type: "limit" or "market" (default "limit")'
                ),
                "yes_price": ParameterDef(type="integer", description="Yes price in cents (1-99)"),
                "no_price": ParameterDef(type="integer", description="No price in cents (1-99)"),
                "yes_price_dollars": ParameterDef(
                    type="string", description="Yes price in dollars (e.g., '0.56')"
                ),
                "no_price_dollars": ParameterDef(
                    type="string", description="No price in dollars (e.g., '0.56')"
                ),
                "client_order_id": ParameterDef(
                    type="string", description="Custom order identifier"
                ),
                "expiration_ts": ParameterDef(
                    type="integer", description="Unix timestamp for order expiration"
                ),
                "time_in_force": ParameterDef(
                    type="string",
                    description="TIF: fill_or_kill / good_till_canceled / immediate_or_cancel",
                ),
                "buy_max_cost": ParameterDef(
                    type="integer", description="Maximum cost in cents (auto-enables fill_or_kill)"
                ),
                "post_only": ParameterDef(type="boolean", description="Maker-only order"),
                "reduce_only": ParameterDef(type="boolean", description="Position reduction only"),
                "self_trade_prevention_type": ParameterDef(
                    type="string", description="Self-trade prevention: 'taker_at_cross' or 'maker'"
                ),
                "order_group_id": ParameterDef(
                    type="string", description="Associated order group ID"
                ),
                "count_fp": ParameterDef(
                    type="string", description="Count in fixed-point for fractional contracts"
                ),
                "cancel_order_on_pause": ParameterDef(
                    type="boolean", description="Cancel order on market pause"
                ),
                "subaccount": ParameterDef(
                    type="string", description="Subaccount to use for the order"
                ),
            },
        ),
        ActionDefinition(
            name="cancel_order",
            description="Cancel an existing order.",
            parameters={
                **_AUTH_PARAMS,
                "order_id": ParameterDef(
                    type="string", description="Order ID to cancel", required=True
                ),
            },
        ),
        ActionDefinition(
            name="amend_order",
            description="Modify the price or quantity of an existing order.",
            parameters={
                **_AUTH_PARAMS,
                "order_id": ParameterDef(
                    type="string", description="Order ID to amend", required=True
                ),
                "ticker": ParameterDef(
                    type="string", description="Market ticker identifier", required=True
                ),
                "side": ParameterDef(
                    type="string", description='Order side: "yes" or "no"', required=True
                ),
                "action": ParameterDef(
                    type="string", description='Action type: "buy" or "sell"', required=True
                ),
                "client_order_id": ParameterDef(
                    type="string", description="Original client-specified order ID"
                ),
                "updated_client_order_id": ParameterDef(
                    type="string", description="New client-specified order ID"
                ),
                "count": ParameterDef(type="integer", description="Updated quantity for the order"),
                "yes_price": ParameterDef(
                    type="integer", description="Updated yes price in cents (1-99)"
                ),
                "no_price": ParameterDef(
                    type="integer", description="Updated no price in cents (1-99)"
                ),
                "yes_price_dollars": ParameterDef(
                    type="string", description="Updated yes price in dollars"
                ),
                "no_price_dollars": ParameterDef(
                    type="string", description="Updated no price in dollars"
                ),
                "count_fp": ParameterDef(
                    type="string", description="Count in fixed-point for fractional contracts"
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description=(
                "Authenticate with a Kalshi API key id and its RSA private key. "
                "Each request is signed with the private key (RSA-PSS over "
                "SHA-256); the signing material never leaves the runtime."
            ),
            setup_instructions=[
                "Sign in at https://kalshi.com and open Account → API Keys.",
                "Create a new API key; download the RSA private key (PEM) and copy the Key ID.",
                "Paste the Key ID into KALSHI_KEY_ID below.",
                "Paste the full PEM private key into KALSHI_PRIVATE_KEY below.",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="KALSHI_KEY_ID",
                    display_name="API Key ID",
                    description="Your Kalshi API Key ID from Account → API Keys",
                    required=True,
                    sensitive=False,
                    inject_into_auth_data=True,
                    about_url="https://docs.kalshi.com/getting_started/api_keys",
                ),
                EnvVar(
                    name="KALSHI_PRIVATE_KEY",
                    display_name="RSA Private Key (PEM)",
                    description="Your Kalshi RSA private key in PEM format",
                    required=True,
                    sensitive=True,
                    inject_into_auth_data=True,
                    sample_format="-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----",
                    about_url="https://docs.kalshi.com/getting_started/api_keys",
                ),
            ],
        ),
    ],
)
