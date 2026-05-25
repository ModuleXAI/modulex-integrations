"""Tests for the Coinbase integration.

JWT signing is mocked out via ``unittest.mock.patch`` on the
``_headers`` helper to avoid generating real Ed25519/ECDSA keys in the
test path. One direct ``generate_jwt`` test exercises the signing path
end-to-end with a locally generated Ed25519 key.
"""
from __future__ import annotations

import base64
from typing import Any
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from modulex_integrations.tools.coinbase import (
    TOOLS,
    get_account,
    get_accounts,
    get_exchange_rates,
    get_payment_methods,
    get_spot_price,
    get_transactions,
    manifest,
    place_buy_order,
    withdraw_funds,
)
from modulex_integrations.tools.coinbase.outputs import (
    GetAccountOutput,
    GetAccountsOutput,
    GetExchangeRatesOutput,
    GetPaymentMethodsOutput,
    GetSpotPriceOutput,
    GetTransactionsOutput,
    PlaceBuyOrderOutput,
    WithdrawFundsOutput,
)
from modulex_integrations.tools.coinbase.tools import generate_jwt

V3 = "https://api.coinbase.com/api/v3/brokerage"
V2 = "https://api.coinbase.com/v2"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {"api_key": "kid", "api_secret": "fake-secret"},
}
_STUB_HEADERS = ({"Authorization": "Bearer stub", "Accept": "application/json"}, None)


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


class TestManifest:
    def test_manifest_exposes_eight_actions(self) -> None:
        assert len(manifest.actions) == 8

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["custom"]

    def test_reachability_test_endpoint(self) -> None:
        # JWT signing for real CDP auth runs in tools.py at first call.
        # The manifest ships a reachability check against the public
        # /v2/time endpoint so the credential-save flow has something
        # to test.
        for a in manifest.auth_schemas:
            assert a.test_endpoint is not None
            assert "api.coinbase.com" in a.test_endpoint.url


def test_generate_jwt_ed25519_roundtrip() -> None:
    """End-to-end signing on a locally generated Ed25519 key."""
    private = Ed25519PrivateKey.generate()
    seed = private.private_bytes_raw()
    public = private.public_key().public_bytes_raw()
    secret_b64 = base64.b64encode(seed + public).decode()
    token = generate_jwt("kid", secret_b64, "GET", "/v2/accounts")
    assert token.count(".") == 2  # header.payload.signature


def test_generate_jwt_rejects_oversized_key() -> None:
    bogus = base64.b64encode(b"x" * 31).decode()
    with pytest.raises(ValueError):
        generate_jwt("kid", bogus, "GET", "/v2/accounts")


# Patch _headers so each test doesn't have to sign a real JWT.
def _patch_headers() -> Any:
    return patch(
        "modulex_integrations.tools.coinbase.tools._headers",
        return_value=_STUB_HEADERS,
    )


@pytest.mark.asyncio
async def test_get_accounts(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{V3}/accounts?limit=25",
        json={
            "accounts": [
                {
                    "uuid": "u1",
                    "name": "BTC Wallet",
                    "currency": "BTC",
                    "available_balance": {"value": "0.5", "currency": "BTC"},
                    "active": True,
                }
            ],
            "has_next": False,
        },
    )
    with _patch_headers():
        result = GetAccountsOutput.model_validate(
            await get_accounts.ainvoke(_args())
        )
    assert result.success is True
    assert result.total == 1
    assert result.accounts[0].available_balance == "0.5"


@pytest.mark.asyncio
async def test_get_accounts_api_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{V3}/accounts?limit=25", status_code=401, text="bad jwt"
    )
    with _patch_headers():
        result = GetAccountsOutput.model_validate(
            await get_accounts.ainvoke(_args())
        )
    assert result.success is False
    assert result.error is not None and "401" in result.error


@pytest.mark.asyncio
async def test_get_account(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{V3}/accounts/u1",
        json={"account": {"uuid": "u1", "name": "BTC", "default": True}},
    )
    with _patch_headers():
        result = GetAccountOutput.model_validate(
            await get_account.ainvoke(_args(account_id="u1"))
        )
    assert result.success is True
    assert result.account is not None and result.account.uuid == "u1"


@pytest.mark.asyncio
async def test_get_transactions(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{V3}/orders/historical/fills?limit=10&cursor=c1",
        json={"fills": [{"trade_id": "t1", "side": "BUY"}], "cursor": "c2"},
    )
    with _patch_headers():
        result = GetTransactionsOutput.model_validate(
            await get_transactions.ainvoke(
                _args(account_id="u1", limit=10, starting_after="c1")
            )
        )
    assert result.success is True
    assert result.total == 1
    assert result.cursor == "c2"


@pytest.mark.asyncio
async def test_place_buy_order_success(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{V3}/orders",
        status_code=201,
        json={
            "success_response": {
                "order_id": "o1",
                "product_id": "BTC-USD",
                "side": "BUY",
                "client_order_id": "co1",
            }
        },
    )
    with _patch_headers():
        result = PlaceBuyOrderOutput.model_validate(
            await place_buy_order.ainvoke(
                _args(account_id="u1", amount="100", currency="BTC")
            )
        )
    assert result.success is True
    assert result.order is not None and result.order.order_id == "o1"


@pytest.mark.asyncio
async def test_place_buy_order_returns_200_with_error_response(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{V3}/orders",
        status_code=200,
        json={
            "error_response": {
                "error": "INSUFFICIENT_FUND",
                "message": "Not enough USD",
            }
        },
    )
    with _patch_headers():
        result = PlaceBuyOrderOutput.model_validate(
            await place_buy_order.ainvoke(
                _args(account_id="u1", amount="100", currency="BTC")
            )
        )
    assert result.success is False
    assert result.error is not None and "INSUFFICIENT_FUND" in result.error


@pytest.mark.asyncio
async def test_withdraw_funds(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.coinbase.com/api/v3/brokerage/portfolios/default/withdrawals/crypto",
        status_code=201,
        json={"id": "w1", "status": "processing", "amount": "0.1", "asset": "BTC"},
    )
    with _patch_headers():
        result = WithdrawFundsOutput.model_validate(
            await withdraw_funds.ainvoke(
                _args(account_id="u1", amount="0.1", currency="BTC", payment_method="addr1")
            )
        )
    assert result.success is True
    assert result.id == "w1"


@pytest.mark.asyncio
async def test_get_exchange_rates(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{V2}/exchange-rates?currency=USD",
        json={"data": {"currency": "USD", "rates": {"BTC": "0.00002"}}},
    )
    with _patch_headers():
        result = GetExchangeRatesOutput.model_validate(
            await get_exchange_rates.ainvoke(_args())
        )
    assert result.success is True
    assert result.rates["BTC"] == "0.00002"


@pytest.mark.asyncio
async def test_get_spot_price(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{V2}/prices/BTC-USD/spot",
        json={"data": {"base": "BTC", "currency": "USD", "amount": "50000"}},
    )
    with _patch_headers():
        result = GetSpotPriceOutput.model_validate(
            await get_spot_price.ainvoke(_args(currency_pair="BTC-USD"))
        )
    assert result.success is True
    assert result.amount == "50000"


@pytest.mark.asyncio
async def test_get_payment_methods(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{V3}/payment_methods",
        json={
            "payment_methods": [
                {"id": "pm1", "name": "Bank", "type": "ACH", "allow_buy": True}
            ]
        },
    )
    with _patch_headers():
        result = GetPaymentMethodsOutput.model_validate(
            await get_payment_methods.ainvoke(_args())
        )
    assert result.success is True
    assert result.total == 1


@pytest.mark.asyncio
async def test_missing_credentials_short_circuits() -> None:
    bad = {"auth_type": "custom", "auth_data": {}}
    result = GetAccountsOutput.model_validate(
        await get_accounts.ainvoke(bad)
    )
    assert result.success is False
    assert result.error is not None and "api_key" in result.error
