"""RevenueCat integration manifest.

RevenueCat exposes a single-API-key REST API (v1). Authentication is an
``Authorization: Bearer <api_key>`` header. The runtime injects the key
via the ``api_key`` credential convention (key-based signature).
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="revenuecat",
    display_name="RevenueCat",
    description=(
        "Manage in-app subscriptions and entitlements. Retrieve customer "
        "subscription status, grant or revoke promotional entitlements, record "
        "purchases, update subscriber attributes, and manage Google Play "
        "subscription billing."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:revenuecat-themed",
    app_url="https://www.revenuecat.com",
    categories=["Finance & Payments", "payments", "subscriptions"],
    actions=[
        ActionDefinition(
            name="get_customer",
            description="Retrieve subscriber information by app user ID.",
            parameters={
                "app_user_id": ParameterDef(
                    type="string",
                    description="The app user ID of the subscriber",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_customer",
            description="Permanently delete a subscriber and all associated data.",
            parameters={
                "app_user_id": ParameterDef(
                    type="string",
                    description="The app user ID of the subscriber to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_purchase",
            description="Record a purchase (receipt) for a subscriber via the REST API.",
            parameters={
                "app_user_id": ParameterDef(
                    type="string",
                    description="The app user ID of the subscriber",
                    required=True,
                ),
                "fetch_token": ParameterDef(
                    type="string",
                    description=(
                        "Store receipt or purchase token: iOS base64 receipt / "
                        "JWSTransaction, Android purchase token, Amazon receipt, "
                        "Stripe subscription or Checkout Session ID, Roku transaction "
                        "ID, or Paddle subscription/transaction ID"
                    ),
                    required=True,
                ),
                "platform": ParameterDef(
                    type="string",
                    description=(
                        "Platform of the purchase, sent as the X-Platform header. One "
                        "of: ios, android, amazon, macos, uikitformac, stripe, roku, "
                        "paddle"
                    ),
                    required=True,
                ),
                "product_id": ParameterDef(
                    type="string",
                    description="Product identifier or SKU. Required for Google.",
                ),
                "price": ParameterDef(
                    type="number",
                    description="Price of the product. Required if you provide a currency.",
                ),
                "currency": ParameterDef(
                    type="string",
                    description="ISO 4217 currency code. Required if you provide a price.",
                ),
                "is_restore": ParameterDef(
                    type="boolean",
                    description=(
                        "Deprecated. Triggers configured restore behavior for shared "
                        "fetch tokens."
                    ),
                ),
                "presented_offering_identifier": ParameterDef(
                    type="string",
                    description=(
                        "Identifier of the offering presented to the customer at "
                        "purchase time."
                    ),
                ),
                "payment_mode": ParameterDef(
                    type="string",
                    description=(
                        "Payment mode for the introductory period: pay_as_you_go, "
                        "pay_up_front, or free_trial."
                    ),
                ),
                "introductory_price": ParameterDef(
                    type="number",
                    description="Introductory price paid (if any).",
                ),
                "attributes": ParameterDef(
                    type="string",
                    description=(
                        "JSON object of subscriber attributes to set alongside the "
                        "purchase. Each key maps to {\"value\": string, "
                        "\"updated_at_ms\": number}."
                    ),
                ),
                "updated_at_ms": ParameterDef(
                    type="integer",
                    description=(
                        "UNIX epoch ms used to resolve attribute conflicts at the "
                        "request level."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="grant_entitlement",
            description="Grant a promotional entitlement to a subscriber.",
            parameters={
                "app_user_id": ParameterDef(
                    type="string",
                    description="The app user ID of the subscriber",
                    required=True,
                ),
                "entitlement_identifier": ParameterDef(
                    type="string",
                    description="The entitlement identifier to grant",
                    required=True,
                ),
                "duration": ParameterDef(
                    type="string",
                    description=(
                        "Deprecated. Provide either duration or end_time_ms "
                        "(end_time_ms preferred). One of: daily, three_day, weekly, "
                        "two_week, monthly, two_month, three_month, six_month, yearly, "
                        "lifetime."
                    ),
                ),
                "end_time_ms": ParameterDef(
                    type="integer",
                    description=(
                        "Absolute end time in ms since Unix epoch. Use instead of "
                        "duration."
                    ),
                ),
                "start_time_ms": ParameterDef(
                    type="integer",
                    description=(
                        "Deprecated. Optional start time in ms since Unix epoch, used "
                        "with duration."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="revoke_entitlement",
            description=(
                "Revoke all promotional entitlements for a specific entitlement "
                "identifier."
            ),
            parameters={
                "app_user_id": ParameterDef(
                    type="string",
                    description="The app user ID of the subscriber",
                    required=True,
                ),
                "entitlement_identifier": ParameterDef(
                    type="string",
                    description="The entitlement identifier to revoke",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_offerings",
            description="List all offerings configured for the project.",
            parameters={
                "app_user_id": ParameterDef(
                    type="string",
                    description="An app user ID to retrieve offerings for",
                    required=True,
                ),
                "platform": ParameterDef(
                    type="string",
                    description=(
                        "X-Platform header value. One of: ios, android, amazon, "
                        "stripe, roku, paddle. Required for legacy public API keys; "
                        "ignored with app-specific keys."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="update_subscriber_attributes",
            description=(
                "Update custom subscriber attributes (e.g., $email, $displayName, or "
                "custom key-value pairs)."
            ),
            parameters={
                "app_user_id": ParameterDef(
                    type="string",
                    description="The app user ID of the subscriber",
                    required=True,
                ),
                "attributes": ParameterDef(
                    type="string",
                    description=(
                        "JSON object of attributes to set. Each key maps to an object "
                        "with \"value\" (string; null or empty deletes the attribute) "
                        "and \"updated_at_ms\" (Unix epoch ms used for conflict "
                        "resolution — required)."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="defer_google_subscription",
            description=(
                "Defer a Google Play subscription by extending its billing date "
                "(Google Play only)."
            ),
            parameters={
                "app_user_id": ParameterDef(
                    type="string",
                    description="The app user ID of the subscriber",
                    required=True,
                ),
                "product_id": ParameterDef(
                    type="string",
                    description=(
                        "The Google Play product identifier of the subscription to "
                        "defer"
                    ),
                    required=True,
                ),
                "extend_by_days": ParameterDef(
                    type="integer",
                    description=(
                        "Number of days to extend by (1-365). Provide extend_by_days "
                        "or expiry_time_ms."
                    ),
                ),
                "expiry_time_ms": ParameterDef(
                    type="integer",
                    description=(
                        "Absolute new expiry time in ms since Unix epoch. Use instead "
                        "of extend_by_days."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="refund_google_subscription",
            description=(
                "Refund a specific store transaction by its store transaction "
                "identifier and revoke access (subscription or non-subscription, last "
                "365 days)."
            ),
            parameters={
                "app_user_id": ParameterDef(
                    type="string",
                    description="The app user ID of the subscriber",
                    required=True,
                ),
                "store_transaction_id": ParameterDef(
                    type="string",
                    description=(
                        "The store transaction identifier of the purchase to refund "
                        "(e.g., GPA.3309-9122-6177-45730 for Google Play)"
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="revoke_google_subscription",
            description=(
                "Immediately revoke access to a Google Play subscription and issue a "
                "refund (Google Play only)."
            ),
            parameters={
                "app_user_id": ParameterDef(
                    type="string",
                    description="The app user ID of the subscriber",
                    required=True,
                ),
                "product_id": ParameterDef(
                    type="string",
                    description=(
                        "The Google Play product identifier of the subscription to "
                        "revoke"
                    ),
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your RevenueCat REST API v1 key",
            setup_instructions=[
                "Go to https://app.revenuecat.com and log in",
                "Open Project Settings → API Keys",
                "Create or copy a secret API key (sk_...) for write operations",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="REVENUECAT_API_KEY",
                    display_name="RevenueCat API Key",
                    description="Your RevenueCat REST API v1 key (secret key recommended)",
                    required=True,
                    sensitive=True,
                    sample_format="sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://www.revenuecat.com/docs/api-v1",
                ),
            ],
            test_endpoint=TestEndpoint(
                # GET /subscribers/{id} returns 200 and gets-or-creates the
                # subscriber, making it a low-impact credential probe.
                url="https://api.revenuecat.com/v1/subscribers/modulex_credential_probe",
                method="GET",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["subscriber"],
                ),
                cost_level="minimal",
                description="Validates the API key by fetching a probe subscriber record",
            ),
        ),
    ],
)
