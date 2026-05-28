"""Shopify Partner integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="shopify_partner",
    display_name="Shopify Partner",
    description="Shopify Partner API for managing apps, verifying webhooks, and accessing partner account data",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:shopify_partner-themed",
    app_url="https://partners.shopify.com",
    categories=["ecommerce", "Developer Tools & Infrastructure"],
    actions=[
        ActionDefinition(
            name="verify_webhook",
            description="Verify an incoming webhook from Shopify by validating its HMAC-SHA256 signature",
            parameters={
                "app_secret_key": ParameterDef(
                    type="string",
                    description="The secret key associated with the Shopify App receiving the webhook",
                    required=True,
                ),
                "shopify_hmac": ParameterDef(
                    type="string",
                    description="The value of the x-shopify-hmac-sha256 webhook request header",
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="The incoming webhook payload as a JSON string",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Shopify Partner API Credentials",
            description="Authenticate using your Shopify Partner organization ID and API key",
            setup_instructions=[
                "Log in to your Shopify Partner Dashboard at https://partners.shopify.com",
                "Go to Settings > Partner API clients",
                "Create or copy your API key and note your Organization ID from the URL",
                "Paste both values below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="SHOPIFY_PARTNER_ORGANIZATION_ID",
                    display_name="Organization ID",
                    description="Your Shopify Partner organization ID (visible in the URL: partners.shopify.com/<org_id>)",
                    required=True,
                    sensitive=False,
                    sample_format="12345678",
                    about_url="https://partners.shopify.com",
                ),
                EnvVar(
                    name="SHOPIFY_PARTNER_API_KEY",
                    display_name="API Key",
                    description="Your Shopify Partner API access token",
                    required=True,
                    sensitive=True,
                    sample_format="shppa_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://partners.shopify.com",
                ),
            ],
        ),
    ],
)
