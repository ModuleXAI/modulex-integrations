"""Exa integration manifest.

Direct pydantic translation of the legacy
``modulex/py/app/integrations/tools/exa_integration.json``.

This is the first migrated integration to exercise the ``api_key`` and
``modulex_key`` auth variants (github and slack used oauth2 +
bearer_token). Both Exa auth schemas POST to ``/search`` for the
credential test, which made ``TestEndpoint.body`` necessary in the
shared schema (added in this same change).
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


_TEST_BODY = {"query": "test", "numResults": 1}
_TEST_HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": "{api_key}",
}
_TEST_SUCCESS = SuccessIndicators(
    status_codes=[200],
    response_fields=["results"],
)


manifest = IntegrationManifest(
    name="exa",
    display_name="Exa Search",
    description=(
        "AI-powered semantic search engine for intelligent web search, "
        "content extraction, similarity matching, and answer generation"
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:exa",
    app_url="https://exa.ai",
    categories=["Web Search & Scraping", "data", "search"],
    actions=[
        ActionDefinition(
            name="search",
            description=(
                "Perform semantic web search using Exa's AI-powered search engine. "
                "Supports multiple search types (auto, neural, deep, fast) and "
                "category filtering."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Search query string",
                    required=True,
                ),
                "num_results": ParameterDef(
                    type="integer",
                    description="Number of results to return (1-100)",
                    default=10,
                ),
                "search_type": ParameterDef(
                    type="string",
                    description="Search type: 'auto' (default), 'neural', 'deep', or 'fast'",
                    default="auto",
                ),
                "category": ParameterDef(
                    type="string",
                    description="Filter results by content category",
                ),
                "include_domains": ParameterDef(
                    type="array",
                    description="List of domains to include in search results",
                ),
                "exclude_domains": ParameterDef(
                    type="array",
                    description="List of domains to exclude from search results",
                ),
                "start_published_date": ParameterDef(
                    type="string",
                    description=(
                        "Filter results published after this date (ISO 8601 format)"
                    ),
                ),
                "end_published_date": ParameterDef(
                    type="string",
                    description=(
                        "Filter results published before this date (ISO 8601 format)"
                    ),
                ),
                "include_text": ParameterDef(
                    type="boolean",
                    description="Whether to include page text content in results",
                    default=True,
                ),
                "include_highlights": ParameterDef(
                    type="boolean",
                    description="Whether to include relevant text highlights",
                    default=False,
                ),
                "include_summary": ParameterDef(
                    type="boolean",
                    description="Whether to include AI-generated summaries",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_contents",
            description=(
                "Extract full page contents, summaries, and metadata from a list "
                "of URLs. Uses cached results with optional live crawling."
            ),
            parameters={
                "urls": ParameterDef(
                    type="array",
                    description="List of URLs to extract content from",
                    required=True,
                ),
                "include_text": ParameterDef(
                    type="boolean",
                    description="Whether to include full page text",
                    default=True,
                ),
                "include_highlights": ParameterDef(
                    type="boolean",
                    description="Whether to include relevant text highlights",
                    default=False,
                ),
                "highlights_per_url": ParameterDef(
                    type="integer",
                    description="Number of highlight snippets per URL",
                    default=3,
                ),
                "include_summary": ParameterDef(
                    type="boolean",
                    description="Whether to include AI-generated summary",
                    default=False,
                ),
                "livecrawl": ParameterDef(
                    type="string",
                    description="Live crawl option: 'never', 'fallback', 'preferred', 'always'",
                    default="fallback",
                ),
            },
        ),
        ActionDefinition(
            name="find_similar",
            description=(
                "Find pages similar to a given URL using semantic similarity. "
                "Ideal for discovering related content, competitive analysis, "
                "and research expansion."
            ),
            parameters={
                "url": ParameterDef(
                    type="string",
                    description="URL to find similar pages for",
                    required=True,
                ),
                "num_results": ParameterDef(
                    type="integer",
                    description="Number of similar results to return (1-100)",
                    default=10,
                ),
                "include_domains": ParameterDef(
                    type="array",
                    description="List of domains to include in results",
                ),
                "exclude_domains": ParameterDef(
                    type="array",
                    description="List of domains to exclude from results",
                ),
                "exclude_source_domain": ParameterDef(
                    type="boolean",
                    description="Whether to exclude results from the source URL's domain",
                    default=True,
                ),
                "category": ParameterDef(
                    type="string",
                    description="Filter by content category",
                ),
                "include_text": ParameterDef(
                    type="boolean",
                    description="Include page text content in results",
                    default=True,
                ),
            },
        ),
        ActionDefinition(
            name="answer",
            description=(
                "Get an AI-generated answer to a question informed by Exa search "
                "results. Provides accurate answers with citations from "
                "authoritative sources."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Question to answer using web search",
                    required=True,
                ),
                "num_results": ParameterDef(
                    type="integer",
                    description="Number of search results to use for generating answer",
                    default=5,
                ),
                "search_type": ParameterDef(
                    type="string",
                    description="Search type for finding sources",
                    default="auto",
                ),
                "include_domains": ParameterDef(
                    type="array",
                    description="Domains to prioritize for answers",
                ),
                "exclude_domains": ParameterDef(
                    type="array",
                    description="Domains to exclude from answer sources",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Exa API key",
            setup_instructions=[
                "Go to https://dashboard.exa.ai and sign up or log in",
                "Navigate to 'API Keys' section",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="EXA_API_KEY",
                    display_name="Exa API Key",
                    description="Your Exa API key from dashboard.exa.ai",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://dashboard.exa.ai/api-keys",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.exa.ai/search",
                method="POST",
                headers=_TEST_HEADERS,
                body=_TEST_BODY,
                success_indicators=_TEST_SUCCESS,
                cost_level="minimal",
                description="Validates API key with minimal search query (1 result)",
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
                url="https://api.exa.ai/search",
                method="POST",
                headers=_TEST_HEADERS,
                body=_TEST_BODY,
                success_indicators=_TEST_SUCCESS,
                cost_level="minimal",
                description="Validates system API key with minimal search query (1 result)",
            ),
        ),
    ],
)
