"""Tavily integration manifest.

Pydantic translation of the legacy
``modulex/py/app/integrations/tools/tavily_integration.json``.

Both auth schemas (api_key + modulex_key) POST to ``/search`` with a
JSON body for the credential test — same pattern as exa, relies on
``TestEndpoint.body`` introduced in the schema for that integration.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ModulexKeyAuthSchema,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


_TEST_BODY = {
    "api_key": "{api_key}",
    "query": "test",
    "max_results": 1,
    "search_depth": "basic",
}
_TEST_HEADERS = {"Content-Type": "application/json"}
_TEST_SUCCESS = SuccessIndicators(status_codes=[200], response_fields=["results"])


manifest = IntegrationManifest(
    name="tavily",
    display_name="Tavily Search",
    description=(
        "AI-powered web search engine with advanced search capabilities, "
        "answer generation, and news search"
    ),
    version="1.0.0",
    author="ModuleX",
    logo="https://cdn.jsdelivr.net/gh/ModuleXAI/logox@main/tools/tavily.svg",
    app_url="https://tavily.com",
    categories=["Web Search & Scraping", "research", "ai"],
    actions=[
        ActionDefinition(
            name="web_search",
            description=(
                "Performs comprehensive web search using Tavily's AI-powered "
                "search engine"
            ),
            parameters={
                "query": ParameterDef(
                    type="string", description="Search query", required=True
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return (1-20)",
                    default=5,
                ),
                "search_depth": ParameterDef(
                    type="string",
                    description="Search depth: basic (faster) or advanced (thorough)",
                    default="basic",
                ),
                "include_domains": ParameterDef(
                    type="array",
                    description="List of domains to specifically include in search results",
                ),
                "exclude_domains": ParameterDef(
                    type="array",
                    description="List of domains to specifically exclude from search results",
                ),
            },
        ),
        ActionDefinition(
            name="answer_search",
            description=(
                "Performs web search and generates a direct AI answer to the "
                "query with supporting sources"
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Question or search query",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of supporting results to return",
                    default=5,
                ),
                "search_depth": ParameterDef(
                    type="string",
                    description="Search depth: basic or advanced",
                    default="advanced",
                ),
                "include_domains": ParameterDef(
                    type="array",
                    description="List of domains to specifically include",
                ),
                "exclude_domains": ParameterDef(
                    type="array",
                    description="List of domains to exclude",
                ),
            },
        ),
        ActionDefinition(
            name="news_search",
            description="Searches recent news articles using Tavily's specialized news search",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="News search query",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of news articles to return",
                    default=5,
                ),
                "days": ParameterDef(
                    type="integer",
                    description="Number of days back to search (1-365)",
                    default=3,
                ),
                "include_domains": ParameterDef(
                    type="array",
                    description="News domains to include (e.g., reuters.com, bbc.com)",
                ),
                "exclude_domains": ParameterDef(
                    type="array",
                    description="News domains to exclude",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Tavily API key",
            setup_environment_variables=[
                EnvVar(
                    name="TAVILY_API_KEY",
                    display_name="Tavily API Key",
                    description="Your Tavily API key for authentication",
                    required=True,
                    sensitive=True,
                    sample_format="tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://tavily.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.tavily.com/search",
                method="POST",
                headers=_TEST_HEADERS,
                body=_TEST_BODY,
                success_indicators=_TEST_SUCCESS,
                cost_level="minimal",
                description=(
                    "Validates API key with minimal search query (1 result, basic depth)"
                ),
            ),
        ),
        ModulexKeyAuthSchema(
            display_name="ModuleX Managed Key",
            description=(
                "Use ModuleX's managed API keys with usage tracked against your "
                "weekly credit limit"
            ),
            setup_environment_variables=[],
            test_endpoint=TestEndpoint(
                url="https://api.tavily.com/search",
                method="POST",
                headers=_TEST_HEADERS,
                body=_TEST_BODY,
                success_indicators=_TEST_SUCCESS,
                cost_level="minimal",
                description=(
                    "Validates system API key with minimal search query (1 result, basic depth)"
                ),
            ),
        ),
    ],
)
