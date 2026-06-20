"""Similarweb integration manifest.

Similarweb authenticates with an API key passed as the ``api_key``
query-string parameter on every request, so the integration ships a
single ``ApiKeyAuthSchema`` (bring-your-own-key). The credential test
hits the lightweight ``general-data/all`` overview endpoint.
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


_DOMAIN_PARAM = ParameterDef(
    type="string",
    description=(
        'Website domain to analyze (e.g., "example.com" without www or protocol)'
    ),
    required=True,
)
_COUNTRY_PARAM = ParameterDef(
    type="string",
    description=(
        '2-letter ISO country code (e.g., "us", "gb", "de") or "world" for '
        "worldwide data"
    ),
    default="world",
)
_GRANULARITY_PARAM = ParameterDef(
    type="string",
    description="Data granularity: daily, weekly, or monthly",
    default="monthly",
)
_START_DATE_PARAM = ParameterDef(
    type="string",
    description='Start date in YYYY-MM format (e.g., "2024-01")',
)
_END_DATE_PARAM = ParameterDef(
    type="string",
    description='End date in YYYY-MM format (e.g., "2024-12")',
)
_MAIN_DOMAIN_ONLY_PARAM = ParameterDef(
    type="boolean",
    description="Exclude subdomains from results",
)


def _time_series_parameters() -> dict[str, ParameterDef]:
    return {
        "domain": _DOMAIN_PARAM,
        "country": _COUNTRY_PARAM,
        "granularity": _GRANULARITY_PARAM,
        "start_date": _START_DATE_PARAM,
        "end_date": _END_DATE_PARAM,
        "main_domain_only": _MAIN_DOMAIN_ONLY_PARAM,
    }


manifest = IntegrationManifest(
    name="similarweb",
    display_name="Similarweb",
    description=(
        "Access comprehensive website analytics including traffic estimates, "
        "engagement metrics, rankings, and traffic sources using the Similarweb "
        "API."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:similarweb",
    app_url="https://www.similarweb.com",
    categories=["Analytics & Data", "marketing", "seo"],
    actions=[
        ActionDefinition(
            name="website_overview",
            description=(
                "Get comprehensive website analytics including traffic, rankings, "
                "engagement, and traffic sources"
            ),
            parameters={"domain": _DOMAIN_PARAM},
        ),
        ActionDefinition(
            name="traffic_visits",
            description="Get total website visits over time (desktop and mobile combined)",
            parameters=_time_series_parameters(),
        ),
        ActionDefinition(
            name="bounce_rate",
            description="Get website bounce rate over time (desktop and mobile combined)",
            parameters=_time_series_parameters(),
        ),
        ActionDefinition(
            name="pages_per_visit",
            description="Get average pages per visit over time (desktop and mobile combined)",
            parameters=_time_series_parameters(),
        ),
        ActionDefinition(
            name="visit_duration",
            description="Get average desktop visit duration over time (in seconds)",
            parameters=_time_series_parameters(),
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Similarweb API key",
            setup_instructions=[
                "Sign in to your Similarweb account at https://www.similarweb.com",
                "Open the API account dashboard at https://account.similarweb.com",
                "Locate your API key under the API management section",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="SIMILARWEB_API_KEY",
                    display_name="Similarweb API Key",
                    description="Your Similarweb Web Traffic API key",
                    required=True,
                    sensitive=True,
                    about_url="https://developers.similarweb.com/docs/getting-started",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.similarweb.com/v1/website/similarweb.com/general-data/all",
                method="GET",
                params={"api_key": "{api_key}", "format": "json"},
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="minimal",
                description="Validates the API key with a lightweight website overview request",
            ),
        ),
    ],
)
