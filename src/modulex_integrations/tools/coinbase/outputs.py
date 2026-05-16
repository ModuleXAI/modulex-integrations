"""Pydantic response models for the Coinbase integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AccountRow",
    "GetAccountOutput",
    "GetAccountsOutput",
    "GetExchangeRatesOutput",
    "GetPaymentMethodsOutput",
    "GetSpotPriceOutput",
    "GetTransactionsOutput",
    "PaymentMethodRow",
    "PlaceBuyOrderOutput",
    "TransactionRow",
    "WithdrawFundsOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class AccountRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    uuid: str | None = None
    name: str | None = None
    type: str | None = None
    currency: str | None = None
    available_balance: str | None = None
    available_balance_currency: str | None = None
    hold_balance: str | None = None
    hold_balance_currency: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    active: bool | None = None
    ready: bool | None = None
    default: bool | None = None


class GetAccountsOutput(_Base):
    accounts: list[AccountRow] = Field(default_factory=list)
    total: int = 0
    has_next: bool | None = None
    cursor: str | None = None


class GetAccountOutput(_Base):
    account: AccountRow | None = None


class TransactionRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entry_id: str | None = None
    trade_id: str | None = None
    order_id: str | None = None
    trade_time: str | None = None
    trade_type: str | None = None
    price: str | None = None
    size: str | None = None
    commission: str | None = None
    product_id: str | None = None
    sequence_timestamp: str | None = None
    liquidity_indicator: str | None = None
    size_in_quote: bool | None = None
    user_id: str | None = None
    side: str | None = None


class GetTransactionsOutput(_Base):
    transactions: list[TransactionRow] = Field(default_factory=list)
    total: int = 0
    cursor: str | None = None


class _OrderInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: str | None = None
    product_id: str | None = None
    side: str | None = None
    client_order_id: str | None = None


class PlaceBuyOrderOutput(_Base):
    order: _OrderInfo | None = None


class WithdrawFundsOutput(_Base):
    id: str | None = None
    status: str | None = None
    amount: str | None = None
    asset: str | None = None
    fee: str | None = None
    transaction_hash: str | None = None
    destination_address: str | None = None
    network: str | None = None
    created_at: str | None = None


class GetExchangeRatesOutput(_Base):
    currency: str | None = None
    rates: dict[str, Any] = Field(default_factory=dict)


class GetSpotPriceOutput(_Base):
    base: str | None = None
    currency: str | None = None
    amount: str | None = None


class PaymentMethodRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str | None = None
    type: str | None = None
    name: str | None = None
    currency: str | None = None
    allow_buy: bool | None = None
    allow_sell: bool | None = None
    allow_deposit: bool | None = None
    allow_withdraw: bool | None = None
    verified: bool | None = None


class GetPaymentMethodsOutput(_Base):
    payment_methods: list[PaymentMethodRow] = Field(default_factory=list)
    total: int = 0
