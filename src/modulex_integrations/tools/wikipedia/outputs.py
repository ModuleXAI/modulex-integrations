"""Pydantic response models for the Wikipedia integration's @tool functions.

Two Wikipedia APIs back these models and both answer with JSON:

- the Wikimedia REST API (``/api/rest_v1/page/summary/...`` and
  ``/api/rest_v1/page/random/summary``) for page summaries;
- the MediaWiki core REST API (``/w/rest.php/v1/search/page`` and
  ``/w/rest.php/v1/page/{title}/with_html``) for search and page HTML.

Every field is optional. Wikipedia omits whole blocks depending on the
article (no ``thumbnail`` on a text-only page, no ``coordinates`` outside
geo articles, ``matched_title``/``description`` null on many search hits),
so the models mirror the permissive ``.get()`` reading done in
``tools.py`` rather than the happy-path article.

Error model: a missing page (HTTP 404), a rejected parameter (HTTP 400), a
timeout, a non-JSON body and an unexpected body shape are all surfaced as
``success=False`` + ``error`` — nothing raises past the ``@tool``
boundary.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ContentOutput",
    "RandomOutput",
    "SearchOutput",
    "SummaryOutput",
    "WikipediaContentUrl",
    "WikipediaContentUrls",
    "WikipediaCoordinates",
    "WikipediaImage",
    "WikipediaPageContent",
    "WikipediaPageSummary",
    "WikipediaRandomPage",
    "WikipediaSearchResult",
    "WikipediaSearchThumbnail",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class WikipediaImage(_Base):
    """A ``thumbnail`` or ``originalimage`` block on a page summary."""

    source: str | None = None
    width: int | None = None
    height: int | None = None


class WikipediaContentUrl(_Base):
    """The desktop or mobile URL set for one page."""

    page: str | None = None
    revisions: str | None = None
    edit: str | None = None
    talk: str | None = None


class WikipediaContentUrls(_Base):
    desktop: WikipediaContentUrl | None = None
    mobile: WikipediaContentUrl | None = None


class WikipediaCoordinates(_Base):
    """Geographic coordinates, present only on articles about places."""

    lat: float | None = None
    lon: float | None = None


class WikipediaPageSummary(_Base):
    """A page summary: lead extract plus article metadata.

    ``type`` distinguishes an ordinary article (``standard``) from a
    ``disambiguation`` page and from ``no-extract``/``mainpage`` variants,
    so a caller can tell "the title was ambiguous" from "here is the
    article".
    """

    type: str | None = None
    title: str | None = None
    displaytitle: str | None = None
    description: str | None = None
    extract: str | None = None
    extract_html: str | None = None
    thumbnail: WikipediaImage | None = None
    originalimage: WikipediaImage | None = None
    content_urls: WikipediaContentUrls | None = None
    lang: str | None = None
    dir: str | None = None
    timestamp: str | None = None
    pageid: int | None = None
    wikibase_item: str | None = None
    coordinates: WikipediaCoordinates | None = None


class WikipediaSearchThumbnail(_Base):
    """The thumbnail block attached to a search hit."""

    mimetype: str | None = None
    size: int | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None
    url: str | None = None


class WikipediaSearchResult(_Base):
    """One search hit.

    ``excerpt`` is HTML: matched terms are wrapped in
    ``<span class="searchmatch">`` by the search backend.
    """

    id: int | None = None
    key: str | None = None
    title: str | None = None
    excerpt: str | None = None
    matched_title: str | None = None
    description: str | None = None
    thumbnail: WikipediaSearchThumbnail | None = None
    url: str | None = None


class WikipediaPageContent(_Base):
    """A page's rendered HTML plus its revision metadata.

    ``truncated`` reports whether ``html`` was cut to the requested
    maximum length — full articles routinely exceed a megabyte of HTML.
    """

    title: str | None = None
    pageid: int | None = None
    html: str | None = None
    html_length: int | None = None
    truncated: bool = False
    revision: int | None = None
    tid: str | None = None
    timestamp: str | None = None
    content_model: str | None = None
    content_format: str | None = None


class WikipediaRandomPage(_Base):
    """A randomly selected page, summarized."""

    type: str | None = None
    title: str | None = None
    displaytitle: str | None = None
    description: str | None = None
    extract: str | None = None
    thumbnail: WikipediaImage | None = None
    content_urls: WikipediaContentUrls | None = None
    lang: str | None = None
    timestamp: str | None = None
    pageid: int | None = None


# --- Per-action output models ----------------------------------------------


class SummaryOutput(_Base):
    success: bool
    error: str | None = None
    summary: WikipediaPageSummary | None = None


class SearchOutput(_Base):
    success: bool
    error: str | None = None
    search_results: list[WikipediaSearchResult] = Field(default_factory=list)
    total_hits: int = 0
    query: str | None = None


class ContentOutput(_Base):
    success: bool
    error: str | None = None
    content: WikipediaPageContent | None = None


class RandomOutput(_Base):
    success: bool
    error: str | None = None
    random_page: WikipediaRandomPage | None = None
