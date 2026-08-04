"""Wikipedia integration manifest.

The Wikipedia APIs are fully open — they accept no API key, no OAuth
token, and no other credential. Every action is a plain unauthenticated
GET against ``https://<language>.wikipedia.org``.

The declared ``modulex_key`` schema therefore validates nothing: it exists
so the credential-resolution step the runtime performs before every tool
call has something to resolve. The same approach is used by the other
credential-free integrations in this package. Each ``@tool`` accepts an
``api_key`` argument for signature uniformity and ignores it.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    IntegrationManifest,
    ModulexKeyAuthSchema,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]

_USER_AGENT = "modulex-integrations/1.0 (+https://modulex.dev)"


def _language() -> ParameterDef:
    return ParameterDef(
        type="string",
        description=(
            "Wikipedia language edition to query, e.g. 'en', 'tr', 'de', "
            "'simple'. Defaults to 'en'."
        ),
        default="en",
    )


manifest = IntegrationManifest(
    name="wikipedia",
    display_name="Wikipedia",
    description=(
        "Search and retrieve content from Wikipedia, the free online "
        "encyclopedia. Get the lead summary and metadata for an article, "
        "search articles by title or full text, fetch the full rendered HTML "
        "of a page, and draw a random article. Any of the ~340 language "
        "editions can be queried."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:wikipedia-themed",
    app_url="https://www.wikipedia.org",
    categories=["Web Search & Scraping", "knowledge-base", "research", "reference"],
    actions=[
        ActionDefinition(
            name="summary",
            description=(
                "Get a summary and metadata for a specific Wikipedia page: the "
                "lead extract, short description, thumbnail, page URLs, "
                "Wikidata item and coordinates. The returned 'type' field "
                "reports whether the title resolved to a standard article or "
                "to a disambiguation page."
            ),
            parameters={
                "page_title": ParameterDef(
                    type="string",
                    description=(
                        "Title of the Wikipedia page to summarize, e.g. "
                        "'Python (programming language)'"
                    ),
                    required=True,
                ),
                "language": _language(),
            },
        ),
        ActionDefinition(
            name="search",
            description=(
                "Search for Wikipedia pages by title or content. Returns "
                "matching articles with a highlighted excerpt, short "
                "description, thumbnail and article URL."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Search terms used to find Wikipedia pages",
                    required=True,
                ),
                "search_limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return (1-100)",
                    default=10,
                ),
                "language": _language(),
            },
        ),
        ActionDefinition(
            name="content",
            description=(
                "Get the full rendered HTML of a Wikipedia page along with its "
                "page id, title, latest revision id and timestamp."
            ),
            parameters={
                "page_title": ParameterDef(
                    type="string",
                    description="Title of the Wikipedia page to fetch content for",
                    required=True,
                ),
                "max_length": ParameterDef(
                    type="integer",
                    description=(
                        "Maximum number of HTML characters to return. Longer "
                        "articles are truncated and the 'truncated' flag is set. "
                        "Use 0 or a negative value to return the full article HTML."
                    ),
                    default=100000,
                ),
                "language": _language(),
            },
        ),
        ActionDefinition(
            name="random",
            description=(
                "Get a random Wikipedia page with its summary, description and "
                "thumbnail."
            ),
            parameters={
                "language": _language(),
            },
        ),
    ],
    auth_schemas=[
        ModulexKeyAuthSchema(
            display_name="ModuleX Managed Key",
            description=(
                "Use ModuleX's managed access (the Wikipedia APIs are public, "
                "no authentication required)"
            ),
            test_endpoint=TestEndpoint(
                url="https://en.wikipedia.org/api/rest_v1/page/summary/Wikipedia",
                method="GET",
                headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description=(
                    "Reachability check against the public Wikipedia page-summary "
                    "endpoint. No credential to validate; this only confirms the "
                    "API is reachable."
                ),
            ),
        ),
    ],
)
