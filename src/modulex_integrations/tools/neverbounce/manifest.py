"""NeverBounce integration manifest."""
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
    name="neverbounce",
    display_name="NeverBounce",
    description=(
        "Integrate NeverBounce to verify email deliverability in real time — "
        "classify addresses as valid, invalid, catch-all, disposable, or "
        "unknown — and check your remaining verification credits."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:neverbounce",
    app_url="https://www.neverbounce.com",
    categories=["Sales", "enrichment", "sales-engagement"],
    actions=[
        ActionDefinition(
            name="verify_email",
            description=(
                "Verify the deliverability of an email address. Classifies the "
                "address as valid, invalid, catch_all, disposable, or unknown and "
                "surfaces role-account and free-provider flags. Uses one "
                "verification credit."
            ),
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Email address to verify (e.g., john@example.com)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_credits",
            description=(
                "Retrieve the remaining paid and free verification credits for "
                "the account."
            ),
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your NeverBounce API key",
            setup_instructions=[
                "Go to https://app.neverbounce.com and sign up or log in",
                "Open Settings and select the 'API' section",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="NEVERBOUNCE_API_KEY",
                    display_name="NeverBounce API Key",
                    description="Your NeverBounce API key from app.neverbounce.com",
                    required=True,
                    sensitive=True,
                    sample_format="secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://app.neverbounce.com/apps/custom-integration",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.neverbounce.com/v4/account/info",
                method="GET",
                params={"key": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["status"],
                ),
                cost_level="free",
                description=(
                    "Validates the API key by reading the account credit balance "
                    "(does not consume a verification credit)"
                ),
            ),
        ),
    ],
)
