"""Airweave integration manifest.

Airweave is an AI-powered semantic search platform that retrieves
knowledge across synced data sources. The single ``search`` action is
collection-scoped and authenticates with an API key sent in the
``x-api-key`` header.
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
    name="airweave",
    display_name="Airweave",
    description=(
        "Search across your synced data sources using Airweave. Supports "
        "semantic search with hybrid, neural, or keyword retrieval strategies. "
        "Optionally generate AI-powered answers from search results."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:airweave-themed",
    app_url="https://airweave.ai",
    categories=["Web Search & Scraping", "vector-search", "knowledge-base"],
    actions=[
        ActionDefinition(
            name="search",
            description=(
                "Search your synced data collections using Airweave. Supports "
                "semantic search with hybrid, neural, or keyword retrieval "
                "strategies. Optionally generate AI-powered answers from search "
                "results."
            ),
            parameters={
                "collection_id": ParameterDef(
                    type="string",
                    description="The readable ID of the collection to search",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="The search query text",
                    required=True,
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                ),
                "retrieval_strategy": ParameterDef(
                    type="string",
                    description=(
                        "Retrieval strategy: 'hybrid' (default), 'neural', or 'keyword'"
                    ),
                ),
                "expand_query": ParameterDef(
                    type="boolean",
                    description="Generate query variations to improve recall",
                ),
                "rerank": ParameterDef(
                    type="boolean",
                    description="Reorder results for improved relevance using an LLM",
                ),
                "generate_answer": ParameterDef(
                    type="boolean",
                    description="Generate a natural-language answer to the query",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Airweave API key",
            setup_instructions=[
                "Go to https://app.airweave.ai and sign up or log in",
                "Open the API Keys section of your dashboard",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="AIRWEAVE_API_KEY",
                    display_name="Airweave API Key",
                    description="Your Airweave API key from app.airweave.ai",
                    required=True,
                    sensitive=True,
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.airweave.ai/collections",
                method="GET",
                headers={"x-api-key": "{api_key}"},
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description="Validates the API key by listing collections",
            ),
        ),
    ],
)
