"""Similarweb LangChain ``@tool`` functions.

Five async tools wrapping the Similarweb Web Traffic API. The modulex
``ToolExecutor`` injects an ``api_key: str`` directly (resolved from the
user's ``api_key`` credential); the credential is sent to Similarweb as
the ``api_key`` query-string parameter, not an HTTP header.

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions. Non-2xx responses do not raise.
"""
from __future__ import annotations

import re
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.similarweb.outputs import (
    BounceRateOutput,
    BounceRatePoint,
    PagesPerVisitOutput,
    PagesPerVisitPoint,
    TopCountryShare,
    TrafficSources,
    TrafficVisitsOutput,
    VisitDurationOutput,
    VisitDurationPoint,
    VisitPoint,
    WebsiteOverviewOutput,
)

__all__ = [
    "bounce_rate",
    "pages_per_visit",
    "traffic_visits",
    "visit_duration",
    "website_overview",
]

_BASE_URL = "https://api.similarweb.com/v1/website"
_TIMEOUT = 30.0
_EMPTY_KEY_ERROR = (
    "Similarweb API key is empty. Please configure a valid Similarweb credential."
)

_SCHEME_WWW = re.compile(r"^(https?://)?(www\.)?")


def _clean_domain(domain: str) -> str:
    """Strip protocol, leading ``www.`` and a trailing slash from a domain."""
    cleaned = _SCHEME_WWW.sub("", domain.strip())
    return cleaned.rstrip("/")


def _pick(data: dict[str, Any], *keys: str) -> Any:
    """Return the first present, non-null value among ``keys``."""
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return None


def _rank(data: dict[str, Any], object_key: str, scalar_key: str) -> Any:
    """Resolve a rank that may be an object ``{Rank: n}`` or a bare number."""
    container = data.get(object_key)
    if isinstance(container, dict) and container.get("Rank") is not None:
        return container.get("Rank")
    container = data.get(scalar_key)
    if isinstance(container, dict) and container.get("rank") is not None:
        return container.get("rank")
    raw = data.get(object_key)
    if isinstance(raw, (int, float)):
        return raw
    raw = data.get(scalar_key)
    if isinstance(raw, (int, float)):
        return raw
    return None


def _time_series_params(
    api_key: str,
    country: str,
    granularity: str,
    start_date: str | None,
    end_date: str | None,
    main_domain_only: bool | None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "api_key": api_key.strip(),
        "country": (country or "world").strip(),
        "granularity": granularity or "monthly",
        "format": "json",
    }
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if main_domain_only is not None:
        params["main_domain_only"] = str(main_domain_only).lower()
    return params


# --- Input schemas (args_schema for each @tool) ----------------------------


class WebsiteOverviewInput(BaseModel):
    domain: str = Field(
        description=(
            'Website domain to analyze (e.g., "example.com" without www or protocol)'
        )
    )
    api_key: str = Field(description="Similarweb API key (provided by credential system)")


class _TimeSeriesInput(BaseModel):
    domain: str = Field(
        description=(
            'Website domain to analyze (e.g., "example.com" without www or protocol)'
        )
    )
    api_key: str = Field(description="Similarweb API key (provided by credential system)")
    country: str = Field(
        default="world",
        description=(
            '2-letter ISO country code (e.g., "us", "gb", "de") or "world" '
            "for worldwide data"
        ),
    )
    granularity: str = Field(
        default="monthly",
        description="Data granularity: daily, weekly, or monthly",
    )
    start_date: str | None = Field(
        default=None, description='Start date in YYYY-MM format (e.g., "2024-01")'
    )
    end_date: str | None = Field(
        default=None, description='End date in YYYY-MM format (e.g., "2024-12")'
    )
    main_domain_only: bool | None = Field(
        default=None, description="Exclude subdomains from results"
    )


class TrafficVisitsInput(_TimeSeriesInput):
    pass


class BounceRateInput(_TimeSeriesInput):
    pass


class PagesPerVisitInput(_TimeSeriesInput):
    pass


class VisitDurationInput(_TimeSeriesInput):
    pass


# --- @tool functions -------------------------------------------------------


@tool(args_schema=WebsiteOverviewInput)
@serialize_pydantic_return
async def website_overview(domain: str, api_key: str) -> WebsiteOverviewOutput:
    """Get comprehensive website analytics: traffic, rankings, engagement, and traffic sources."""
    if not api_key or not api_key.strip():
        return WebsiteOverviewOutput(success=False, error=_EMPTY_KEY_ERROR)

    cleaned = _clean_domain(domain)
    url = f"{_BASE_URL}/{cleaned}/general-data/all"
    params: dict[str, Any] = {"api_key": api_key.strip(), "format": "json"}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                url, params=params, headers={"Accept": "application/json"}
            )
        if response.status_code != 200:
            return WebsiteOverviewOutput(
                success=False,
                error=f"Similarweb API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return WebsiteOverviewOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return WebsiteOverviewOutput(success=False, error=f"website_overview failed: {exc}")

    top_countries_raw = _pick(data, "TopCountryShares", "top_country_shares") or []
    top_countries: list[TopCountryShare] = []
    for item in top_countries_raw:
        if not isinstance(item, dict):
            continue
        country_code = _pick(item, "CountryCode", "country_code")
        if country_code is None:
            numeric = _pick(item, "Country", "country")
            country_code = str(numeric) if numeric is not None else None
        top_countries.append(
            TopCountryShare(
                country=country_code,
                share=_pick(item, "Value", "value"),
            )
        )

    sources = _pick(data, "TrafficSources", "traffic_sources") or {}
    if not isinstance(sources, dict):
        sources = {}
    traffic_sources = TrafficSources(
        direct=_pick(sources, "Direct", "direct"),
        referrals=_pick(sources, "Referrals", "referrals"),
        search=_pick(sources, "Search", "search"),
        social=_pick(sources, "Social", "social"),
        mail=_pick(sources, "Mail", "mail"),
        paid_referrals=_pick(sources, "Paid Referrals", "paid_referrals"),
    )

    engagements = _pick(data, "Engagements", "engagements", "engagments") or {}
    if not isinstance(engagements, dict):
        engagements = {}

    return WebsiteOverviewOutput(
        success=True,
        site_name=_pick(data, "SiteName", "site_name"),
        description=_pick(data, "Description", "description"),
        global_rank=_rank(data, "GlobalRank", "global_rank"),
        country_rank=_rank(data, "CountryRank", "country_rank"),
        category_rank=_rank(data, "CategoryRank", "category_rank"),
        category=_pick(data, "Category", "category"),
        monthly_visits=_pick(engagements, "Visits", "visits"),
        engagement_visit_duration=_pick(engagements, "TimeOnSite", "time_on_site"),
        engagement_pages_per_visit=_pick(engagements, "PagePerVisit", "page_per_visit"),
        engagement_bounce_rate=_pick(engagements, "BounceRate", "bounce_rate"),
        top_countries=top_countries,
        traffic_sources=traffic_sources,
    )


@tool(args_schema=TrafficVisitsInput)
@serialize_pydantic_return
async def traffic_visits(
    domain: str,
    api_key: str,
    country: str = "world",
    granularity: str = "monthly",
    start_date: str | None = None,
    end_date: str | None = None,
    main_domain_only: bool | None = None,
) -> TrafficVisitsOutput:
    """Get total website visits over time (desktop and mobile combined)."""
    if not api_key or not api_key.strip():
        return TrafficVisitsOutput(success=False, error=_EMPTY_KEY_ERROR)

    cleaned = _clean_domain(domain)
    url = f"{_BASE_URL}/{cleaned}/total-traffic-and-engagement/visits"
    params = _time_series_params(
        api_key, country, granularity, start_date, end_date, main_domain_only
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                url, params=params, headers={"Accept": "application/json"}
            )
        if response.status_code != 200:
            return TrafficVisitsOutput(
                success=False,
                error=f"Similarweb API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return TrafficVisitsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return TrafficVisitsOutput(success=False, error=f"traffic_visits failed: {exc}")

    meta = data.get("meta") or {}
    request_meta = meta.get("request") or {}
    points = [
        VisitPoint(date=item.get("date"), visits=item.get("visits"))
        for item in (data.get("visits") or [])
        if isinstance(item, dict)
    ]

    return TrafficVisitsOutput(
        success=True,
        domain=request_meta.get("domain"),
        country=request_meta.get("country"),
        granularity=request_meta.get("granularity"),
        last_updated=meta.get("last_updated"),
        visits=points,
    )


@tool(args_schema=BounceRateInput)
@serialize_pydantic_return
async def bounce_rate(
    domain: str,
    api_key: str,
    country: str = "world",
    granularity: str = "monthly",
    start_date: str | None = None,
    end_date: str | None = None,
    main_domain_only: bool | None = None,
) -> BounceRateOutput:
    """Get website bounce rate over time (desktop and mobile combined)."""
    if not api_key or not api_key.strip():
        return BounceRateOutput(success=False, error=_EMPTY_KEY_ERROR)

    cleaned = _clean_domain(domain)
    url = f"{_BASE_URL}/{cleaned}/total-traffic-and-engagement/bounce-rate"
    params = _time_series_params(
        api_key, country, granularity, start_date, end_date, main_domain_only
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                url, params=params, headers={"Accept": "application/json"}
            )
        if response.status_code != 200:
            return BounceRateOutput(
                success=False,
                error=f"Similarweb API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return BounceRateOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return BounceRateOutput(success=False, error=f"bounce_rate failed: {exc}")

    meta = data.get("meta") or {}
    request_meta = meta.get("request") or {}
    points = [
        BounceRatePoint(date=item.get("date"), bounce_rate=item.get("bounce_rate"))
        for item in (data.get("bounce_rate") or [])
        if isinstance(item, dict)
    ]

    return BounceRateOutput(
        success=True,
        domain=request_meta.get("domain"),
        country=request_meta.get("country"),
        granularity=request_meta.get("granularity"),
        last_updated=meta.get("last_updated"),
        bounce_rate=points,
    )


@tool(args_schema=PagesPerVisitInput)
@serialize_pydantic_return
async def pages_per_visit(
    domain: str,
    api_key: str,
    country: str = "world",
    granularity: str = "monthly",
    start_date: str | None = None,
    end_date: str | None = None,
    main_domain_only: bool | None = None,
) -> PagesPerVisitOutput:
    """Get average pages per visit over time (desktop and mobile combined)."""
    if not api_key or not api_key.strip():
        return PagesPerVisitOutput(success=False, error=_EMPTY_KEY_ERROR)

    cleaned = _clean_domain(domain)
    url = f"{_BASE_URL}/{cleaned}/total-traffic-and-engagement/pages-per-visit"
    params = _time_series_params(
        api_key, country, granularity, start_date, end_date, main_domain_only
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                url, params=params, headers={"Accept": "application/json"}
            )
        if response.status_code != 200:
            return PagesPerVisitOutput(
                success=False,
                error=f"Similarweb API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return PagesPerVisitOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PagesPerVisitOutput(success=False, error=f"pages_per_visit failed: {exc}")

    meta = data.get("meta") or {}
    request_meta = meta.get("request") or {}
    points = [
        PagesPerVisitPoint(
            date=item.get("date"), pages_per_visit=item.get("pages_per_visit")
        )
        for item in (data.get("pages_per_visit") or [])
        if isinstance(item, dict)
    ]

    return PagesPerVisitOutput(
        success=True,
        domain=request_meta.get("domain"),
        country=request_meta.get("country"),
        granularity=request_meta.get("granularity"),
        last_updated=meta.get("last_updated"),
        pages_per_visit=points,
    )


@tool(args_schema=VisitDurationInput)
@serialize_pydantic_return
async def visit_duration(
    domain: str,
    api_key: str,
    country: str = "world",
    granularity: str = "monthly",
    start_date: str | None = None,
    end_date: str | None = None,
    main_domain_only: bool | None = None,
) -> VisitDurationOutput:
    """Get average desktop visit duration over time (in seconds)."""
    if not api_key or not api_key.strip():
        return VisitDurationOutput(success=False, error=_EMPTY_KEY_ERROR)

    cleaned = _clean_domain(domain)
    url = f"{_BASE_URL}/{cleaned}/traffic-and-engagement/average-visit-duration"
    params = _time_series_params(
        api_key, country, granularity, start_date, end_date, main_domain_only
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                url, params=params, headers={"Accept": "application/json"}
            )
        if response.status_code != 200:
            return VisitDurationOutput(
                success=False,
                error=f"Similarweb API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return VisitDurationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return VisitDurationOutput(success=False, error=f"visit_duration failed: {exc}")

    meta = data.get("meta") or {}
    request_meta = meta.get("request") or {}
    points = [
        VisitDurationPoint(
            date=item.get("date"),
            duration_seconds=item.get("average_visit_duration"),
        )
        for item in (data.get("average_visit_duration") or [])
        if isinstance(item, dict)
    ]

    return VisitDurationOutput(
        success=True,
        domain=request_meta.get("domain"),
        country=request_meta.get("country"),
        granularity=request_meta.get("granularity"),
        last_updated=meta.get("last_updated"),
        average_visit_duration=points,
    )
