"""GoDaddy integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="godaddy",
    display_name="GoDaddy",
    description="Domain registration, availability checking, and management via the GoDaddy API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:godaddy-themed",
    app_url="https://www.godaddy.com",
    categories=["domains", "infrastructure", "web-hosting"],
    actions=[
        ActionDefinition(
            name="check_domain_availability",
            description="Check the availability of a domain for purchase or transfer",
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="The domain name to check availability for (e.g. example.com)",
                    required=True,
                ),
                "check_type": ParameterDef(
                    type="string",
                    description="Optimize for time (FAST) or accuracy (FULL). Allowed values: FAST, FULL",
                ),
                "for_transfer": ParameterDef(
                    type="boolean",
                    description="Whether to include domains available for transfer. If true, check_type is ignored",
                ),
            },
        ),
        ActionDefinition(
            name="list_domains",
            description="List domains owned by the authenticated GoDaddy account",
            parameters={
                "statuses": ParameterDef(
                    type="array",
                    description="Filter by status. Array of strings: ACTIVE, CANCELLED, etc.",
                ),
                "status_groups": ParameterDef(
                    type="array",
                    description="Filter by status group. Array of strings: VISIBLE, INACTIVE, RENEWABLE, etc.",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of domains to return",
                ),
                "marker": ParameterDef(
                    type="string",
                    description="Marker domain to use as the offset in results",
                ),
                "includes": ParameterDef(
                    type="array",
                    description="Optional details to include: authCode, contacts, nameServers",
                ),
                "modified_date": ParameterDef(
                    type="string",
                    description="Only include results modified since this date (ISO 8601 format)",
                ),
            },
        ),
        ActionDefinition(
            name="list_tlds_options",
            description="Retrieve the list of available top-level domains (TLDs)",
            parameters={},
        ),
        ActionDefinition(
            name="renew_domain",
            description="Renew a domain registration in GoDaddy",
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="The domain name to renew (e.g. example.com)",
                    required=True,
                ),
                "period": ParameterDef(
                    type="integer",
                    description="Number of years to extend the domain (1-10). Defaults to original purchase period when omitted",
                ),
            },
        ),
        ActionDefinition(
            name="suggest_domains",
            description="Suggest available domain names based on given criteria",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Domain name or keywords for which alternative domain names will be suggested",
                    required=True,
                ),
                "country": ParameterDef(
                    type="string",
                    description="Two-letter ISO country code as a hint for target region",
                ),
                "city": ParameterDef(
                    type="string",
                    description="City name as a hint for target region",
                ),
                "sources": ParameterDef(
                    type="array",
                    description="Sources to query: CC_TLD, EXTENSION, KEYWORD_SPIN, PREMIUM",
                ),
                "tlds": ParameterDef(
                    type="array",
                    description="Top-level domains to include in suggestions (e.g. com, net, org)",
                ),
                "length_max": ParameterDef(
                    type="integer",
                    description="Maximum length of second-level domain",
                ),
                "length_min": ParameterDef(
                    type="integer",
                    description="Minimum length of second-level domain",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of suggestions to return",
                ),
                "wait_ms": ParameterDef(
                    type="integer",
                    description="Maximum time in milliseconds to wait for responses",
                ),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="GoDaddy API Key + Secret",
            description=(
                "Authenticate using a GoDaddy API key and secret pair. "
                "The Authorization header is built as 'sso-key <key>:<secret>'."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="GODADDY_API_KEY",
                    display_name="API Key",
                    description="Your GoDaddy API Key from developer.godaddy.com",
                    required=True,
                    sensitive=False,
                    sample_format="xxxxxxxxxxxxxxxx",
                    about_url="https://developer.godaddy.com/keys",
                ),
                EnvVar(
                    name="GODADDY_API_SECRET",
                    display_name="API Secret",
                    description="Your GoDaddy API Secret from developer.godaddy.com",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://developer.godaddy.com/keys",
                ),
                EnvVar(
                    name="GODADDY_API_URL",
                    display_name="API URL",
                    description=(
                        "GoDaddy API base URL. Use https://api.godaddy.com for production "
                        "or https://api.ote-godaddy.com for the test environment"
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="https://api.godaddy.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="{GODADDY_API_URL}/v1/domains?limit=1",
                method="GET",
                headers={
                    "Authorization": "sso-key {GODADDY_API_KEY}:{GODADDY_API_SECRET}",
                    "Accept": "application/json",
                },
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description=(
                    "Validates the API key + secret pair by listing a single "
                    "domain on the configured GoDaddy environment"
                ),
            ),
        ),
    ],
)
