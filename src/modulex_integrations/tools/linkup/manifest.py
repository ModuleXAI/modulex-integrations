"""Linkup integration manifest.

Linkup is a web-search API that grounds AI agents in up-to-date web
information with source attribution. Authentication is a single API key
sent as an ``Authorization: Bearer`` token.
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
    name="linkup",
    display_name="Linkup",
    description=(
        "Search the web with Linkup — retrieve up-to-date information with "
        "source attribution, returning either an AI-generated sourced answer "
        "or raw ranked search results."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:linkup-themed",
    app_url="https://www.linkup.so",
    categories=["Web Search & Scraping", "data", "search"],
    actions=[
        ActionDefinition(
            name="search",
            description="Search the web for information using Linkup.",
            parameters={
                "q": ParameterDef(
                    type="string",
                    description='The search query (e.g., "latest AI research papers 2024")',
                    required=True,
                ),
                "depth": ParameterDef(
                    type="string",
                    description=(
                        'Search depth: "standard" for quick results, "deep" for '
                        'comprehensive search (also supports "fast")'
                    ),
                    default="standard",
                ),
                "output_type": ParameterDef(
                    type="string",
                    description=(
                        'Output format: "sourcedAnswer" for an AI-generated answer '
                        'with citations, "searchResults" for raw results, or '
                        '"structured"'
                    ),
                    default="sourcedAnswer",
                ),
                "include_images": ParameterDef(
                    type="boolean",
                    description="Whether to include images in search results",
                ),
                "include_inline_citations": ParameterDef(
                    type="boolean",
                    description=(
                        "Add inline citations to answers (only applies when "
                        'output_type is "sourcedAnswer")'
                    ),
                ),
                "include_sources": ParameterDef(
                    type="boolean",
                    description="Include sources in the response",
                ),
                "from_date": ParameterDef(
                    type="string",
                    description="Start date for filtering results (YYYY-MM-DD format)",
                ),
                "to_date": ParameterDef(
                    type="string",
                    description="End date for filtering results (YYYY-MM-DD format)",
                ),
                "include_domains": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated list of domain names to restrict search "
                        "results to"
                    ),
                ),
                "exclude_domains": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated list of domain names to exclude from "
                        "search results"
                    ),
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Linkup API key",
            setup_instructions=[
                "Go to https://app.linkup.so and sign up or log in",
                "Open the API Keys section of your dashboard",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="LINKUP_API_KEY",
                    display_name="Linkup API Key",
                    description="Your Linkup API key from app.linkup.so",
                    required=True,
                    sensitive=True,
                    about_url="https://app.linkup.so",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.linkup.so/v1/search",
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {api_key}",
                },
                body={"q": "test", "depth": "standard", "outputType": "sourcedAnswer"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["answer"],
                ),
                cost_level="minimal",
                description="Validates the API key with a minimal standard search query",
            ),
        ),
    ],
)
