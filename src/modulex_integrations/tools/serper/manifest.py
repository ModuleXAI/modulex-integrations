"""Serper integration manifest.

Serper is a Google Search API that returns structured SERP data (web,
news, places, images, videos, shopping) over a single ``POST`` endpoint.
Authentication is a single API key sent in the ``X-API-KEY`` header.
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
    name="serper",
    display_name="Serper",
    description=(
        "Search the web with the Serper Google Search API. Supports web, "
        "news, places, and image search, returning organic results plus "
        "knowledge graph, answer box, people-also-ask, and related searches."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:serper",
    app_url="https://serper.dev",
    categories=["Web Search & Scraping", "search", "seo"],
    actions=[
        ActionDefinition(
            name="search",
            description=(
                "A powerful web search tool that provides access to Google search "
                "results through the Serper API. Supports different types of "
                "searches including regular web search, news, places, and images. "
                "Returns comprehensive results including organic results, knowledge "
                "graph, answer box, people also ask, related searches, and top stories."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description=(
                        'The search query (e.g., "latest AI news", '
                        '"best restaurants in NYC")'
                    ),
                    required=True,
                ),
                "num": ParameterDef(
                    type="integer",
                    description="Number of results to return (e.g., 10, 20, 50)",
                ),
                "gl": ParameterDef(
                    type="string",
                    description='Country code for search results (e.g., "us", "uk", "de", "fr")',
                ),
                "hl": ParameterDef(
                    type="string",
                    description='Language code for search results (e.g., "en", "es", "de", "fr")',
                ),
                "type": ParameterDef(
                    type="string",
                    description=(
                        'Type of search to perform: "search" (default), "news", '
                        '"places", "images", "videos", or "shopping"'
                    ),
                    default="search",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Serper API key",
            setup_instructions=[
                "Go to https://serper.dev and sign up or log in",
                "Open your dashboard and navigate to the 'API Key' section",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="SERPER_API_KEY",
                    display_name="Serper API Key",
                    description="Your Serper API key from serper.dev",
                    required=True,
                    sensitive=True,
                    about_url="https://serper.dev/api-key",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://google.serper.dev/search",
                method="POST",
                headers={
                    "X-API-KEY": "{api_key}",
                    "Content-Type": "application/json",
                },
                body={"q": "test"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    # TODO (unverified): top-level "searchParameters" echo key
                    # casing not confirmed against a live JSON sample; documented
                    # in the source types and returned on every response, but a
                    # 200 alone already validates the key.
                    response_fields=["searchParameters"],
                ),
                cost_level="minimal",
                description="Validates the API key with a minimal search query",
            ),
        ),
    ],
)
