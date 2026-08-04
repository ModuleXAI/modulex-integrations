"""Wikipedia LangChain ``@tool`` functions.

Four async tools over the public Wikipedia APIs. Two API families are
used, each for what it does best:

- **Wikimedia REST API** (``https://<lang>.wikipedia.org/api/rest_v1``)
  — ``/page/summary/{title}`` and ``/page/random/summary``. This is the
  service that produces the lead extract, description, thumbnail,
  ``content_urls`` and the ``type`` discriminator that flags a
  disambiguation page.
- **MediaWiki core REST API** (``https://<lang>.wikipedia.org/w/rest.php/v1``)
  — ``/search/page`` and ``/page/{title}/with_html``. Search returns
  highlighted excerpts, short descriptions and thumbnails; ``with_html``
  returns the rendered article HTML together with the page id, title and
  latest-revision metadata in a single JSON response.

Transport notes:

- Wikipedia is fully open: no API key, no OAuth token, no credential of
  any kind. Each function accepts ``api_key`` for signature uniformity
  with the credential system and ignores it.
- Redirects are followed. ``/page/random/summary`` answers ``303`` with a
  ``Location`` pointing at the drawn article, and ``with_html`` answers
  ``307`` when the requested title is a redirect page, so
  ``follow_redirects=True`` is required rather than cosmetic.
- Wikimedia requires a descriptive ``User-Agent`` carrying a contact URL
  and rate-limits or blocks generic ones, so every request sends
  ``modulex-integrations/1.0 (+https://modulex.dev)``.
- ``language`` selects the wiki and therefore lands in the request host.
  It is matched against an anchored pattern before use, so the only host
  reachable from these tools is ``<language>.wikipedia.org``.
- Nothing raises past the ``@tool`` boundary: a missing page (404), a
  rejected parameter (400), a timeout, a non-JSON body, and a body whose
  shape or field types differ from the documented ones all come back as
  ``success=False`` + ``error``, or as ``None``-valued fields.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.wikipedia.outputs import (
    ContentOutput,
    RandomOutput,
    SearchOutput,
    SummaryOutput,
    WikipediaContentUrl,
    WikipediaContentUrls,
    WikipediaCoordinates,
    WikipediaImage,
    WikipediaPageContent,
    WikipediaPageSummary,
    WikipediaRandomPage,
    WikipediaSearchResult,
    WikipediaSearchThumbnail,
)

__all__ = ["content", "random", "search", "summary"]

_TIMEOUT = 30.0

# Wikimedia's User-Agent policy asks automated clients for a tool name,
# a version and a contact URL; generic agents are throttled or refused.
_HEADERS = {
    "User-Agent": "modulex-integrations/1.0 (+https://modulex.dev)",
    "Accept": "application/json",
}

_DEFAULT_LANGUAGE = "en"

# The language code lands in the request host (``<language>.wikipedia.org``),
# which makes it an SSRF vector: it is LLM-facing and a value such as
# ``en@attacker.example`` would otherwise redirect the whole request to a
# host of the caller's choosing. Wikipedia has ~340 language editions with
# codes ranging from ``tr`` through ``simple`` to ``zh-min-nan``, so the set
# is too open-ended for a literal map; instead the value is anchored to
# lowercase letters, digits and interior hyphens only. Nothing matching this
# pattern can terminate the host early or introduce a new one, so the only
# reachable netloc is a wikipedia.org subdomain.
_LANGUAGE_PATTERN = re.compile(r"^[a-z]{2,10}(?:-[a-z0-9]{2,10}){0,2}$")

_DEFAULT_SEARCH_LIMIT = 10
_MAX_SEARCH_LIMIT = 100  # the /search/page endpoint rejects limit > 100

_DEFAULT_MAX_HTML_LENGTH = 100_000

_HTML_CONTENT_FORMAT = "text/html"


class _WikipediaError(Exception):
    """A recoverable failure that each ``@tool`` turns into its envelope.

    ``status_code`` carries the upstream HTTP status when there was one, so
    an action can special-case it — a ``404`` on a page endpoint means "no
    such article", which is worth saying plainly.
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


# --- Request helpers -------------------------------------------------------


def _wiki_base_url(language: str) -> str:
    """Return the wiki base URL for a validated language code.

    Raises ``_WikipediaError`` when the code does not match the anchored
    pattern, so an unvalidated value can never reach the host.
    """
    normalized = (language or _DEFAULT_LANGUAGE).strip().lower()
    if not normalized:
        normalized = _DEFAULT_LANGUAGE
    if not _LANGUAGE_PATTERN.fullmatch(normalized):
        raise _WikipediaError(
            f"Invalid language code '{language}'. Use a Wikipedia language code "
            "such as 'en', 'tr', 'de' or 'zh-min-nan'."
        )
    return f"https://{normalized}.wikipedia.org"


def _encode_title(page_title: str) -> str:
    """Percent-encode an article title for use as a URL path segment.

    Spaces become underscores the way Wikipedia writes them, and every
    other character — including ``/`` in titles such as ``AC/DC`` and
    ``:`` in ``Portal:Science`` — is escaped so it cannot open a new path
    segment.
    """
    return quote(page_title.strip().replace(" ", "_"), safe="")


def _error_detail(response: httpx.Response) -> str:
    """Pull a human-readable message out of an error response body."""
    try:
        payload: Any = response.json()
    except Exception:
        return response.text.strip()[:300]

    if isinstance(payload, dict):
        translations = payload.get("messageTranslations")
        if isinstance(translations, dict):
            english = translations.get("en")
            if isinstance(english, str) and english.strip():
                return english.strip()[:300]
        for key in ("detail", "title", "error", "message"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:300]

    return response.text.strip()[:300]


async def _get(url: str, params: dict[str, Any] | None = None) -> httpx.Response:
    """Issue one GET against Wikipedia, following redirects.

    Raises ``_WikipediaError`` for every recoverable failure so each
    ``@tool`` can convert it into its own typed ``success=False``
    envelope.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url, headers=_HEADERS, params=params)
    except httpx.TimeoutException as exc:
        raise _WikipediaError("Request to the Wikipedia API timed out.") from exc
    except Exception as exc:
        raise _WikipediaError(f"Request to the Wikipedia API failed: {exc}") from exc

    if response.status_code != 200:
        raise _WikipediaError(
            f"Wikipedia API error ({response.status_code}): {_error_detail(response)}",
            status_code=response.status_code,
        )
    return response


def _missing_page_error(page_title: str) -> str:
    """The message used when a page endpoint answers 404.

    Wikipedia's own 404 body is unhelpful — the cached summary endpoint
    returns ``{"status": 404, "type": "Internal error"}`` — and an agent
    that reads it verbatim reports a server fault instead of a missing
    article.
    """
    return f"Wikipedia has no page titled '{page_title.strip()}' (HTTP 404)."


def _json_body(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception as exc:
        raise _WikipediaError(
            f"Wikipedia returned a response that is not valid JSON: {exc}"
        ) from exc


# --- Parse guards ----------------------------------------------------------
#
# Everything between the JSON parse and the ``return`` runs outside the
# ``try``/``except``, so it must not be able to raise. Two failure modes are
# covered: a body whose *shape* is not what the endpoint documents (a bare
# array, a string, ``null``), and a field whose *type* differs from the model
# (a number where a string is declared). The first is handled by ``_as_dict``,
# the second by the scalar coercers below — applied inside the ``_parse_*``
# helpers so each entity has a single chokepoint. No documented field of
# these four endpoints is a boolean, so there is no ``_as_bool``; the one
# boolean in ``outputs.py`` (``truncated``) is computed locally, never read
# off the wire.


def _as_dict(payload: Any) -> dict[str, Any]:
    """A non-object body degrades to empty rather than raising."""
    return payload if isinstance(payload, dict) else {}


def _as_str(value: Any) -> str | None:
    if value is None or isinstance(value, dict | list):
        return None
    return value if isinstance(value, str) else str(value)


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _as_url(value: Any) -> str | None:
    """Normalize a URL, expanding the protocol-relative form Wikipedia uses.

    Search thumbnails come back as ``//upload.wikimedia.org/...``, which is
    not fetchable on its own.
    """
    url = _as_str(value)
    if url is None:
        return None
    return f"https:{url}" if url.startswith("//") else url


# --- Entity parsers --------------------------------------------------------


def _parse_image(raw: Any) -> WikipediaImage | None:
    data = _as_dict(raw)
    if not data:
        return None
    return WikipediaImage(
        source=_as_url(data.get("source")),
        width=_as_int(data.get("width")),
        height=_as_int(data.get("height")),
    )


def _parse_content_url(raw: Any) -> WikipediaContentUrl | None:
    data = _as_dict(raw)
    if not data:
        return None
    return WikipediaContentUrl(
        page=_as_url(data.get("page")),
        revisions=_as_url(data.get("revisions")),
        edit=_as_url(data.get("edit")),
        talk=_as_url(data.get("talk")),
    )


def _parse_content_urls(raw: Any) -> WikipediaContentUrls | None:
    data = _as_dict(raw)
    if not data:
        return None
    return WikipediaContentUrls(
        desktop=_parse_content_url(data.get("desktop")),
        mobile=_parse_content_url(data.get("mobile")),
    )


def _parse_coordinates(raw: Any) -> WikipediaCoordinates | None:
    data = _as_dict(raw)
    if not data:
        return None
    return WikipediaCoordinates(
        lat=_as_float(data.get("lat")),
        lon=_as_float(data.get("lon")),
    )


def _parse_summary(data: dict[str, Any]) -> WikipediaPageSummary:
    title = _as_str(data.get("title"))
    return WikipediaPageSummary(
        type=_as_str(data.get("type")),
        title=title,
        displaytitle=_as_str(data.get("displaytitle")) or title,
        description=_as_str(data.get("description")),
        extract=_as_str(data.get("extract")),
        extract_html=_as_str(data.get("extract_html")),
        thumbnail=_parse_image(data.get("thumbnail")),
        originalimage=_parse_image(data.get("originalimage")),
        content_urls=_parse_content_urls(data.get("content_urls")),
        lang=_as_str(data.get("lang")),
        dir=_as_str(data.get("dir")),
        timestamp=_as_str(data.get("timestamp")),
        pageid=_as_int(data.get("pageid")),
        wikibase_item=_as_str(data.get("wikibase_item")),
        coordinates=_parse_coordinates(data.get("coordinates")),
    )


def _parse_random_page(data: dict[str, Any]) -> WikipediaRandomPage:
    title = _as_str(data.get("title"))
    return WikipediaRandomPage(
        type=_as_str(data.get("type")),
        title=title,
        displaytitle=_as_str(data.get("displaytitle")) or title,
        description=_as_str(data.get("description")),
        extract=_as_str(data.get("extract")),
        thumbnail=_parse_image(data.get("thumbnail")),
        content_urls=_parse_content_urls(data.get("content_urls")),
        lang=_as_str(data.get("lang")),
        timestamp=_as_str(data.get("timestamp")),
        pageid=_as_int(data.get("pageid")),
    )


def _parse_search_thumbnail(raw: Any) -> WikipediaSearchThumbnail | None:
    data = _as_dict(raw)
    if not data:
        return None
    return WikipediaSearchThumbnail(
        mimetype=_as_str(data.get("mimetype")),
        size=_as_int(data.get("size")),
        width=_as_int(data.get("width")),
        height=_as_int(data.get("height")),
        duration=_as_int(data.get("duration")),
        url=_as_url(data.get("url")),
    )


def _parse_search_result(raw: Any, base_url: str) -> WikipediaSearchResult:
    data = _as_dict(raw)
    key = _as_str(data.get("key"))
    # /search/page returns the page key, not a URL; the article URL is
    # derived from it so callers get a link they can follow.
    url = f"{base_url}/wiki/{quote(key, safe='')}" if key else None
    return WikipediaSearchResult(
        id=_as_int(data.get("id")),
        key=key,
        title=_as_str(data.get("title")),
        excerpt=_as_str(data.get("excerpt")),
        matched_title=_as_str(data.get("matched_title")),
        description=_as_str(data.get("description")),
        thumbnail=_parse_search_thumbnail(data.get("thumbnail")),
        url=url,
    )


def _parse_page_content(
    data: dict[str, Any], etag: str | None, max_length: int
) -> WikipediaPageContent:
    latest = _as_dict(data.get("latest"))

    html = _as_str(data.get("html"))
    html_length = len(html) if html is not None else None
    truncated = False
    if html is not None and max_length > 0 and len(html) > max_length:
        html = html[:max_length]
        truncated = True

    return WikipediaPageContent(
        title=_as_str(data.get("title")),
        pageid=_as_int(data.get("id")),
        html=html,
        html_length=html_length,
        truncated=truncated,
        revision=_as_int(latest.get("id")),
        tid=_as_str(etag),
        timestamp=_as_str(latest.get("timestamp")),
        content_model=_as_str(data.get("content_model")),
        content_format=_HTML_CONTENT_FORMAT,
    )


# --- Input schemas (args_schema for each @tool) ----------------------------

_LANGUAGE_DESCRIPTION = (
    "Wikipedia language edition to query, e.g. 'en', 'tr', 'de', 'simple'. "
    "Defaults to 'en'."
)


class SummaryInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    page_title: str = Field(
        description=(
            "Title of the Wikipedia page to summarize, e.g. "
            "'Python (programming language)'"
        )
    )
    language: str = Field(default=_DEFAULT_LANGUAGE, description=_LANGUAGE_DESCRIPTION)


class SearchInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    query: str = Field(description="Search terms used to find Wikipedia pages")
    search_limit: int = Field(
        default=_DEFAULT_SEARCH_LIMIT,
        description="Maximum number of results to return (1-100, default 10)",
    )
    language: str = Field(default=_DEFAULT_LANGUAGE, description=_LANGUAGE_DESCRIPTION)


class ContentInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    page_title: str = Field(description="Title of the Wikipedia page to fetch content for")
    max_length: int = Field(
        default=_DEFAULT_MAX_HTML_LENGTH,
        description=(
            "Maximum number of HTML characters to return. Longer articles are "
            "truncated and the 'truncated' flag is set. Use 0 or a negative "
            "value to return the full article HTML."
        ),
    )
    language: str = Field(default=_DEFAULT_LANGUAGE, description=_LANGUAGE_DESCRIPTION)


class RandomInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    language: str = Field(default=_DEFAULT_LANGUAGE, description=_LANGUAGE_DESCRIPTION)


# --- @tool functions -------------------------------------------------------


@tool(args_schema=SummaryInput)
@serialize_pydantic_return
async def summary(
    page_title: str,
    language: str = _DEFAULT_LANGUAGE,
    api_key: str | None = None,
) -> SummaryOutput:
    """Get a summary and metadata for a specific Wikipedia page."""
    if not page_title or not page_title.strip():
        return SummaryOutput(success=False, error="page_title is required and cannot be empty.")

    try:
        base_url = _wiki_base_url(language)
        url = f"{base_url}/api/rest_v1/page/summary/{_encode_title(page_title)}"
        payload = _json_body(await _get(url))
    except _WikipediaError as exc:
        if exc.status_code == 404:
            return SummaryOutput(success=False, error=_missing_page_error(page_title))
        return SummaryOutput(success=False, error=str(exc))

    data = _as_dict(payload)
    if not data:
        return SummaryOutput(
            success=False,
            error="Wikipedia returned an unexpected response shape for the page summary.",
        )

    return SummaryOutput(success=True, summary=_parse_summary(data))


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(
    query: str,
    search_limit: int = _DEFAULT_SEARCH_LIMIT,
    language: str = _DEFAULT_LANGUAGE,
    api_key: str | None = None,
) -> SearchOutput:
    """Search for Wikipedia pages by title or content."""
    if not query or not query.strip():
        return SearchOutput(success=False, error="query is required and cannot be empty.")

    search_terms = query.strip()
    limit = min(max(search_limit, 1), _MAX_SEARCH_LIMIT)

    try:
        base_url = _wiki_base_url(language)
        params: dict[str, Any] = {"q": search_terms, "limit": limit}
        payload = _json_body(await _get(f"{base_url}/w/rest.php/v1/search/page", params=params))
    except _WikipediaError as exc:
        return SearchOutput(success=False, error=str(exc), query=search_terms)

    pages = _as_dict(payload).get("pages")
    if not isinstance(pages, list):
        return SearchOutput(
            success=False,
            error="Wikipedia returned an unexpected response shape for the search results.",
            query=search_terms,
        )

    results = [_parse_search_result(page, base_url) for page in pages]
    return SearchOutput(
        success=True,
        search_results=results,
        total_hits=len(results),
        query=search_terms,
    )


@tool(args_schema=ContentInput)
@serialize_pydantic_return
async def content(
    page_title: str,
    max_length: int = _DEFAULT_MAX_HTML_LENGTH,
    language: str = _DEFAULT_LANGUAGE,
    api_key: str | None = None,
) -> ContentOutput:
    """Get the full HTML content of a Wikipedia page."""
    if not page_title or not page_title.strip():
        return ContentOutput(success=False, error="page_title is required and cannot be empty.")

    try:
        base_url = _wiki_base_url(language)
        url = f"{base_url}/w/rest.php/v1/page/{_encode_title(page_title)}/with_html"
        response = await _get(url)
        payload = _json_body(response)
    except _WikipediaError as exc:
        if exc.status_code == 404:
            return ContentOutput(success=False, error=_missing_page_error(page_title))
        return ContentOutput(success=False, error=str(exc))

    data = _as_dict(payload)
    if not data:
        return ContentOutput(
            success=False,
            error="Wikipedia returned an unexpected response shape for the page content.",
        )

    return ContentOutput(
        success=True,
        content=_parse_page_content(data, response.headers.get("etag"), max_length),
    )


@tool(args_schema=RandomInput)
@serialize_pydantic_return
async def random(
    language: str = _DEFAULT_LANGUAGE,
    api_key: str | None = None,
) -> RandomOutput:
    """Get a random Wikipedia page with its summary."""
    try:
        base_url = _wiki_base_url(language)
        payload = _json_body(await _get(f"{base_url}/api/rest_v1/page/random/summary"))
    except _WikipediaError as exc:
        return RandomOutput(success=False, error=str(exc))

    data = _as_dict(payload)
    if not data:
        return RandomOutput(
            success=False,
            error="Wikipedia returned an unexpected response shape for the random page.",
        )

    return RandomOutput(success=True, random_page=_parse_random_page(data))
