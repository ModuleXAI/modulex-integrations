"""Firecrawl LangChain ``@tool`` functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.firecrawl.outputs import (
    BatchScrapeOutput,
    CheckCrawlStatusOutput,
    CrawlOutput,
    ExtractOutput,
    MapWebsiteOutput,
    ScrapeOutput,
    SearchOutput,
)

__all__ = [
    "batch_scrape",
    "check_crawl_status",
    "crawl",
    "extract",
    "map_website",
    "scrape",
    "search",
]

_BASE_URL = "https://api.firecrawl.dev/v1"
# Firecrawl can be slow on big crawls / extract jobs; legacy used
# 120s for most actions and 180s for crawl/extract/batch.
_TIMEOUT = 120.0
_LONG_TIMEOUT = 180.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _clean(params: dict[str, Any]) -> dict[str, Any]:
    """Drop Nones, empty strings, empty lists, empty dicts."""
    out: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, dict)) and not value:
            continue
        out[key] = value
    return out


def _empty_key_error(name: str) -> str:
    return (
        f"Firecrawl API key is empty for {name}. "
        "Please configure a valid Firecrawl credential."
    )


async def _post_json(
    path: str, api_key: str, body: dict[str, Any], timeout: float = _TIMEOUT
) -> tuple[bool, str | None, dict[str, Any] | None]:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{_BASE_URL}{path}", headers=_headers(api_key), json=body
            )
        if response.status_code not in (200, 201):
            return False, (
                f"{path} failed with status {response.status_code}: {response.text}"
            ), None
        parsed = response.json() or {}
    except Exception as exc:
        return False, f"{path} request failed: {exc}", None
    if not isinstance(parsed, dict):
        return True, None, {"value": parsed}
    return True, None, parsed


async def _get_json(
    path: str, api_key: str
) -> tuple[bool, str | None, dict[str, Any] | None]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}{path}", headers=_headers(api_key))
        if response.status_code != 200:
            return False, (
                f"{path} failed with status {response.status_code}: {response.text}"
            ), None
        parsed = response.json() or {}
    except Exception as exc:
        return False, f"{path} request failed: {exc}", None
    if not isinstance(parsed, dict):
        return True, None, {"value": parsed}
    return True, None, parsed


# --- Input schemas ---------------------------------------------------------


class ScrapeInput(BaseModel):
    url: str = Field(description="The URL to scrape")
    api_key: str = Field(description="Firecrawl API key (provided by credential system)")
    formats: list[str] | None = Field(default=["markdown"], description="Output formats")
    only_main_content: bool | None = Field(default=True, description="Filter chrome")
    include_tags: list[str] | None = Field(default=None, description="HTML tag include list")
    exclude_tags: list[str] | None = Field(default=None, description="HTML tag exclude list")
    wait_for: int | None = Field(default=None, description="ms to wait for dynamic content")
    mobile: bool | None = Field(default=None, description="Use mobile viewport")
    remove_base64_images: bool | None = Field(default=None, description="Strip base64 images")
    max_age: int | None = Field(default=None, description="Cache max age in ms")


class MapInput(BaseModel):
    url: str = Field(description="Starting URL for URL discovery")
    api_key: str = Field(description="Firecrawl API key (provided by credential system)")
    search: str | None = Field(default=None, description="Filter URLs by search term")
    sitemap: str | None = Field(default=None, description="'include', 'skip', or 'only'")
    include_subdomains: bool | None = Field(default=None, description="Include subdomains")
    limit: int | None = Field(default=None, description="Max URLs to return")
    ignore_query_parameters: bool | None = Field(
        default=True, description="Drop URLs with query params"
    )


class SearchInput(BaseModel):
    query: str = Field(description="Search query")
    api_key: str = Field(description="Firecrawl API key (provided by credential system)")
    limit: int | None = Field(default=5, description="Max results")
    tbs: str | None = Field(default=None, description="Time-based filter")
    location: str | None = Field(default=None, description="Location parameter")
    scrape_options: dict[str, Any] | None = Field(
        default=None, description="Options for scraping search results"
    )


class CrawlInput(BaseModel):
    url: str = Field(description="Starting URL for the crawl")
    api_key: str = Field(description="Firecrawl API key (provided by credential system)")
    exclude_paths: list[str] | None = Field(default=None, description="Paths to skip")
    include_paths: list[str] | None = Field(default=None, description="Only crawl these")
    max_depth: int | None = Field(default=None, description="Max recursion depth")
    limit: int | None = Field(default=100, description="Max pages to crawl")
    allow_external_links: bool | None = Field(default=False, description="Allow external")
    allow_backward_links: bool | None = Field(default=False, description="Allow backward")
    ignore_sitemap: bool | None = Field(default=False, description="Ignore sitemap")
    scrape_options: dict[str, Any] | None = Field(
        default=None, description="Per-page scrape options"
    )


class CheckCrawlStatusInput(BaseModel):
    crawl_id: str = Field(description="Crawl job ID to check")
    api_key: str = Field(description="Firecrawl API key (provided by credential system)")


class ExtractInput(BaseModel):
    urls: list[str] = Field(description="URLs to extract from")
    api_key: str = Field(description="Firecrawl API key (provided by credential system)")
    prompt: str | None = Field(default=None, description="Custom LLM prompt")
    schema_definition: dict[str, Any] | None = Field(
        default=None, description="JSON schema for structured output"
    )
    allow_external_links: bool | None = Field(default=False, description="Allow external")
    enable_web_search: bool | None = Field(default=False, description="Enable web search")
    include_subdomains: bool | None = Field(default=False, description="Include subdomains")


class BatchScrapeInput(BaseModel):
    urls: list[str] = Field(description="URLs to scrape")
    api_key: str = Field(description="Firecrawl API key (provided by credential system)")
    formats: list[str] | None = Field(default=["markdown"], description="Output formats")
    only_main_content: bool | None = Field(default=True, description="Filter chrome")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=ScrapeInput)
@serialize_pydantic_return
async def scrape(
    url: str,
    api_key: str,
    formats: list[str] | None = None,
    only_main_content: bool | None = True,
    include_tags: list[str] | None = None,
    exclude_tags: list[str] | None = None,
    wait_for: int | None = None,
    mobile: bool | None = None,
    remove_base64_images: bool | None = None,
    max_age: int | None = None,
) -> ScrapeOutput:
    """Scrape content from a single URL via Firecrawl."""
    if not api_key or not api_key.strip():
        return ScrapeOutput(success=False, error=_empty_key_error("scrape"))

    body = _clean(
        {
            "url": url,
            "formats": formats or ["markdown"],
            "onlyMainContent": only_main_content,
            "includeTags": include_tags,
            "excludeTags": exclude_tags,
            "waitFor": wait_for,
            "mobile": mobile,
            "removeBase64Images": remove_base64_images,
            "maxAge": max_age,
        }
    )

    ok, err, data = await _post_json("/scrape", api_key, body)
    return ScrapeOutput(success=ok, error=err, data=data)


@tool(args_schema=MapInput)
@serialize_pydantic_return
async def map_website(
    url: str,
    api_key: str,
    search: str | None = None,
    sitemap: str | None = None,
    include_subdomains: bool | None = None,
    limit: int | None = None,
    ignore_query_parameters: bool | None = True,
) -> MapWebsiteOutput:
    """Map a website to discover all indexed URLs."""
    if not api_key or not api_key.strip():
        return MapWebsiteOutput(success=False, error=_empty_key_error("map_website"))

    body = _clean(
        {
            "url": url,
            "search": search,
            "sitemap": sitemap,
            "includeSubdomains": include_subdomains,
            "limit": limit,
            "ignoreQueryParameters": ignore_query_parameters,
        }
    )

    ok, err, data = await _post_json("/map", api_key, body)
    return MapWebsiteOutput(success=ok, error=err, data=data)


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(
    query: str,
    api_key: str,
    limit: int | None = 5,
    tbs: str | None = None,
    location: str | None = None,
    scrape_options: dict[str, Any] | None = None,
) -> SearchOutput:
    """Search the web via Firecrawl."""
    if not api_key or not api_key.strip():
        return SearchOutput(success=False, error=_empty_key_error("search"))

    body = _clean(
        {
            "query": query,
            "limit": limit,
            "tbs": tbs,
            "location": location,
            "scrapeOptions": scrape_options,
        }
    )

    ok, err, data = await _post_json("/search", api_key, body)
    return SearchOutput(success=ok, error=err, data=data)


@tool(args_schema=CrawlInput)
@serialize_pydantic_return
async def crawl(
    url: str,
    api_key: str,
    exclude_paths: list[str] | None = None,
    include_paths: list[str] | None = None,
    max_depth: int | None = None,
    limit: int | None = 100,
    allow_external_links: bool | None = False,
    allow_backward_links: bool | None = False,
    ignore_sitemap: bool | None = False,
    scrape_options: dict[str, Any] | None = None,
) -> CrawlOutput:
    """Start a crawl job on a website. Returns a job id."""
    if not api_key or not api_key.strip():
        return CrawlOutput(success=False, error=_empty_key_error("crawl"))

    body = _clean(
        {
            "url": url,
            "excludePaths": exclude_paths,
            "includePaths": include_paths,
            "maxDepth": max_depth,
            "limit": limit,
            "allowExternalLinks": allow_external_links,
            "allowBackwardLinks": allow_backward_links,
            "ignoreSitemap": ignore_sitemap,
            "scrapeOptions": scrape_options,
        }
    )

    ok, err, data = await _post_json("/crawl", api_key, body, timeout=_LONG_TIMEOUT)
    return CrawlOutput(success=ok, error=err, data=data)


@tool(args_schema=CheckCrawlStatusInput)
@serialize_pydantic_return
async def check_crawl_status(crawl_id: str, api_key: str) -> CheckCrawlStatusOutput:
    """Check the status of a crawl job."""
    if not api_key or not api_key.strip():
        return CheckCrawlStatusOutput(
            success=False, error=_empty_key_error("check_crawl_status")
        )

    ok, err, data = await _get_json(f"/crawl/{crawl_id}", api_key)
    return CheckCrawlStatusOutput(success=ok, error=err, data=data)


@tool(args_schema=ExtractInput)
@serialize_pydantic_return
async def extract(
    urls: list[str],
    api_key: str,
    prompt: str | None = None,
    schema_definition: dict[str, Any] | None = None,
    allow_external_links: bool | None = False,
    enable_web_search: bool | None = False,
    include_subdomains: bool | None = False,
) -> ExtractOutput:
    """Extract structured info from web pages via LLM."""
    if not api_key or not api_key.strip():
        return ExtractOutput(success=False, error=_empty_key_error("extract"))

    body = _clean(
        {
            "urls": urls,
            "prompt": prompt,
            "schema": schema_definition,
            "allowExternalLinks": allow_external_links,
            "enableWebSearch": enable_web_search,
            "includeSubdomains": include_subdomains,
        }
    )

    ok, err, data = await _post_json("/extract", api_key, body, timeout=_LONG_TIMEOUT)
    return ExtractOutput(success=ok, error=err, data=data)


@tool(args_schema=BatchScrapeInput)
@serialize_pydantic_return
async def batch_scrape(
    urls: list[str],
    api_key: str,
    formats: list[str] | None = None,
    only_main_content: bool | None = True,
) -> BatchScrapeOutput:
    """Scrape multiple URLs in one job."""
    if not api_key or not api_key.strip():
        return BatchScrapeOutput(
            success=False, error=_empty_key_error("batch_scrape")
        )

    body = _clean(
        {
            "urls": urls,
            "formats": formats or ["markdown"],
            "onlyMainContent": only_main_content,
        }
    )

    ok, err, data = await _post_json(
        "/batch/scrape", api_key, body, timeout=_LONG_TIMEOUT
    )
    return BatchScrapeOutput(success=ok, error=err, data=data)
