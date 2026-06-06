"""Lemon Squeezy integration manifest."""
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


def _pagination_params() -> dict[str, ParameterDef]:
    return {
        "page": ParameterDef(
            type="integer",
            description="Page number for pagination",
            default=1,
        ),
        "per_page": ParameterDef(
            type="integer",
            description="Number of results per page (max 100)",
            default=10,
        ),
    }


manifest = IntegrationManifest(
    name="lemon_squeezy",
    display_name="Lemon Squeezy",
    description=(
        "Digital products and subscriptions platform for selling software, "
        "SaaS, and digital goods with built-in payment processing."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:lemon-squeezy",
    app_url="https://lemonsqueezy.com",
    categories=[
        "Finance & Payments",
        "Business Services",
        "payments",
        "subscriptions",
        "digital-products",
    ],
    actions=[
        ActionDefinition(
            name="list_customers",
            description=(
                "List all customers from your Lemon Squeezy account with "
                "pagination support"
            ),
            parameters=_pagination_params(),
        ),
        ActionDefinition(
            name="retrieve_customer",
            description=(
                "Retrieve a specific customer by ID with their details and "
                "purchase history"
            ),
            parameters={
                "customer_id": ParameterDef(
                    type="string",
                    description="The ID of the customer to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_orders",
            description=(
                "List all orders from your Lemon Squeezy account with optional "
                "filtering"
            ),
            parameters={
                **_pagination_params(),
                "store_id": ParameterDef(
                    type="string", description="Filter orders by store ID"
                ),
                "user_email": ParameterDef(
                    type="string", description="Filter orders by user email"
                ),
            },
        ),
        ActionDefinition(
            name="retrieve_order",
            description="Retrieve a specific order by ID with full order details",
            parameters={
                "order_id": ParameterDef(
                    type="string",
                    description="The ID of the order to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_products",
            description="List all products from your Lemon Squeezy account",
            parameters={
                **_pagination_params(),
                "store_id": ParameterDef(
                    type="string", description="Filter products by store ID"
                ),
            },
        ),
        ActionDefinition(
            name="retrieve_product",
            description="Retrieve a specific product by ID with full product details",
            parameters={
                "product_id": ParameterDef(
                    type="string",
                    description="The ID of the product to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_subscriptions",
            description=(
                "List all subscriptions from your Lemon Squeezy account with "
                "optional filtering"
            ),
            parameters={
                **_pagination_params(),
                "store_id": ParameterDef(
                    type="string", description="Filter subscriptions by store ID"
                ),
                "status": ParameterDef(
                    type="string",
                    description=(
                        "Filter by subscription status: on_trial, active, "
                        "paused, past_due, unpaid, cancelled, expired"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="retrieve_subscription",
            description=(
                "Retrieve a specific subscription by ID with full subscription "
                "details"
            ),
            parameters={
                "subscription_id": ParameterDef(
                    type="string",
                    description="The ID of the subscription to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_stores",
            description="List all stores from your Lemon Squeezy account",
            parameters=_pagination_params(),
        ),
        ActionDefinition(
            name="retrieve_store",
            description="Retrieve a specific store by ID with full store details",
            parameters={
                "store_id": ParameterDef(
                    type="string",
                    description="The ID of the store to retrieve",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Lemon Squeezy API key",
            setup_environment_variables=[
                EnvVar(
                    name="LEMON_SQUEEZY_API_KEY",
                    display_name="Lemon Squeezy API Key",
                    description="Your Lemon Squeezy API key for authentication",
                    required=True,
                    sensitive=True,
                    sample_format="eyJ...",
                    about_url="https://docs.lemonsqueezy.com/api#authentication",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.lemonsqueezy.com/v1/users/me",
                method="GET",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "Accept": "application/vnd.api+json",
                    "Content-Type": "application/vnd.api+json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["data"]
                ),
                cost_level="free",
                description="Validates API key by fetching the authenticated user",
            ),
        ),
    ],
)
