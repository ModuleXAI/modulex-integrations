"""Brandfetch integration manifest."""
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


_TEST_HEADERS = {
    "Authorization": "Bearer {api_key}",
    "Accept": "application/json",
}
_TEST_SUCCESS = SuccessIndicators(
    status_codes=[200],
    response_fields=["domain"],
)


manifest = IntegrationManifest(
    name="brandfetch",
    display_name="Brandfetch",
    description=(
        "Integrate Brandfetch into your workflow. Retrieve brand logos, "
        "colors, fonts, and company data by domain, ticker, or name search."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:brandfetch-themed",
    app_url="https://brandfetch.com",
    categories=["Sales", "enrichment", "marketing"],
    actions=[
        ActionDefinition(
            name="get_brand",
            description=(
                "Retrieve brand assets including logos, colors, fonts, and "
                "company info by domain, ticker, ISIN, or crypto symbol."
            ),
            parameters={
                "identifier": ParameterDef(
                    type="string",
                    description=(
                        "Brand identifier: domain (nike.com), stock ticker (NKE), "
                        "ISIN (US6541061031), or crypto symbol (BTC)"
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search",
            description="Search for brands by name and find their domains and logos.",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Company or brand name to search for",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Brandfetch API key",
            setup_instructions=[
                "Sign up or log in at https://developers.brandfetch.com",
                "Open your dashboard and locate your API key",
                "Copy the API key and paste it below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="BRANDFETCH_API_KEY",
                    display_name="Brandfetch API Key",
                    description="Your Brandfetch API key from the developer dashboard",
                    required=True,
                    sensitive=True,
                    about_url="https://docs.brandfetch.com/brand-api/overview",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.brandfetch.io/v2/brands/brandfetch.com",
                method="GET",
                headers=_TEST_HEADERS,
                success_indicators=_TEST_SUCCESS,
                cost_level="free",
                description=(
                    "Validates the API key with a free lookup of the "
                    "brandfetch.com domain (does not count toward quota)."
                ),
            ),
        ),
    ],
)
