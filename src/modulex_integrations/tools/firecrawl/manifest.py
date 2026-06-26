"""Firecrawl integration manifest."""
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


def _scrape_test_endpoint(description: str) -> TestEndpoint:
    return TestEndpoint(
        url="https://api.firecrawl.dev/v1/scrape",
        method="POST",
        headers={
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json",
        },
        body={
            "url": "https://example.com",
            "formats": ["markdown"],
            "onlyMainContent": True,
        },
        success_indicators=SuccessIndicators(
            status_codes=[200], response_fields=["success"]
        ),
        cost_level="minimal",
        description=description,
    )


manifest = IntegrationManifest(
    name="firecrawl",
    display_name="Firecrawl",
    description=(
        "AI-powered web scraping, crawling, and search tool for extracting "
        "content from websites with advanced options for JavaScript "
        "rendering, caching, and structured data extraction."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:firecrawl",
    app_url="https://firecrawl.dev",
    categories=["Web Search & Scraping", "data", "search"],
    actions=[
        ActionDefinition(
            name="scrape",
            description=(
                "Scrape content from a single URL with advanced options. "
                "Best for single page content extraction when you know "
                "exactly which page contains the information."
            ),
            parameters={
                "url": ParameterDef(
                    type="string", description="The URL to scrape", required=True
                ),
                "formats": ParameterDef(
                    type="array",
                    description=(
                        "Content formats: markdown, html, rawHtml, screenshot, "
                        "links, summary"
                    ),
                    default=["markdown"],
                ),
                "only_main_content": ParameterDef(
                    type="boolean",
                    description=(
                        "Extract only the main content, filtering out "
                        "navigation/footers"
                    ),
                    default=True,
                ),
                "include_tags": ParameterDef(
                    type="array",
                    description="HTML tags to specifically include in extraction",
                ),
                "exclude_tags": ParameterDef(
                    type="array",
                    description="HTML tags to exclude from extraction",
                ),
                "wait_for": ParameterDef(
                    type="integer",
                    description="Time in milliseconds to wait for dynamic content",
                ),
                "mobile": ParameterDef(
                    type="boolean", description="Use mobile viewport"
                ),
                "remove_base64_images": ParameterDef(
                    type="boolean",
                    description="Remove base64-encoded images from output",
                ),
                "max_age": ParameterDef(
                    type="integer",
                    description=(
                        "Maximum age in milliseconds for cached content. "
                        "Enables faster scrapes for cached pages."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="map_website",
            description=(
                "Map a website to discover all indexed URLs. Best for "
                "discovering URLs before deciding what to scrape."
            ),
            parameters={
                "url": ParameterDef(
                    type="string",
                    description="Starting URL for URL discovery",
                    required=True,
                ),
                "search": ParameterDef(
                    type="string", description="Optional search term to filter URLs"
                ),
                "sitemap": ParameterDef(
                    type="string",
                    description="Sitemap handling: 'include', 'skip', or 'only'",
                ),
                "include_subdomains": ParameterDef(
                    type="boolean",
                    description="Include URLs from subdomains in results",
                ),
                "limit": ParameterDef(
                    type="integer", description="Maximum number of URLs to return"
                ),
                "ignore_query_parameters": ParameterDef(
                    type="boolean",
                    description="Do not return URLs with query parameters",
                    default=True,
                ),
            },
        ),
        ActionDefinition(
            name="search",
            description=(
                "Search the web and optionally extract content from search "
                "results. Supports operators: site:, inurl:, intitle:, "
                'and exact match with quotes.'
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Search query string (supports operators)",
                    required=True,
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=5,
                ),
                "tbs": ParameterDef(
                    type="string", description="Time-based search filter"
                ),
                "location": ParameterDef(
                    type="string", description="Location parameter for search results"
                ),
                "scrape_options": ParameterDef(
                    type="object",
                    description="Options for scraping search results",
                ),
            },
        ),
        ActionDefinition(
            name="crawl",
            description=(
                "Start a crawl job on a website. Returns a job ID — use "
                "check_crawl_status to monitor."
            ),
            parameters={
                "url": ParameterDef(
                    type="string",
                    description="Starting URL for the crawl",
                    required=True,
                ),
                "exclude_paths": ParameterDef(
                    type="array", description="URL paths to exclude from crawling"
                ),
                "include_paths": ParameterDef(
                    type="array", description="Only crawl these URL paths"
                ),
                "max_depth": ParameterDef(
                    type="integer",
                    description="Maximum depth to crawl relative to the entered URL",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of pages to crawl",
                    default=100,
                ),
                "allow_external_links": ParameterDef(
                    type="boolean",
                    description="Allow crawling links to external domains",
                    default=False,
                ),
                "allow_backward_links": ParameterDef(
                    type="boolean",
                    description="Allow crawling links to parent paths",
                    default=False,
                ),
                "ignore_sitemap": ParameterDef(
                    type="boolean",
                    description="Ignore the website sitemap when crawling",
                    default=False,
                ),
                "scrape_options": ParameterDef(
                    type="object",
                    description="Options for scraping each page",
                ),
            },
        ),
        ActionDefinition(
            name="check_crawl_status",
            description=(
                "Check the status of a crawl job and retrieve results once "
                "complete."
            ),
            parameters={
                "crawl_id": ParameterDef(
                    type="string",
                    description="Crawl job ID returned from the crawl action",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="extract",
            description=(
                "Extract structured information from web pages using LLM "
                "capabilities. Best for extracting specific structured data."
            ),
            parameters={
                "urls": ParameterDef(
                    type="array",
                    description="Array of URLs to extract information from",
                    required=True,
                ),
                "prompt": ParameterDef(
                    type="string", description="Custom prompt for the LLM extraction"
                ),
                "schema_definition": ParameterDef(
                    type="object",
                    description="JSON schema for structured data extraction",
                ),
                "allow_external_links": ParameterDef(
                    type="boolean",
                    description="Allow extraction from external links",
                    default=False,
                ),
                "enable_web_search": ParameterDef(
                    type="boolean",
                    description="Enable web search for additional context",
                    default=False,
                ),
                "include_subdomains": ParameterDef(
                    type="boolean",
                    description="Include subdomains in extraction",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="batch_scrape",
            description=(
                "Batch scrape multiple URLs efficiently. More efficient than "
                "calling scrape multiple times."
            ),
            parameters={
                "urls": ParameterDef(
                    type="array",
                    description="Array of URLs to scrape",
                    required=True,
                ),
                "formats": ParameterDef(
                    type="array",
                    description="Content formats to extract",
                    default=["markdown"],
                ),
                "only_main_content": ParameterDef(
                    type="boolean",
                    description="Extract only the main content",
                    default=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Firecrawl API key",
            setup_environment_variables=[
                EnvVar(
                    name="FIRECRAWL_API_KEY",
                    display_name="Firecrawl API Key",
                    description="Your Firecrawl API key for authentication",
                    required=True,
                    sensitive=True,
                    sample_format="fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://firecrawl.dev",
                ),
            ],
            test_endpoint=_scrape_test_endpoint(
                "Validates API key with minimal scrape of example.com"
            ),
        ),
    ],
)
