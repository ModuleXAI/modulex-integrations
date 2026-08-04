"""ArXiv LangChain ``@tool`` functions.

Three async tools wrapping the public arXiv API at
``https://export.arxiv.org/api/query``. The API is open — it takes no
API key, no OAuth token, and no other credential — so the functions
below declare **only** their action parameters and never touch the
credential-injection parameter names.

Transport notes:

- Every response is an Atom 1.0 feed (``application/atom+xml``), not
  JSON. It is parsed with the standard library's
  ``xml.etree.ElementTree`` into the pydantic models in ``outputs.py``,
  so the value returned at the ``@tool`` boundary stays a plain
  JSON-serializable dict.
- arXiv reports failures two different ways: a non-2xx HTTP status
  (``429`` with a plain-text ``Rate exceeded.`` body when the caller is
  too fast) and a ``200`` feed whose single ``<entry>`` is an error
  record (``<title>Error</title>``, ``<id>`` under
  ``http://arxiv.org/api/errors#``). Both are detected and returned as
  ``success=False`` + ``error``; nothing raises.
- arXiv asks callers for no more than one request every three seconds
  from a single connection. These tools do not sleep — pace calls on
  the agent side.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.arxiv.outputs import (
    ArxivPaper,
    GetAuthorPapersOutput,
    GetPaperOutput,
    SearchOutput,
)

__all__ = ["get_author_papers", "get_paper", "search"]

_ARXIV_API_URL = "https://export.arxiv.org/api/query"
_TIMEOUT = 30.0
_MAX_RESULTS_CAP = 2000
_ERROR_ID_PREFIX = "http://arxiv.org/api/errors"

# Atom feed namespaces used by the arXiv API.
_ATOM = "{http://www.w3.org/2005/Atom}"
_ARXIV_NS = "{http://arxiv.org/schemas/atom}"
_OPENSEARCH = "{http://a9.com/-/spec/opensearch/1.1/}"

# Field prefixes accepted by the ``search_query`` grammar. ``all`` means
# "no explicit prefix" — the raw query is forwarded untouched so callers
# can pass full boolean expressions (``au:Smith AND ti:electron``).
_SEARCH_FIELDS = frozenset({"all", "ti", "au", "abs", "co", "jr", "cat", "rn"})

_HEADERS = {
    "Accept": "application/atom+xml",
    "User-Agent": "modulex-integrations/1.0 (+https://modulex.dev)",
}

_ABS_PREFIXES = ("http://arxiv.org/abs/", "https://arxiv.org/abs/")


# --- Atom parsing helpers --------------------------------------------------


class _FeedError(Exception):
    """The feed parsed, but carries an arXiv error record instead of data."""


def _clean(text: str | None) -> str | None:
    """Collapse the whitespace arXiv wraps around element text."""
    if text is None:
        return None
    collapsed = " ".join(text.split())
    return collapsed or None


def _text(element: ET.Element, tag: str) -> str | None:
    found = element.find(tag)
    if found is None:
        return None
    return _clean(found.text)


def _parse_entry(entry: ET.Element) -> ArxivPaper:
    link = _text(entry, f"{_ATOM}id")

    paper_id = link
    if paper_id:
        for prefix in _ABS_PREFIXES:
            if paper_id.startswith(prefix):
                paper_id = paper_id[len(prefix) :]
                break

    pdf_link: str | None = None
    for link_element in entry.findall(f"{_ATOM}link"):
        if link_element.get("title") == "pdf":
            pdf_link = link_element.get("href")
            break

    authors: list[str] = []
    for author in entry.findall(f"{_ATOM}author"):
        name = _text(author, f"{_ATOM}name")
        if name:
            authors.append(name)

    categories: list[str] = []
    for category in entry.findall(f"{_ATOM}category"):
        term = category.get("term")
        if term:
            categories.append(term)

    primary_category_element = entry.find(f"{_ARXIV_NS}primary_category")
    primary_category = (
        primary_category_element.get("term") if primary_category_element is not None else None
    )

    return ArxivPaper(
        id=paper_id,
        title=_text(entry, f"{_ATOM}title"),
        summary=_text(entry, f"{_ATOM}summary"),
        authors=authors,
        published=_text(entry, f"{_ATOM}published"),
        updated=_text(entry, f"{_ATOM}updated"),
        link=link,
        pdf_link=pdf_link,
        categories=categories,
        primary_category=primary_category,
        comment=_text(entry, f"{_ARXIV_NS}comment"),
        journal_ref=_text(entry, f"{_ARXIV_NS}journal_ref"),
        doi=_text(entry, f"{_ARXIV_NS}doi"),
    )


def _parse_feed(xml_text: str) -> tuple[list[ArxivPaper], int]:
    """Parse an arXiv Atom feed into papers plus the total-results count.

    Raises ``_FeedError`` when the XML is unparseable or when the feed
    carries arXiv's single error ``<entry>`` instead of results.

    A document type declaration is rejected before parsing. The arXiv API
    never emits one, and refusing it removes the entity-expansion
    ("billion laughs") class of attack that the standard library's XML
    parser is otherwise open to — without pulling in a hardened parser.
    """
    if "<!DOCTYPE" in xml_text or "<!ENTITY" in xml_text:
        raise _FeedError(
            "Refusing to parse an ArXiv response containing a document type declaration."
        )

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise _FeedError(f"Could not parse the ArXiv response as Atom XML: {exc}") from exc

    entries = root.findall(f"{_ATOM}entry")

    if len(entries) == 1:
        entry_id = _text(entries[0], f"{_ATOM}id") or ""
        if entry_id.startswith(_ERROR_ID_PREFIX):
            message = _text(entries[0], f"{_ATOM}summary") or "ArXiv rejected the query."
            raise _FeedError(f"ArXiv API error: {message}")

    total_results = 0
    total_element = root.find(f"{_OPENSEARCH}totalResults")
    if total_element is not None and total_element.text:
        try:
            total_results = int(total_element.text.strip())
        except ValueError:
            total_results = 0

    return [_parse_entry(entry) for entry in entries], total_results


async def _fetch_feed(params: dict[str, Any]) -> tuple[list[ArxivPaper], int]:
    """Issue one arXiv query and return the parsed papers + total count.

    Raises ``_FeedError`` for every recoverable failure so each ``@tool``
    can convert it into its own typed ``success=False`` envelope.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(_ARXIV_API_URL, headers=_HEADERS, params=params)
    except httpx.TimeoutException as exc:
        raise _FeedError("Request to the ArXiv API timed out.") from exc
    except Exception as exc:
        raise _FeedError(f"Request to the ArXiv API failed: {exc}") from exc

    if response.status_code != 200:
        detail = response.text.strip()[:200]
        raise _FeedError(f"ArXiv API error ({response.status_code}): {detail}")

    return _parse_feed(response.text)


# --- Input schemas (args_schema for each @tool) ----------------------------


class SearchInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    search_query: str = Field(description="Search terms to look for on ArXiv")
    search_field: str = Field(
        default="all",
        description=(
            "Field to search in: 'all', 'ti' (title), 'au' (author), 'abs' (abstract), "
            "'co' (comment), 'jr' (journal reference), 'cat' (category), "
            "'rn' (report number)"
        ),
    )
    max_results: int = Field(default=10, description="Maximum number of results (1-2000)")
    sort_by: str = Field(
        default="relevance",
        description="Sort results by: 'relevance', 'lastUpdatedDate', or 'submittedDate'",
    )
    sort_order: str = Field(
        default="descending", description="Sort direction: 'descending' or 'ascending'"
    )
    start: int = Field(default=0, description="Zero-based index of the first result to return")


class GetPaperInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    paper_id: str = Field(
        description=(
            "ArXiv paper identifier, e.g. '1706.03762' or 'cs.AI/0001001'. "
            "A full https://arxiv.org/abs/... URL is also accepted."
        )
    )


class GetAuthorPapersInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    author_name: str = Field(description="Author name to search for, e.g. 'John Smith'")
    max_results: int = Field(default=10, description="Maximum number of results (1-2000)")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(
    search_query: str,
    search_field: str = "all",
    max_results: int = 10,
    sort_by: str = "relevance",
    sort_order: str = "descending",
    start: int = 0,
    api_key: str | None = None,
) -> SearchOutput:
    """Search for academic papers on ArXiv by keywords, authors, titles, or other fields."""
    if not search_query or not search_query.strip():
        return SearchOutput(success=False, error="search_query is required and cannot be empty.")

    query = search_query.strip()
    field = (search_field or "all").strip()
    if field in _SEARCH_FIELDS and field != "all":
        query = f"{field}:{query}"

    params: dict[str, Any] = {
        "search_query": query,
        "start": max(start, 0),
        "max_results": min(max(max_results, 1), _MAX_RESULTS_CAP),
    }
    if sort_by:
        params["sortBy"] = sort_by
    if sort_order:
        params["sortOrder"] = sort_order

    try:
        papers, total_results = await _fetch_feed(params)
    except _FeedError as exc:
        return SearchOutput(success=False, error=str(exc))

    return SearchOutput(
        success=True,
        papers=papers,
        total_results=total_results,
        query=query,
    )


@tool(args_schema=GetPaperInput)
@serialize_pydantic_return
async def get_paper(paper_id: str, api_key: str | None = None) -> GetPaperOutput:
    """Get detailed information about a specific ArXiv paper by its ID."""
    if not paper_id or not paper_id.strip():
        return GetPaperOutput(success=False, error="paper_id is required and cannot be empty.")

    identifier = paper_id.strip()
    if "arxiv.org/abs/" in identifier:
        identifier = identifier.split("arxiv.org/abs/", 1)[1]

    try:
        papers, _ = await _fetch_feed({"id_list": identifier})
    except _FeedError as exc:
        return GetPaperOutput(success=False, error=str(exc))

    if not papers:
        return GetPaperOutput(
            success=False, error=f"No ArXiv paper found for id '{identifier}'."
        )

    return GetPaperOutput(success=True, paper=papers[0])


@tool(args_schema=GetAuthorPapersInput)
@serialize_pydantic_return
async def get_author_papers(
    author_name: str, max_results: int = 10, api_key: str | None = None
) -> GetAuthorPapersOutput:
    """Search for papers by a specific author on ArXiv, newest submissions first."""
    if not author_name or not author_name.strip():
        return GetAuthorPapersOutput(
            success=False, error="author_name is required and cannot be empty."
        )

    # Quotes delimit the phrase in the search_query grammar, so any quote
    # inside the name is dropped rather than allowed to end the phrase.
    name = author_name.replace('"', "").strip()
    if not name:
        return GetAuthorPapersOutput(
            success=False, error="author_name is required and cannot be empty."
        )

    params: dict[str, Any] = {
        "search_query": f'au:"{name}"',
        "max_results": min(max(max_results, 1), _MAX_RESULTS_CAP),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    try:
        papers, total_results = await _fetch_feed(params)
    except _FeedError as exc:
        return GetAuthorPapersOutput(success=False, error=str(exc))

    return GetAuthorPapersOutput(
        success=True,
        author_papers=papers,
        total_results=total_results,
        author_name=name,
    )
