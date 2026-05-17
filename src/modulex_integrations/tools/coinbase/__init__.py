"""Coinbase integration."""
from modulex_integrations.tools.coinbase.manifest import manifest
from modulex_integrations.tools.coinbase.tools import (
    get_account,
    get_accounts,
    get_exchange_rates,
    get_payment_methods,
    get_spot_price,
    get_transactions,
    place_buy_order,
    withdraw_funds,
)

TOOLS = (
    get_accounts,
    get_account,
    get_transactions,
    place_buy_order,
    withdraw_funds,
    get_exchange_rates,
    get_spot_price,
    get_payment_methods,
)

__all__ = [
    "TOOLS",
    "get_account",
    "get_accounts",
    "get_exchange_rates",
    "get_payment_methods",
    "get_spot_price",
    "get_transactions",
    "manifest",
    "place_buy_order",
    "withdraw_funds",
]
