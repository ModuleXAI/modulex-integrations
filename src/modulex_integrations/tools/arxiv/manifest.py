"""ArXiv integration manifest.

The arXiv API is fully open — it accepts no API key, no OAuth token, and
no other credential. Every action is a plain unauthenticated GET against
``https://export.arxiv.org/api/query``.

The declared ``modulex_key`` schema therefore validates nothing: it exists
so the credential-resolution step the runtime performs before every tool
call has something to resolve. The same approach is used by the other
credential-free integration in this package. Each ``@tool`` accepts an
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


def _max_results() -> ParameterDef:
    return ParameterDef(
        type="integer",
        description="Maximum number of results to return (1-2000)",
        default=10,
    )


manifest = IntegrationManifest(
    name="arxiv",
    display_name="ArXiv",
    description=(
        "Search and retrieve academic papers from ArXiv, the open-access "
        "repository of preprints in physics, mathematics, computer science, "
        "quantitative biology, quantitative finance, statistics, electrical "
        "engineering and economics. Search by keyword or field, fetch full "
        "metadata for a single paper by its identifier, and list an author's "
        "most recent submissions."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:arxiv-themed",
    app_url="https://arxiv.org",
    categories=["Web Search & Scraping", "research", "academic", "papers"],
    actions=[
        ActionDefinition(
            name="search",
            description=(
                "Search for academic papers on ArXiv by keywords, authors, titles, "
                "or other fields. Returns matching papers with abstracts, authors, "
                "categories and PDF links."
            ),
            parameters={
                "search_query": ParameterDef(
                    type="string",
                    description=(
                        "Search terms to look for on ArXiv. Boolean expressions "
                        "using AND, OR and ANDNOT are supported."
                    ),
                    required=True,
                ),
                "search_field": ParameterDef(
                    type="string",
                    description=(
                        "Field to search in: 'all', 'ti' (title), 'au' (author), "
                        "'abs' (abstract), 'co' (comment), 'jr' (journal reference), "
                        "'cat' (category), 'rn' (report number)"
                    ),
                    default="all",
                ),
                "max_results": _max_results(),
                "sort_by": ParameterDef(
                    type="string",
                    description=(
                        "Sort results by: 'relevance', 'lastUpdatedDate', "
                        "or 'submittedDate'"
                    ),
                    default="relevance",
                ),
                "sort_order": ParameterDef(
                    type="string",
                    description="Sort direction: 'descending' or 'ascending'",
                    default="descending",
                ),
                "start": ParameterDef(
                    type="integer",
                    description=(
                        "Zero-based index of the first result to return, for paging "
                        "through a large result set"
                    ),
                    default=0,
                ),
            },
        ),
        ActionDefinition(
            name="get_paper",
            description=(
                "Get detailed information about a specific ArXiv paper by its "
                "identifier, including title, abstract, authors, categories, "
                "journal reference, DOI and PDF link."
            ),
            parameters={
                "paper_id": ParameterDef(
                    type="string",
                    description=(
                        "ArXiv paper identifier, e.g. '1706.03762' or "
                        "'cs.AI/0001001'. A full https://arxiv.org/abs/... URL "
                        "is also accepted."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_author_papers",
            description=(
                "Search for papers by a specific author on ArXiv, returned with "
                "the newest submissions first."
            ),
            parameters={
                "author_name": ParameterDef(
                    type="string",
                    description="Author name to search for, e.g. 'John Smith'",
                    required=True,
                ),
                "max_results": _max_results(),
            },
        ),
    ],
    auth_schemas=[
        ModulexKeyAuthSchema(
            display_name="ModuleX Managed Key",
            description=(
                "Use ModuleX's managed access (the arXiv API is public, "
                "no authentication required)"
            ),
            test_endpoint=TestEndpoint(
                url="https://export.arxiv.org/api/query?search_query=all:electron&max_results=1",
                method="GET",
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description=(
                    "Reachability check against the public arXiv query "
                    "endpoint. No credential to validate; this only "
                    "confirms the API is reachable."
                ),
            ),
        ),
    ],
)
