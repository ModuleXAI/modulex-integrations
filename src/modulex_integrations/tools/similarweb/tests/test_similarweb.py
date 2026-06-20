"""Happy-path tests per action + failure-path and empty-credential tests
for the non-2xx → success=False branch (the tools don't raise)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.similarweb import (
    TOOLS,
    bounce_rate,
    manifest,
    pages_per_visit,
    traffic_visits,
    visit_duration,
    website_overview,
)
from modulex_integrations.tools.similarweb.outputs import (
    BounceRateOutput,
    PagesPerVisitOutput,
    TrafficVisitsOutput,
    VisitDurationOutput,
    WebsiteOverviewOutput,
)

BASE = "https://api.similarweb.com/v1/website"
_API_KEY = "fake-api-key"
_DOMAIN = "example.com"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, domain=_DOMAIN, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_5_actions(self) -> None:
        assert len(manifest.actions) == 5

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_website_overview(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/{_DOMAIN}/general-data/all?api_key={_API_KEY}&format=json",
        json={
            "SiteName": "example.com",
            "Description": "An example site",
            "Category": "Computers_Electronics_and_Technology",
            "GlobalRank": {"Rank": 1234},
            "CountryRank": {"Rank": 56},
            "CategoryRank": {"Rank": 7},
            "Engagements": {
                "Visits": 1000000,
                "TimeOnSite": 120.5,
                "PagePerVisit": 3.2,
                "BounceRate": 0.45,
            },
            "TopCountryShares": [
                {"CountryCode": "US", "Value": 0.4},
                {"Country": 826, "Value": 0.1},
            ],
            "TrafficSources": {
                "Direct": 0.5,
                "Referrals": 0.1,
                "Search": 0.3,
                "Social": 0.05,
                "Mail": 0.02,
                "Paid Referrals": 0.03,
            },
        },
    )

    result_dict = await website_overview.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = WebsiteOverviewOutput.model_validate(result_dict)
    assert result.success is True
    assert result.site_name == "example.com"
    assert result.global_rank == 1234
    assert result.country_rank == 56
    assert result.category_rank == 7
    assert result.monthly_visits == 1000000
    assert result.engagement_bounce_rate == 0.45
    assert result.top_countries[0].country == "US"
    assert result.top_countries[0].share == 0.4
    assert result.top_countries[1].country == "826"
    assert result.traffic_sources is not None
    assert result.traffic_sources.direct == 0.5
    assert result.traffic_sources.paid_referrals == 0.03

    sent = httpx_mock.get_requests()[0]
    assert sent.url.params["api_key"] == _API_KEY


@pytest.mark.asyncio
async def test_traffic_visits(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{BASE}/{_DOMAIN}/total-traffic-and-engagement/visits"
            f"?api_key={_API_KEY}&country=world&granularity=monthly&format=json"
        ),
        json={
            "meta": {
                "request": {
                    "domain": "example.com",
                    "country": "world",
                    "granularity": "monthly",
                },
                "last_updated": "2024-05-01",
            },
            "visits": [
                {"date": "2024-01-01", "visits": 950000},
                {"date": "2024-02-01", "visits": 1010000},
            ],
        },
    )

    result_dict = await traffic_visits.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = TrafficVisitsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.domain == "example.com"
    assert result.country == "world"
    assert result.granularity == "monthly"
    assert result.last_updated == "2024-05-01"
    assert len(result.visits) == 2
    assert result.visits[0].date == "2024-01-01"
    assert result.visits[0].visits == 950000


@pytest.mark.asyncio
async def test_bounce_rate(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{BASE}/{_DOMAIN}/total-traffic-and-engagement/bounce-rate"
            f"?api_key={_API_KEY}&country=world&granularity=monthly&format=json"
        ),
        json={
            "meta": {
                "request": {
                    "domain": "example.com",
                    "country": "world",
                    "granularity": "monthly",
                },
                "last_updated": "2024-05-01",
            },
            "bounce_rate": [
                {"date": "2024-01-01", "bounce_rate": 0.42},
            ],
        },
    )

    result_dict = await bounce_rate.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = BounceRateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.bounce_rate[0].date == "2024-01-01"
    assert result.bounce_rate[0].bounce_rate == 0.42


@pytest.mark.asyncio
async def test_pages_per_visit(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{BASE}/{_DOMAIN}/total-traffic-and-engagement/pages-per-visit"
            f"?api_key={_API_KEY}&country=world&granularity=monthly&format=json"
        ),
        json={
            "meta": {
                "request": {
                    "domain": "example.com",
                    "country": "world",
                    "granularity": "monthly",
                },
                "last_updated": "2024-05-01",
            },
            "pages_per_visit": [
                {"date": "2024-01-01", "pages_per_visit": 3.4},
            ],
        },
    )

    result_dict = await pages_per_visit.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = PagesPerVisitOutput.model_validate(result_dict)
    assert result.success is True
    assert result.pages_per_visit[0].pages_per_visit == 3.4


@pytest.mark.asyncio
async def test_visit_duration(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{BASE}/{_DOMAIN}/traffic-and-engagement/average-visit-duration"
            f"?api_key={_API_KEY}&country=world&granularity=monthly&format=json"
        ),
        json={
            "meta": {
                "request": {
                    "domain": "example.com",
                    "country": "world",
                    "granularity": "monthly",
                },
                "last_updated": "2024-05-01",
            },
            "average_visit_duration": [
                {"date": "2024-01-01", "average_visit_duration": 134.7},
            ],
        },
    )

    result_dict = await visit_duration.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = VisitDurationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.average_visit_duration[0].duration_seconds == 134.7


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_website_overview_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Non-2xx responses are wrapped in success=False + error, not raised."""
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/{_DOMAIN}/general-data/all?api_key={_API_KEY}&format=json",
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await website_overview.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = WebsiteOverviewOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_traffic_visits_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await traffic_visits.ainvoke({"domain": _DOMAIN, "api_key": ""})

    assert isinstance(result_dict, dict)

    result = TrafficVisitsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
