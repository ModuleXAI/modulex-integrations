"""SEMrush integration manifest."""
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


def _domain_database(default_limit: int = 10) -> dict[str, ParameterDef]:
    return {
        "domain": ParameterDef(
            type="string", description="Domain name to analyze", required=True
        ),
        "database": ParameterDef(
            type="string",
            description="Regional database (e.g. 'us', 'uk', 'ca', 'de', 'fr')",
            default="us",
        ),
        "limit": ParameterDef(
            type="integer",
            description="Maximum number of records to return",
            default=default_limit,
        ),
    }


def _keyword_with_db(required_db: bool = True, default_limit: int = 10) -> dict[str, ParameterDef]:
    if required_db:
        database = ParameterDef(
            type="string", description="Database to use", required=True
        )
    else:
        database = ParameterDef(
            type="string", description="Database to use", default="us"
        )
    return {
        "keyword": ParameterDef(
            type="string", description="Keyword to analyze", required=True
        ),
        "database": database,
        "limit": ParameterDef(
            type="integer",
            description="Maximum number of results",
            default=default_limit,
        ),
    }


manifest = IntegrationManifest(
    name="semrush",
    display_name="SEMrush",
    description=(
        "Comprehensive SEO analytics platform for domain analysis, keyword "
        "research, backlink analysis, competitor research, and traffic "
        "analytics."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="simple-icons:semrush",
    app_url="https://www.semrush.com",
    categories=["Data & Analytics", "analytics", "marketing", "research"],
    actions=[
        ActionDefinition(
            name="domain_overview",
            description=(
                "Get domain overview data including organic/paid search "
                "traffic, keywords, and rankings"
            ),
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="Domain name to analyze",
                    required=True,
                ),
                "database": ParameterDef(
                    type="string", description="Regional database", default="us"
                ),
            },
        ),
        ActionDefinition(
            name="domain_organic_keywords",
            description="Get organic keywords for a domain with position, volume, and traffic data",
            parameters=_domain_database(),
        ),
        ActionDefinition(
            name="domain_paid_keywords",
            description="Get paid keywords for a domain with ad position and CPC data",
            parameters=_domain_database(),
        ),
        ActionDefinition(
            name="competitors",
            description="Get organic-search competitors for a domain",
            parameters=_domain_database(),
        ),
        ActionDefinition(
            name="backlinks",
            description=(
                "Get backlinks for a domain or URL with source details and "
                "authority scores"
            ),
            parameters={
                "target": ParameterDef(
                    type="string",
                    description="Domain or URL to analyze",
                    required=True,
                ),
                "limit": ParameterDef(
                    type="integer", description="Maximum backlinks to return", default=10
                ),
            },
        ),
        ActionDefinition(
            name="backlinks_domains",
            description="Get referring domains for a domain or URL",
            parameters={
                "target": ParameterDef(
                    type="string",
                    description="Domain or URL to analyze",
                    required=True,
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum referring domains to return",
                    default=10,
                ),
            },
        ),
        ActionDefinition(
            name="keyword_overview",
            description=(
                "Get overview data for a keyword including volume, CPC, and "
                "competition"
            ),
            parameters={
                "keyword": ParameterDef(
                    type="string", description="Keyword to analyze", required=True
                ),
                "database": ParameterDef(
                    type="string", description="Database to use", default="us"
                ),
            },
        ),
        ActionDefinition(
            name="keyword_overview_single_db",
            description=(
                "Get detailed keyword overview from a specific database with "
                "difficulty score"
            ),
            parameters={
                "keyword": ParameterDef(
                    type="string", description="Keyword to analyze", required=True
                ),
                "database": ParameterDef(
                    type="string", description="Database to use", required=True
                ),
            },
        ),
        ActionDefinition(
            name="batch_keyword_overview",
            description="Analyze up to 100 keywords at once in a specific database",
            parameters={
                "keywords": ParameterDef(
                    type="array",
                    description="Array of keywords (max 100)",
                    required=True,
                ),
                "database": ParameterDef(
                    type="string", description="Database to use", required=True
                ),
            },
        ),
        ActionDefinition(
            name="related_keywords",
            description="Get semantically related keywords for a keyword",
            parameters=_keyword_with_db(required_db=False),
        ),
        ActionDefinition(
            name="keyword_organic_results",
            description="Get domains ranking in Google's top 100 for a keyword",
            parameters=_keyword_with_db(required_db=True),
        ),
        ActionDefinition(
            name="keyword_paid_results",
            description="Get domains in Google's paid search results for a keyword",
            parameters=_keyword_with_db(required_db=True),
        ),
        ActionDefinition(
            name="keyword_ads_history",
            description="Get domains that bid on a keyword in the last 12 months",
            parameters=_keyword_with_db(required_db=True),
        ),
        ActionDefinition(
            name="broad_match_keywords",
            description="Get broad matches and alternate search queries for a keyword",
            parameters=_keyword_with_db(required_db=True),
        ),
        ActionDefinition(
            name="phrase_questions",
            description="Get question-based keywords related to a term",
            parameters=_keyword_with_db(required_db=True),
        ),
        ActionDefinition(
            name="keyword_difficulty",
            description="Get difficulty index (0-100) for ranking in Google's top 10",
            parameters={
                "keywords": ParameterDef(
                    type="array",
                    description="Array of keywords (max 100)",
                    required=True,
                ),
                "database": ParameterDef(
                    type="string", description="Database to use", required=True
                ),
            },
        ),
        ActionDefinition(
            name="traffic_summary",
            description=(
                "Get traffic summary data for domains (requires .Trends API "
                "access)"
            ),
            parameters={
                "domains": ParameterDef(
                    type="array",
                    description="Array of domains to analyze",
                    required=True,
                ),
                "country": ParameterDef(
                    type="string", description="Country code", default="us"
                ),
            },
        ),
        ActionDefinition(
            name="traffic_sources",
            description=(
                "Get traffic sources breakdown for a domain (requires "
                ".Trends API access)"
            ),
            parameters={
                "domain": ParameterDef(
                    type="string", description="Domain to analyze", required=True
                ),
                "country": ParameterDef(
                    type="string", description="Country code", default="us"
                ),
            },
        ),
        ActionDefinition(
            name="api_units_balance",
            description="Check the remaining API units balance in your SEMrush account",
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your SEMrush API key",
            setup_environment_variables=[
                EnvVar(
                    name="SEMRUSH_API_KEY",
                    display_name="SEMrush API Key",
                    description="Your SEMrush API key for authentication",
                    required=True,
                    sensitive=True,
                    sample_format="x" * 32,
                    about_url="https://www.semrush.com/api-analytics/",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.semrush.com/",
                method="GET",
                params={"type": "api_units", "key": "{api_key}"},
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="minimal",
                description="Validates API key by checking API units balance (no cost)",
            ),
        ),
    ],
)
