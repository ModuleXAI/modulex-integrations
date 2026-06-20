"""ZeroBounce integration manifest."""
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
    name="zerobounce",
    display_name="ZeroBounce",
    description=(
        "Validate email deliverability in real time — detect invalid, "
        "catch-all, spamtrap, abuse, and do-not-mail addresses — and check "
        "your remaining validation credits."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:zerobounce",
    app_url="https://www.zerobounce.net",
    categories=["Sales", "enrichment", "sales-engagement"],
    actions=[
        ActionDefinition(
            name="verify_email",
            description=(
                "Validate an email address deliverability in real time. "
                "Uses one validation credit."
            ),
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Email address to validate (e.g., john@example.com)",
                    required=True,
                ),
                "ip_address": ParameterDef(
                    type="string",
                    description=(
                        "Optional IP address the email signed up from "
                        "(improves scoring)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="get_credits",
            description=(
                "Retrieve the remaining validation credits for the "
                "authenticated account."
            ),
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your ZeroBounce API key",
            setup_instructions=[
                "Go to https://www.zerobounce.net and sign up or log in",
                "Open your account and navigate to the 'API' section",
                "Copy your API key",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="ZEROBOUNCE_API_KEY",
                    display_name="ZeroBounce API Key",
                    description="Your ZeroBounce API key from your account settings",
                    required=True,
                    sensitive=True,
                    about_url="https://www.zerobounce.net/members/apikey/",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.zerobounce.net/v2/getcredits",
                method="GET",
                params={"api_key": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["Credits"],
                ),
                cost_level="free",
                description="Validates the API key by fetching the credit balance",
            ),
        ),
    ],
)
