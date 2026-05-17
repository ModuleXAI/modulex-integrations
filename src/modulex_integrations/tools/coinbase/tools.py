"""Coinbase LangChain ``@tool`` functions.

Coinbase Developer Platform (CDP) authenticates via short-lived JWTs
signed with either Ed25519 (base64-encoded seed) or ECDSA P-256 (PEM).
Signing happens locally — the runtime hands us the key pair through
``auth_data`` and we mint a fresh JWT per request.

Runtime convention: token-based (``auth_type, auth_data`` first args).
``auth_type`` is the modulex schema label (``custom``); the tool body
ignores it and reads ``api_key`` / ``api_secret`` straight out of
``auth_data``.
"""
from __future__ import annotations

import base64
import json
import secrets
import time
import uuid
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.coinbase.outputs import (
    AccountRow,
    GetAccountOutput,
    GetAccountsOutput,
    GetExchangeRatesOutput,
    GetPaymentMethodsOutput,
    GetSpotPriceOutput,
    GetTransactionsOutput,
    PaymentMethodRow,
    PlaceBuyOrderOutput,
    TransactionRow,
    WithdrawFundsOutput,
    _OrderInfo,
)

__all__ = [
    "generate_jwt",
    "get_account",
    "get_accounts",
    "get_exchange_rates",
    "get_payment_methods",
    "get_spot_price",
    "get_transactions",
    "place_buy_order",
    "withdraw_funds",
]

_API_V2 = "https://api.coinbase.com/v2"
_API_V3 = "https://api.coinbase.com/api/v3/brokerage"
_API_HOST = "api.coinbase.com"
_TIMEOUT = 30.0


# --- JWT signing (Ed25519 + ECDSA) ----------------------------------------


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _sign_ecdsa(header: dict[str, Any], payload: dict[str, Any], pem: str) -> str:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    header_b64 = _b64url(json.dumps(header).encode())
    payload_b64 = _b64url(json.dumps(payload).encode())
    message = f"{header_b64}.{payload_b64}"

    key = load_pem_private_key(
        pem.replace("\\n", "\n").encode(), password=None, backend=default_backend()
    )
    if not isinstance(key, ec.EllipticCurvePrivateKey):
        raise ValueError(
            f"Expected ECDSA private key for Coinbase ES256, got {type(key).__name__}"
        )
    der = key.sign(message.encode(), ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    raw = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return f"{message}.{_b64url(raw)}"


def _sign_ed25519(header: dict[str, Any], payload: dict[str, Any], b64: str) -> str:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    header_b64 = _b64url(json.dumps(header).encode())
    payload_b64 = _b64url(json.dumps(payload).encode())
    message = f"{header_b64}.{payload_b64}"

    decoded = base64.b64decode(b64)
    if len(decoded) != 64:
        raise ValueError(f"Invalid Ed25519 key length: {len(decoded)}")
    key = Ed25519PrivateKey.from_private_bytes(decoded[:32])
    return f"{message}.{_b64url(key.sign(message.encode()))}"


def generate_jwt(
    api_key_id: str, api_key_secret: str, method: str, path: str
) -> str:
    """Mint a Coinbase CDP JWT (Ed25519 unless the secret looks like a PEM)."""
    is_pem = (
        "BEGIN EC PRIVATE KEY" in api_key_secret
        or "BEGIN PRIVATE KEY" in api_key_secret
    )
    now = int(time.time())
    header: dict[str, Any] = {
        "typ": "JWT",
        "kid": api_key_id,
        "nonce": secrets.token_hex(16),
    }
    payload: dict[str, Any] = {
        "sub": api_key_id,
        "iss": "cdp",
        "aud": ["cdp_service"],
        "nbf": now,
        "exp": now + 120,
        "uri": f"{method.upper()} {_API_HOST}{path}",
    }
    if is_pem:
        header["alg"] = "ES256"
        return _sign_ecdsa(header, payload, api_key_secret)
    header["alg"] = "EdDSA"
    return _sign_ed25519(header, payload, api_key_secret)


def _headers(
    auth_data: dict[str, Any], method: str, path: str
) -> tuple[dict[str, str], str | None]:
    api_key = auth_data.get("api_key", "")
    api_secret = auth_data.get("api_secret", "")
    if not api_key or not api_secret:
        return {}, "Coinbase api_key + api_secret are required"
    try:
        jwt = generate_jwt(api_key, api_secret, method, path)
    except Exception as exc:
        return {}, f"JWT signing failed: {exc}"
    return (
        {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        None,
    )


def _api_err(status: int, body: str) -> str:
    return f"API error: {status} - {body}"


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (custom)")
    auth_data: dict[str, Any] = Field(
        description="Auth data carrying api_key + api_secret"
    )


class GetAccountsInput(_AuthFields):
    limit: int = Field(default=25, description="Maximum accounts (1-100)")


class GetAccountInput(_AuthFields):
    account_id: str = Field(description="Account ID")


class GetTransactionsInput(_AuthFields):
    account_id: str = Field(description="Account ID")
    limit: int = Field(default=25)
    starting_after: str | None = Field(default=None, description="Pagination cursor")


class PlaceBuyOrderInput(_AuthFields):
    account_id: str = Field(description="Account ID")
    amount: str = Field(description="Quote-currency spend (USD)")
    currency: str = Field(description="Base currency (e.g. 'BTC')")
    payment_method: str | None = Field(default=None)


class WithdrawFundsInput(_AuthFields):
    account_id: str = Field(description="Account ID")
    amount: str = Field(description="Amount to withdraw")
    currency: str = Field(description="Currency / asset")
    payment_method: str = Field(description="Destination address")


class GetExchangeRatesInput(_AuthFields):
    currency: str = Field(default="USD", description="Base currency")


class GetSpotPriceInput(_AuthFields):
    currency_pair: str = Field(description="e.g. 'BTC-USD'")


class GetPaymentMethodsInput(_AuthFields):
    pass


# --- Helpers ---------------------------------------------------------------


def _account_row(account: dict[str, Any]) -> AccountRow:
    avail = account.get("available_balance") or {}
    hold = account.get("hold") or {}
    return AccountRow(
        uuid=account.get("uuid"),
        name=account.get("name"),
        type=account.get("type"),
        currency=account.get("currency"),
        available_balance=avail.get("value"),
        available_balance_currency=avail.get("currency"),
        hold_balance=hold.get("value"),
        hold_balance_currency=hold.get("currency"),
        created_at=account.get("created_at"),
        updated_at=account.get("updated_at"),
        active=account.get("active"),
        ready=account.get("ready"),
        default=account.get("default"),
    )


# --- Tools -----------------------------------------------------------------


@tool(args_schema=GetAccountsInput)
@serialize_pydantic_return
async def get_accounts(
    auth_type: str, auth_data: dict[str, Any], limit: int = 25
) -> GetAccountsOutput:
    """List all cryptocurrency accounts (wallets)."""
    path = "/api/v3/brokerage/accounts"
    headers, err = _headers(auth_data, "GET", path)
    if err:
        return GetAccountsOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_V3}/accounts", headers=headers, params={"limit": limit}
            )
        if response.status_code != 200:
            return GetAccountsOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
    except Exception as exc:
        return GetAccountsOutput(success=False, error=str(exc))
    rows = [_account_row(a) for a in data.get("accounts") or []]
    return GetAccountsOutput(
        success=True,
        accounts=rows,
        total=len(rows),
        has_next=data.get("has_next"),
        cursor=data.get("cursor"),
    )


@tool(args_schema=GetAccountInput)
@serialize_pydantic_return
async def get_account(
    auth_type: str, auth_data: dict[str, Any], account_id: str
) -> GetAccountOutput:
    """Get details for a specific Coinbase account."""
    path = f"/api/v3/brokerage/accounts/{account_id}"
    headers, err = _headers(auth_data, "GET", path)
    if err:
        return GetAccountOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_API_V3}/accounts/{account_id}", headers=headers)
        if response.status_code != 200:
            return GetAccountOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
    except Exception as exc:
        return GetAccountOutput(success=False, error=str(exc))
    return GetAccountOutput(
        success=True, account=_account_row(data.get("account") or {})
    )


@tool(args_schema=GetTransactionsInput)
@serialize_pydantic_return
async def get_transactions(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    limit: int = 25,
    starting_after: str | None = None,
) -> GetTransactionsOutput:
    """List order fills (Coinbase's v3 equivalent of transactions)."""
    path = "/api/v3/brokerage/orders/historical/fills"
    headers, err = _headers(auth_data, "GET", path)
    if err:
        return GetTransactionsOutput(success=False, error=err)
    params: dict[str, Any] = {"limit": limit}
    if starting_after:
        params["cursor"] = starting_after
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_V3}/orders/historical/fills", headers=headers, params=params
            )
        if response.status_code != 200:
            return GetTransactionsOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
    except Exception as exc:
        return GetTransactionsOutput(success=False, error=str(exc))
    rows = [
        TransactionRow(
            entry_id=f.get("entry_id"),
            trade_id=f.get("trade_id"),
            order_id=f.get("order_id"),
            trade_time=f.get("trade_time"),
            trade_type=f.get("trade_type"),
            price=f.get("price"),
            size=f.get("size"),
            commission=f.get("commission"),
            product_id=f.get("product_id"),
            sequence_timestamp=f.get("sequence_timestamp"),
            liquidity_indicator=f.get("liquidity_indicator"),
            size_in_quote=f.get("size_in_quote"),
            user_id=f.get("user_id"),
            side=f.get("side"),
        )
        for f in data.get("fills") or []
    ]
    return GetTransactionsOutput(
        success=True, transactions=rows, total=len(rows), cursor=data.get("cursor")
    )


@tool(args_schema=PlaceBuyOrderInput)
@serialize_pydantic_return
async def place_buy_order(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    amount: str,
    currency: str,
    payment_method: str | None = None,
) -> PlaceBuyOrderOutput:
    """Place a market buy order (immediate-or-cancel)."""
    path = "/api/v3/brokerage/orders"
    headers, err = _headers(auth_data, "POST", path)
    if err:
        return PlaceBuyOrderOutput(success=False, error=err)
    payload = {
        "client_order_id": str(uuid.uuid4()),
        "product_id": f"{currency}-USD",
        "side": "BUY",
        "order_configuration": {"market_market_ioc": {"quote_size": amount}},
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_V3}/orders", headers=headers, json=payload
            )
        if response.status_code not in (200, 201):
            return PlaceBuyOrderOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
    except Exception as exc:
        return PlaceBuyOrderOutput(success=False, error=str(exc))

    if data.get("error_response"):
        e = data.get("error_response") or {}
        return PlaceBuyOrderOutput(
            success=False,
            error=f"Order failed: {e.get('error', 'Unknown')} - {e.get('message', '')}",
        )
    order = data.get("success_response") or {}
    return PlaceBuyOrderOutput(
        success=True,
        order=_OrderInfo(
            order_id=order.get("order_id"),
            product_id=order.get("product_id"),
            side=order.get("side"),
            client_order_id=order.get("client_order_id"),
        ),
    )


@tool(args_schema=WithdrawFundsInput)
@serialize_pydantic_return
async def withdraw_funds(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    amount: str,
    currency: str,
    payment_method: str,
) -> WithdrawFundsOutput:
    """Withdraw cryptocurrency to an external destination address."""
    path = "/api/v3/brokerage/portfolios/default/withdrawals/crypto"
    headers, err = _headers(auth_data, "POST", path)
    if err:
        return WithdrawFundsOutput(success=False, error=err)
    payload = {
        "idem": str(uuid.uuid4()),
        "amount": amount,
        "asset": currency,
        "address": payment_method,
        "network": currency,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"https://{_API_HOST}{path}", headers=headers, json=payload
            )
        if response.status_code not in (200, 201):
            return WithdrawFundsOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
    except Exception as exc:
        return WithdrawFundsOutput(success=False, error=str(exc))
    return WithdrawFundsOutput(
        success=True,
        id=data.get("id"),
        status=data.get("status"),
        amount=data.get("amount"),
        asset=data.get("asset"),
        fee=data.get("fee"),
        transaction_hash=data.get("transaction_hash"),
        destination_address=data.get("destination_address"),
        network=data.get("network"),
        created_at=data.get("created_at"),
    )


@tool(args_schema=GetExchangeRatesInput)
@serialize_pydantic_return
async def get_exchange_rates(
    auth_type: str, auth_data: dict[str, Any], currency: str = "USD"
) -> GetExchangeRatesOutput:
    """Get current exchange rates for the requested base currency."""
    path = "/v2/exchange-rates"
    headers, err = _headers(auth_data, "GET", path)
    if err:
        return GetExchangeRatesOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_V2}/exchange-rates",
                headers=headers,
                params={"currency": currency},
            )
        if response.status_code != 200:
            return GetExchangeRatesOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
    except Exception as exc:
        return GetExchangeRatesOutput(success=False, error=str(exc))
    rates_block = data.get("data") or {}
    return GetExchangeRatesOutput(
        success=True,
        currency=rates_block.get("currency"),
        rates=rates_block.get("rates") or {},
    )


@tool(args_schema=GetSpotPriceInput)
@serialize_pydantic_return
async def get_spot_price(
    auth_type: str, auth_data: dict[str, Any], currency_pair: str
) -> GetSpotPriceOutput:
    """Get the current spot price for the given currency pair."""
    path = f"/v2/prices/{currency_pair}/spot"
    headers, err = _headers(auth_data, "GET", path)
    if err:
        return GetSpotPriceOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_V2}/prices/{currency_pair}/spot", headers=headers
            )
        if response.status_code != 200:
            return GetSpotPriceOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
    except Exception as exc:
        return GetSpotPriceOutput(success=False, error=str(exc))
    price = data.get("data") or {}
    return GetSpotPriceOutput(
        success=True,
        base=price.get("base"),
        currency=price.get("currency"),
        amount=price.get("amount"),
    )


@tool(args_schema=GetPaymentMethodsInput)
@serialize_pydantic_return
async def get_payment_methods(
    auth_type: str, auth_data: dict[str, Any]
) -> GetPaymentMethodsOutput:
    """List all payment methods configured on the authenticated account."""
    path = "/api/v3/brokerage/payment_methods"
    headers, err = _headers(auth_data, "GET", path)
    if err:
        return GetPaymentMethodsOutput(success=False, error=err)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_V3}/payment_methods", headers=headers
            )
        if response.status_code != 200:
            return GetPaymentMethodsOutput(
                success=False, error=_api_err(response.status_code, response.text)
            )
        data = response.json() or {}
    except Exception as exc:
        return GetPaymentMethodsOutput(success=False, error=str(exc))
    rows = [
        PaymentMethodRow(
            id=pm.get("id"),
            type=pm.get("type"),
            name=pm.get("name"),
            currency=pm.get("currency"),
            allow_buy=pm.get("allow_buy"),
            allow_sell=pm.get("allow_sell"),
            allow_deposit=pm.get("allow_deposit"),
            allow_withdraw=pm.get("allow_withdraw"),
            verified=pm.get("verified"),
        )
        for pm in data.get("payment_methods") or []
    ]
    return GetPaymentMethodsOutput(success=True, payment_methods=rows, total=len(rows))
