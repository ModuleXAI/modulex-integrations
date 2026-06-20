"""WhatsApp integration manifest.

Wraps the WhatsApp Cloud API (Meta Graph API) for sending text messages.
Uses the modulex ``api_key`` (bring-your-own-key) auth convention: the
credential is the WhatsApp Business API access token, sent as the bearer
token on each request.
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
    name="whatsapp",
    display_name="WhatsApp",
    description=(
        "Send WhatsApp messages through the WhatsApp Cloud API (Meta Graph "
        "API). Deliver text messages with optional link previews directly to "
        "recipients on WhatsApp."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:whatsapp-themed",
    app_url="https://www.whatsapp.com",
    categories=["Communication", "messaging", "automation"],
    actions=[
        ActionDefinition(
            name="send_message",
            description="Send a text message through the WhatsApp Cloud API.",
            parameters={
                "phone_number": ParameterDef(
                    type="string",
                    description=(
                        "Recipient phone number with country code (e.g., +14155552671)"
                    ),
                    required=True,
                ),
                "message": ParameterDef(
                    type="string",
                    description="Plain text message content to send",
                    required=True,
                ),
                "phone_number_id": ParameterDef(
                    type="string",
                    description=(
                        "WhatsApp Business Phone Number ID (from Meta Business Suite)"
                    ),
                    required=True,
                ),
                "preview_url": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether WhatsApp should try to render a link preview for the "
                        "first URL in the message"
                    ),
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description=(
                "Authenticate using your WhatsApp Business API access token "
                "(used as the bearer token on every request)"
            ),
            setup_instructions=[
                "Go to https://developers.facebook.com and open your Meta app",
                "Add the WhatsApp product and configure a Business Phone Number",
                "Copy the WhatsApp Business API access token (a temporary token is "
                "available in the dashboard; generate a permanent System User token "
                "for production)",
                "Note your WhatsApp Business Phone Number ID for each send call",
                "Paste the access token below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="WHATSAPP_ACCESS_TOKEN",
                    display_name="WhatsApp Access Token",
                    description=(
                        "WhatsApp Business API access token from the Meta Developer "
                        "Portal"
                    ),
                    required=True,
                    sensitive=True,
                    about_url="https://developers.facebook.com/docs/whatsapp/cloud-api/get-started",
                ),
            ],
            # TODO (unverified): the Graph API /me endpoint returns {"id": ...}
            # for user and system-user tokens, but exact behavior across all
            # WhatsApp Business token types is not documented as a dedicated
            # credential probe per
            # https://developers.facebook.com/docs/graph-api/reference/debug_token/
            test_endpoint=TestEndpoint(
                url="https://graph.facebook.com/v25.0/me",
                method="GET",
                headers={"Authorization": "Bearer {api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description=(
                    "Validates the access token against the Graph API /me endpoint"
                ),
            ),
        ),
    ],
)
