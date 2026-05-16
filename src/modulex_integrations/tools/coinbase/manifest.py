"""Coinbase integration manifest.

Coinbase Developer Platform (CDP) authenticates via JWT signed with
either Ed25519 or ECDSA P-256 keys. That maps to neither our standard
``api_key`` (single secret) nor ``oauth2`` schema — the user actually
provides a key *pair* (key ID + private key material). Modeled as
``CustomAuthSchema``; the runtime ships both values through
``auth_data`` and the tool functions perform local JWT signing.

No ``test_endpoint`` is declared: validating CDP credentials requires
the JWT signature itself, which the credential-tester layer does not
construct. The modulex runtime simply skips the test in that case.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
)

__all__ = ["manifest"]


def _account_id_param() -> ParameterDef:
    return ParameterDef(
        type="string", description="The ID of the account", required=True
    )


def _amount_currency_params() -> dict[str, ParameterDef]:
    return {
        "amount": ParameterDef(
            type="string", description="The amount", required=True
        ),
        "currency": ParameterDef(
            type="string",
            description="The currency code (e.g. 'BTC', 'ETH', 'USD')",
            required=True,
        ),
    }


manifest = IntegrationManifest(
    name="coinbase",
    display_name="Coinbase",
    description=(
        "Cryptocurrency trading and wallet management platform for "
        "buying, selling, and storing digital assets via the Coinbase "
        "Developer Platform (CDP) API."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="bitcoin",
    app_url="https://www.coinbase.com",
    categories=["Business Services", "finance", "trading", "market"],
    actions=[
        ActionDefinition(
            name="get_accounts",
            description="List all cryptocurrency accounts for the authenticated user",
            parameters={
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum accounts to return (1-100)",
                    default=25,
                ),
            },
        ),
        ActionDefinition(
            name="get_account",
            description="Get details for a specific Coinbase account",
            parameters={"account_id": _account_id_param()},
        ),
        ActionDefinition(
            name="get_transactions",
            description="List historical order fills for an account",
            parameters={
                "account_id": _account_id_param(),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum transactions to return (1-100)",
                    default=25,
                ),
                "starting_after": ParameterDef(
                    type="string",
                    description="Pagination cursor (last transaction ID)",
                ),
            },
        ),
        ActionDefinition(
            name="place_buy_order",
            description=(
                "Place a market buy order (IOC) to purchase cryptocurrency. "
                "``amount`` is the spend in the quote currency (USD)."
            ),
            parameters={
                "account_id": _account_id_param(),
                **_amount_currency_params(),
                "payment_method": ParameterDef(
                    type="string",
                    description="Optional payment method ID",
                ),
            },
        ),
        ActionDefinition(
            name="withdraw_funds",
            description=(
                "Withdraw cryptocurrency from a Coinbase account to an "
                "external destination address."
            ),
            parameters={
                "account_id": _account_id_param(),
                **_amount_currency_params(),
                "payment_method": ParameterDef(
                    type="string",
                    description="Destination address (or payment method ID)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_exchange_rates",
            description="Get current exchange rates for cryptocurrencies",
            parameters={
                "currency": ParameterDef(
                    type="string",
                    description="Base currency for the rate table",
                    default="USD",
                ),
            },
        ),
        ActionDefinition(
            name="get_spot_price",
            description="Get current spot price for a currency pair",
            parameters={
                "currency_pair": ParameterDef(
                    type="string",
                    description="Currency pair (e.g. 'BTC-USD')",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_payment_methods",
            description="List all payment methods for the authenticated user",
            parameters={},
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="CDP API Key + Secret",
            description=(
                "Authenticate using a Coinbase Developer Platform API key "
                "pair: the key ID and either an ECDSA (PEM) or Ed25519 "
                "(base64) private key. JWT signing happens locally."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="COINBASE_API_KEY",
                    display_name="API Key ID",
                    description=(
                        "Your Coinbase CDP API Key ID (e.g. "
                        "organizations/{org_id}/apiKeys/{key_id})"
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="organizations/{org_id}/apiKeys/{key_id}",
                    about_url="https://docs.cdp.coinbase.com/",
                ),
                EnvVar(
                    name="COINBASE_API_SECRET",
                    display_name="API Secret",
                    description=(
                        "Coinbase CDP API Secret (PEM for ECDSA or base64 "
                        "for Ed25519). Used to sign JWTs locally."
                    ),
                    required=True,
                    sensitive=True,
                ),
            ],
        ),
    ],
)
