"""Google Merchant Center integration manifest."""
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
    name="google_merchant_center",
    display_name="Google Merchant Center",
    description="Manage product listings in Google Merchant Center via the Shopping Content API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:google_merchant_center",
    app_url="https://merchants.google.com",
    categories=["E-Commerce", "Marketing", "Google"],
    actions=[
        ActionDefinition(
            name="create_product",
            description="Creates a product in your Google Merchant Center account",
            parameters={
                "offer_id": ParameterDef(
                    type="string",
                    description="A unique identifier for the item",
                    required=True,
                ),
                "content_language": ParameterDef(
                    type="string",
                    description="The two-letter ISO 639-1 language code for the item (e.g. 'en', 'fr', 'de')",
                    required=True,
                ),
                "target_country": ParameterDef(
                    type="string",
                    description="The CLDR territory code for the item's country of sale (e.g. 'US', 'GB', 'DE')",
                    required=True,
                ),
                "channel": ParameterDef(
                    type="string",
                    description="The item's channel: 'local' or 'online'",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="Your product's name (max 150 characters)",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Your product's description (max 5000 characters)",
                ),
                "additional_options": ParameterDef(
                    type="object",
                    description="Additional product attributes as a JSON object (e.g. 'link', 'imageLink', 'price', 'availability')",
                ),
            },
        ),
        ActionDefinition(
            name="update_product",
            description="Updates an existing product in your Google Merchant Center account",
            parameters={
                "product_id": ParameterDef(
                    type="string",
                    description="The ID of the product to update (e.g. 'online:en:US:offer123')",
                    required=True,
                ),
                "updated_values": ParameterDef(
                    type="object",
                    description="Product attributes to update as a JSON object with attribute names as keys",
                    required=True,
                ),
                "update_mask": ParameterDef(
                    type="array",
                    description="List of product attribute names to update. Attributes in this list without a value in updated_values will be deleted",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Google OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_MERCHANT_CENTER_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_MERCHANT_CENTER_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_MERCHANT_CENTER_MERCHANT_ID",
                    display_name="Merchant ID",
                    description="Your Google Merchant Center account ID (numeric)",
                    required=True,
                    sensitive=False,
                    # Per-credential user input (every merchant has their own
                    # ID, so it can't be a server global). The runtime persists
                    # the user-entered value into auth_data at credential
                    # creation; tools.py reads it as auth_data["merchant_id"].
                    only_for_custom=False,
                    inject_into_auth_data=True,
                    sample_format="123456789",
                    about_url="https://merchants.google.com/mc/overview",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scopes=["https://www.googleapis.com/auth/content"],
            ),
            test_endpoint=TestEndpoint(
                # /accounts/authinfo doesn't require a merchant_id —
                # it lists the merchant accounts the OAuth token can
                # access. We use this instead of /{merchant_id}/products
                # because the modulex OAuth callback only stores
                # {access_token, refresh_token, expires_at} in auth_data;
                # the user-supplied GOOGLE_MERCHANT_CENTER_MERCHANT_ID
                # EnvVar isn't routed through the OAuth flow.
                url="https://shoppingcontent.googleapis.com/content/v2.1/accounts/authinfo",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["accountIdentifiers"],
                ),
                cost_level="free",
                description="Validates OAuth token via /accounts/authinfo (lists accessible merchant accounts).",
            ),
        ),
    ],
)
