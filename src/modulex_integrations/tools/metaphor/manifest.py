"""Metaphor integration manifest."""
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
    name="metaphor",
    display_name="Metaphor",
    description="AI-powered web search, similarity matching, and document content retrieval via the Metaphor API",
    logo="modulex:metaphor-themed",
    version="1.0.0",
    author="ModuleX",
    app_url="https://metaphor.systems",
    categories=["Web Search & Scraping", "ai"],
    actions=[
        ActionDefinition(
            name="search",
            description="Perform a search with a Metaphor prompt-engineered query and retrieve a list of relevant results",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="The query string in the form of a declarative suggestion, where a high quality search result link would follow",
                    required=True,
                ),
                "num_results": ParameterDef(
                    type="integer",
                    description="Number of search results to return. Default 10. Up to 30 for basic plans.",
                ),
                "include_domains": ParameterDef(
                    type="array",
                    description="List of domains to include in the search. Only one of include_domains and exclude_domains should be specified.",
                ),
                "exclude_domains": ParameterDef(
                    type="array",
                    description="List of domains to exclude in the search. Only one of include_domains and exclude_domains should be specified.",
                ),
                "start_crawl_date": ParameterDef(
                    type="string",
                    description="Only include links crawled after this date. ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).",
                ),
                "end_crawl_date": ParameterDef(
                    type="string",
                    description="Only include links crawled before this date. ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).",
                ),
                "start_published_date": ParameterDef(
                    type="string",
                    description="Only include links published after this date. ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).",
                ),
                "end_published_date": ParameterDef(
                    type="string",
                    description="Only include links published before this date. ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).",
                ),
                "use_autoprompt": ParameterDef(
                    type="boolean",
                    description="Whether to use autoprompt to enhance the query",
                    required=True,
                    default=False,
                ),
                "type": ParameterDef(
                    type="string",
                    description="The type of search. Allowed values: 'keyword', 'neural'. Default: neural.",
                ),
            },
        ),
        ActionDefinition(
            name="find_similar_links",
            description="Find similar links to the link provided",
            parameters={
                "url": ParameterDef(
                    type="string",
                    description="The URL for which you would like to find similar links",
                    required=True,
                ),
                "num_results": ParameterDef(
                    type="integer",
                    description="Number of search results to return. Default 10. Up to 30 for basic plans.",
                ),
                "include_domains": ParameterDef(
                    type="array",
                    description="List of domains to include in the search. Only one of include_domains and exclude_domains should be specified.",
                ),
                "exclude_domains": ParameterDef(
                    type="array",
                    description="List of domains to exclude in the search. Only one of include_domains and exclude_domains should be specified.",
                ),
                "start_crawl_date": ParameterDef(
                    type="string",
                    description="Only include links crawled after this date. ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).",
                ),
                "end_crawl_date": ParameterDef(
                    type="string",
                    description="Only include links crawled before this date. ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).",
                ),
                "start_published_date": ParameterDef(
                    type="string",
                    description="Only include links published after this date. ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).",
                ),
                "end_published_date": ParameterDef(
                    type="string",
                    description="Only include links published before this date. ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).",
                ),
            },
        ),
        ActionDefinition(
            name="get_documents_content",
            description="Retrieve contents of documents based on a list of document IDs obtained from search or find_similar_links",
            parameters={
                "ids": ParameterDef(
                    type="array",
                    description="An array of document IDs obtained from either search or find_similar_links. Array of strings.",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Metaphor API key",
            setup_instructions=[
                "Go to https://dashboard.metaphor.systems and sign in",
                "Navigate to the API Keys section",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="METAPHOR_API_KEY",
                    display_name="Metaphor API Key",
                    description="Your Metaphor API key from dashboard.metaphor.systems",
                    required=True,
                    sensitive=True,
                    about_url="https://dashboard.metaphor.systems",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.metaphor.systems/search",
                method="POST",
                headers={"x-api-key": "{api_key}", "Content-Type": "application/json"},
                body={"query": "test", "numResults": 1},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["results"],
                ),
                cost_level="minimal",
                description="Validates the API key by performing a minimal search",
            ),
        ),
    ],
)
