"""LaTeX LangChain ``@tool`` functions.

Three async tools wrapping the public LaTeX-on-HTTP API at
``https://latex.ytotech.com``. The API is open — it takes no API key, no
OAuth token, and no other credential — so the functions below declare only
their action parameters plus an ``api_key`` argument that exists for
signature uniformity with the credential system and is ignored.

Transport notes:

- ``GET /packages`` answers with ``{"packages": [...]}`` covering the whole
  installed TeX Live tree (~5000 entries) and ``GET /fonts`` with
  ``{"fonts": [...]}`` covering every font on the compiler host (~2700
  entries). Neither endpoint takes a query parameter, so filtering and
  truncation happen here, and ``total_matches`` reports how many entries
  matched before truncation.
- ``GET /packages/<name>`` answers with ``{"package": {...}}`` using TeX
  Live's own key names, or ``404`` with ``{"error": "Package not found"}``.
- Failures are never raised across the ``@tool`` boundary: non-200
  statuses, timeouts, non-JSON bodies, and wrong-typed fields all end up as
  ``success=False`` + ``error``.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.latex.outputs import (
    GetPackageOutput,
    LatexFont,
    LatexPackageDetails,
    LatexPackageSummary,
    ListFontsOutput,
    SearchPackagesOutput,
)

__all__ = ["get_package", "list_fonts", "search_packages"]

_BASE_URL = "https://latex.ytotech.com"

# Both listing endpoints return the complete catalogue in one response
# (roughly a megabyte of JSON for /packages), so the timeout is generous.
_TIMEOUT = 60.0

_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "modulex-integrations/1.0 (+https://modulex.dev)",
}

_SEARCH_DEFAULT_MAX_RESULTS = 25
_SEARCH_MAX_RESULTS_LIMIT = 100
_FONTS_DEFAULT_MAX_RESULTS = 50
_FONTS_MAX_RESULTS_LIMIT = 200

# TeX Live package names are ASCII words plus ``. _ + -`` (``12many``,
# ``texworks.win32``, ``translation-biblatex-de``). Anchoring the name
# before it reaches the request path keeps segments such as ``..`` and any
# escaped separator out of the URL entirely.
_PACKAGE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,99}$")


# --- Parse guards ----------------------------------------------------------


def _as_dict(payload: Any) -> dict[str, Any]:
    """A non-object body (or member) degrades to empty rather than raising."""
    return payload if isinstance(payload, dict) else {}


def _as_list(value: Any) -> list[Any]:
    """A non-array value degrades to empty rather than raising."""
    return value if isinstance(value, list) else []


def _as_str(value: Any) -> str | None:
    if value is None or isinstance(value, dict | list):
        return None
    return value if isinstance(value, str) else str(value)


def _as_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _as_str_list(value: Any) -> list[str]:
    return [text for text in (_as_str(item) for item in _as_list(value)) if text is not None]


def _clamp(requested: int, default: int, limit: int) -> int:
    """Mirror the upstream defaults: non-positive means "use the default"."""
    if requested <= 0:
        return default
    return min(requested, limit)


# --- Transport -------------------------------------------------------------


class _ApiError(Exception):
    """A recoverable failure each ``@tool`` converts into its own envelope."""


async def _get_json(path: str) -> dict[str, Any]:
    """Issue one GET against the LaTeX-on-HTTP API and return its JSON object.

    Raises ``_ApiError`` for every recoverable failure so each ``@tool`` can
    convert it into its own typed ``success=False`` envelope.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}{path}", headers=_HEADERS)
    except httpx.TimeoutException as exc:
        raise _ApiError("Request to the LaTeX-on-HTTP API timed out.") from exc
    except Exception as exc:
        raise _ApiError(f"Request to the LaTeX-on-HTTP API failed: {exc}") from exc

    try:
        payload = _as_dict(response.json())
    except Exception:
        payload = {}

    if response.status_code != 200:
        detail = _as_str(payload.get("error")) or response.text.strip()[:200]
        raise _ApiError(f"LaTeX-on-HTTP API error ({response.status_code}): {detail}")

    error = _as_str(payload.get("error"))
    if error:
        raise _ApiError(error)

    return payload


# --- Entity parsers (the single coercion chokepoint per entity) ------------


def _parse_package_summary(entry: dict[str, Any]) -> LatexPackageSummary:
    return LatexPackageSummary(
        name=_as_str(entry.get("name")),
        short_description=_as_str(entry.get("shortdesc")),
        installed=_as_bool(entry.get("installed")),
        ctan_url=_as_str(entry.get("url_ctan")),
    )


def _parse_package_details(entry: dict[str, Any]) -> LatexPackageDetails:
    # ``cat-related`` is a single whitespace-separated string upstream.
    related = _as_str(entry.get("cat-related")) or ""
    return LatexPackageDetails(
        name=_as_str(entry.get("package")),
        installed=_as_bool(entry.get("installed")),
        short_description=_as_str(entry.get("shortdesc")),
        long_description=_as_str(entry.get("longdesc")),
        category=_as_str(entry.get("category")),
        license=_as_str(entry.get("cat-license")),
        topics=_as_str_list(entry.get("cat-topics")),
        related_packages=related.split(),
        homepage=_as_str(entry.get("cat-contact-home")),
        ctan_url=_as_str(entry.get("url_ctan")),
    )


def _parse_font(entry: dict[str, Any]) -> LatexFont:
    return LatexFont(
        family=_as_str(entry.get("family")),
        name=_as_str(entry.get("name")),
        styles=_as_str_list(entry.get("styles")),
    )


def _text(entry: dict[str, Any], key: str) -> str:
    """Lower-cased field text used for the client-side filters."""
    return (_as_str(entry.get(key)) or "").lower()


# --- Input schemas (args_schema for each @tool) ----------------------------


class SearchPackagesInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    query: str = Field(
        description="Search terms matched against package names and descriptions"
    )
    max_results: int = Field(
        default=_SEARCH_DEFAULT_MAX_RESULTS,
        description="Maximum number of packages to return (default: 25, max: 100)",
    )


class GetPackageInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    name: str = Field(description="Exact package name, e.g. amsmath, tikz, or biblatex")


class ListFontsInput(BaseModel):
    api_key: str | None = Field(default=None, description="Not used — public API")
    query: str | None = Field(
        default=None,
        description='Filter matched against font family and full font name, e.g. "Noto Serif"',
    )
    max_results: int = Field(
        default=_FONTS_DEFAULT_MAX_RESULTS,
        description="Maximum number of fonts to return (default: 50, max: 200)",
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=SearchPackagesInput)
@serialize_pydantic_return
async def search_packages(
    query: str,
    max_results: int = _SEARCH_DEFAULT_MAX_RESULTS,
    api_key: str | None = None,
) -> SearchPackagesOutput:
    """Search the TeX Live packages available to the LaTeX compiler by name or description."""
    needle = (query or "").strip().lower()
    if not needle:
        return SearchPackagesOutput(
            success=False, error="query is required and cannot be empty."
        )

    try:
        payload = await _get_json("/packages")
    except _ApiError as exc:
        return SearchPackagesOutput(success=False, error=str(exc))

    entries = [_as_dict(item) for item in _as_list(payload.get("packages"))]
    matches = [
        entry
        for entry in entries
        if needle in _text(entry, "name") or needle in _text(entry, "shortdesc")
    ]
    limit = _clamp(max_results, _SEARCH_DEFAULT_MAX_RESULTS, _SEARCH_MAX_RESULTS_LIMIT)

    return SearchPackagesOutput(
        success=True,
        packages=[_parse_package_summary(entry) for entry in matches[:limit]],
        total_matches=len(matches),
    )


@tool(args_schema=GetPackageInput)
@serialize_pydantic_return
async def get_package(name: str, api_key: str | None = None) -> GetPackageOutput:
    """Get details about a specific TeX Live package available to the LaTeX compiler."""
    package_name = (name or "").strip()
    if not package_name:
        return GetPackageOutput(success=False, error="name is required and cannot be empty.")
    if not _PACKAGE_NAME_RE.match(package_name):
        return GetPackageOutput(
            success=False,
            error=(
                f"'{package_name}' is not a valid TeX Live package name — names use "
                "only letters, digits and the characters . _ + -"
            ),
        )

    try:
        payload = await _get_json(f"/packages/{quote(package_name, safe='')}")
    except _ApiError as exc:
        return GetPackageOutput(success=False, error=str(exc))

    entry = _as_dict(payload.get("package"))
    if not _as_str(entry.get("package")):
        return GetPackageOutput(
            success=False, error=f"Package '{package_name}' was not found."
        )

    return GetPackageOutput(success=True, package=_parse_package_details(entry))


@tool(args_schema=ListFontsInput)
@serialize_pydantic_return
async def list_fonts(
    query: str | None = None,
    max_results: int = _FONTS_DEFAULT_MAX_RESULTS,
    api_key: str | None = None,
) -> ListFontsOutput:
    """List the system fonts available to the LaTeX compiler, optionally filtered by name."""
    needle = (query or "").strip().lower()

    try:
        payload = await _get_json("/fonts")
    except _ApiError as exc:
        return ListFontsOutput(success=False, error=str(exc))

    entries = [_as_dict(item) for item in _as_list(payload.get("fonts"))]
    matches = [
        entry
        for entry in entries
        if not needle or needle in _text(entry, "family") or needle in _text(entry, "name")
    ]
    limit = _clamp(max_results, _FONTS_DEFAULT_MAX_RESULTS, _FONTS_MAX_RESULTS_LIMIT)

    return ListFontsOutput(
        success=True,
        fonts=[_parse_font(entry) for entry in matches[:limit]],
        total_matches=len(matches),
    )
