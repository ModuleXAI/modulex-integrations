"""Square integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="square",
    display_name="Square",
    description="Payment processing, commerce, and business management platform",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:square-themed",
    app_url="https://squareup.com",
    categories=["payments", "commerce", "finance"],
    actions=[
        ActionDefinition(
            name="create_customer",
            description="Create a new customer for a business. Must provide at least one of: given_name, family_name, company_name, email_address, or phone_number.",
            parameters={
                "given_name": ParameterDef(
                    type="string",
                    description="The first name associated with the customer profile",
                ),
                "family_name": ParameterDef(
                    type="string",
                    description="The last name associated with the customer profile",
                ),
                "company_name": ParameterDef(
                    type="string",
                    description="A business name associated with the customer profile",
                ),
                "email_address": ParameterDef(
                    type="string",
                    description="The email address associated with the customer profile",
                ),
                "phone_number": ParameterDef(
                    type="string",
                    description="Phone number (9-16 digits, optional + prefix and country code)",
                ),
                "reference_id": ParameterDef(
                    type="string",
                    description="An optional second ID to associate the customer with an entity in another system",
                ),
                "note": ParameterDef(
                    type="string",
                    description="A custom note associated with the customer profile",
                ),
            },
        ),
        ActionDefinition(
            name="create_invoice",
            description="Create a draft invoice for an order. You must publish (send) the invoice before Square can process it.",
            parameters={
                "location_id": ParameterDef(
                    type="string",
                    description="The ID of the Square location",
                    required=True,
                ),
                "order_id": ParameterDef(
                    type="string",
                    description="The ID of the order associated with the invoice",
                    required=True,
                ),
                "customer_id": ParameterDef(
                    type="string",
                    description="The ID of the customer who will receive the invoice",
                    required=True,
                ),
                "due_date": ParameterDef(
                    type="string",
                    description="The due date for the payment request, in YYYY-MM-DD format",
                    required=True,
                ),
                "accepted_payment_methods": ParameterDef(
                    type="array",
                    description="Payment methods customers can use. Valid values: card, square_gift_card, bank_account, buy_now_pay_later, cash_app_pay",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_order",
            description="Create a new order that can include information about products for purchase.",
            parameters={
                "location_id": ParameterDef(
                    type="string",
                    description="The ID of the Square location for the order",
                    required=True,
                ),
                "customer_id": ParameterDef(
                    type="string",
                    description="The ID of the customer associated with the order",
                ),
                "reference_id": ParameterDef(
                    type="string",
                    description="An optional second ID to associate the order with an entity in another system",
                ),
                "line_items": ParameterDef(
                    type="object",
                    description="Line items for the order. Array of objects, each with: quantity (string), name (string), base_price_money ({amount: int in cents, currency: string e.g. 'USD'})",
                ),
            },
        ),
        ActionDefinition(
            name="list_event_types_options",
            description="Retrieve the list of available webhook event types from Square.",
            parameters={},
        ),
        ActionDefinition(
            name="list_location_options",
            description="Retrieve the list of locations for the authenticated Square account.",
            parameters={},
        ),
        ActionDefinition(
            name="send_invoice",
            description="Publish the latest version of a specified invoice so Square can process it.",
            parameters={
                "location_id": ParameterDef(
                    type="string",
                    description="The ID of the Square location",
                    required=True,
                ),
                "invoice_id": ParameterDef(
                    type="string",
                    description="The ID of the invoice to publish",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Square OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="SQUARE_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Square OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="sq0idp-xxxxxxxxxxxxxxxx",
                    about_url="https://developer.squareup.com/apps",
                ),
                EnvVar(
                    name="SQUARE_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Square OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="sq0csp-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://developer.squareup.com/apps",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://connect.squareup.com/oauth2/authorize",
                token_url="https://connect.squareup.com/oauth2/token",
                scopes=[
                    "CUSTOMERS_WRITE",
                    "CUSTOMERS_READ",
                    "ORDERS_WRITE",
                    "ORDERS_READ",
                    "INVOICES_WRITE",
                    "INVOICES_READ",
                    "MERCHANT_PROFILE_READ",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://connect.squareup.com/v2/locations",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["locations"],
                ),
                cost_level="free",
                description="Validates OAuth token by listing locations",
            ),
        ),
    ],
)
