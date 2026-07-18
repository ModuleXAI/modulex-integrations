"""Mercury integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    BearerTokenAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="mercury",
    display_name="Mercury",
    description="Business banking platform for startups and scaling companies",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:mercury-themed",
    app_url="https://mercury.com",
    categories=["Finance & Payments", "Banking"],
    actions=[
        ActionDefinition(
            name="get_account_info",
            description="Retrieve information about a specific Mercury bank account",
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="The unique ID of the Mercury account to retrieve",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        BearerTokenAuthSchema(
            display_name="API Token",
            description="Use your Mercury API token to authenticate",
            setup_instructions=[
                "Log in to your Mercury dashboard at https://app.mercury.com",
                "Navigate to Settings -> API Tokens",
                "Generate a new API token and copy it",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="MERCURY_API_TOKEN",
                    display_name="API Token",
                    description="Your Mercury API token from the dashboard",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://app.mercury.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://backend.mercury.com/api/v1/accounts",
                method="GET",
                headers={"Authorization": "Bearer {token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["accounts"],
                ),
                cost_level="free",
                description="Validates the token by listing accounts",
            ),
        ),
    ],
)
