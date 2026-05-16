"""Tests for the SEMrush integration.

All 17 CSV-returning actions share the same `_call_csv` helper, so
test coverage is representative (one per major action shape) plus the
manifest sanity trio, the in-band `ERROR` failure path, and the two
.Trends JSON endpoints.
"""
from __future__ import annotations

import re
from typing import Any

import pytest

from modulex_integrations.tools.semrush import (
    TOOLS,
    api_units_balance,
    backlinks,
    backlinks_domains,
    batch_keyword_overview,
    competitors,
    domain_organic_keywords,
    domain_overview,
    domain_paid_keywords,
    keyword_difficulty,
    keyword_organic_results,
    keyword_overview,
    keyword_overview_single_db,
    manifest,
    related_keywords,
    traffic_sources,
    traffic_summary,
)
from modulex_integrations.tools.semrush.outputs import (
    ApiUnitsBalanceOutput,
    BacklinksDomainsOutput,
    BacklinksOutput,
    BatchKeywordOverviewOutput,
    CompetitorsOutput,
    DomainOrganicKeywordsOutput,
    DomainOverviewOutput,
    DomainPaidKeywordsOutput,
    KeywordDifficultyOutput,
    KeywordOrganicResultsOutput,
    KeywordOverviewOutput,
    KeywordOverviewSingleDbOutput,
    RelatedKeywordsOutput,
    TrafficSourcesOutput,
    TrafficSummaryOutput,
)

API = "https://api.semrush.com/"
TRENDS = "https://api.semrush.com/analytics/ta/api/v3/"
_API_KEY = "semrush-fake-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


class TestManifest:
    def test_manifest_exposes_nineteen_actions(self) -> None:
        assert len(manifest.actions) == 19

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]

    def test_test_endpoint_uses_key_query_param(self) -> None:
        auth = manifest.auth_schemas[0]
        assert auth.test_endpoint is not None
        assert auth.test_endpoint.params == {"type": "api_units", "key": "{api_key}"}


@pytest.mark.asyncio
async def test_domain_overview_parses_csv(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?type=domain_ranks&domain=example.com&database=us"
            f"&export_columns=Db%2CDn%2CRk%2COr%2COt%2COc%2CAd%2CAt%2CAc%2CSh%2CSv"
            f"&key={_API_KEY}"
        ),
        text="Db;Dn;Rk;Or\nus;example.com;42;100\n",
    )
    result_dict = await domain_overview.ainvoke(_args(domain="example.com"))
    assert isinstance(result_dict, dict)
    result = DomainOverviewOutput.model_validate(result_dict)
    assert result.success is True
    assert result.records == [{"Db": "us", "Dn": "example.com", "Rk": "42", "Or": "100"}]


@pytest.mark.asyncio
async def test_domain_overview_in_band_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}?type=domain_ranks&domain=example.com&database=us"
            f"&export_columns=Db%2CDn%2CRk%2COr%2COt%2COc%2CAd%2CAt%2CAc%2CSh%2CSv"
            f"&key={_API_KEY}"
        ),
        text="ERROR 50 :: NOTHING FOUND",
    )
    result = DomainOverviewOutput.model_validate(
        await domain_overview.ainvoke(_args(domain="example.com"))
    )
    assert result.success is False
    assert result.error is not None and "NOTHING FOUND" in result.error


@pytest.mark.asyncio
async def test_domain_organic_keywords(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}\?type=domain_organic.*key={_API_KEY}"),
        text="Ph;Po;Pp;Pd;Nq\nseo;1;2;0;1000\nrank;3;4;1;500\n",
    )
    result = DomainOrganicKeywordsOutput.model_validate(
        await domain_organic_keywords.ainvoke(_args(domain="example.com", limit=2))
    )
    assert result.success is True
    assert len(result.records) == 2
    assert result.records[0]["Ph"] == "seo"


@pytest.mark.asyncio
async def test_domain_paid_keywords(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}\?type=domain_adwords.*"),
        text="Ph;Po;Nq\nads;1;1000\n",
    )
    result = DomainPaidKeywordsOutput.model_validate(
        await domain_paid_keywords.ainvoke(_args(domain="example.com"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_competitors(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}\?type=domain_organic_organic.*"),
        text="Dn;Cr;Np\nrival.com;0.9;10\n",
    )
    result = CompetitorsOutput.model_validate(
        await competitors.ainvoke(_args(domain="example.com"))
    )
    assert result.success is True
    assert result.records[0]["Dn"] == "rival.com"


@pytest.mark.asyncio
async def test_backlinks(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}\?type=backlinks&target=.*"),
        text="source_url;target_url;anchor\nhttps://x.io;https://example.com;example\n",
    )
    result = BacklinksOutput.model_validate(
        await backlinks.ainvoke(_args(target="example.com"))
    )
    assert result.success is True
    assert result.records[0]["anchor"] == "example"


@pytest.mark.asyncio
async def test_backlinks_domains(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}\?type=backlinks_refdomains.*"),
        text="domain;domain_score\nrefer.io;42\n",
    )
    result = BacklinksDomainsOutput.model_validate(
        await backlinks_domains.ainvoke(_args(target="example.com"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_keyword_overview(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}\?type=phrase_all.*"),
        text="Ph;Nq;Cp\nseo;1000;1.5\n",
    )
    result = KeywordOverviewOutput.model_validate(
        await keyword_overview.ainvoke(_args(keyword="seo"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_keyword_overview_single_db(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}\?type=phrase_this.*"),
        text="Ph;Nq;Kd\nseo;1000;72.5\n",
    )
    result = KeywordOverviewSingleDbOutput.model_validate(
        await keyword_overview_single_db.ainvoke(_args(keyword="seo", database="us"))
    )
    assert result.success is True
    assert result.records[0]["Kd"] == "72.5"


@pytest.mark.asyncio
async def test_batch_keyword_overview_joins_with_semicolon(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        from urllib.parse import parse_qs, urlparse
        captured.update(parse_qs(urlparse(str(request.url)).query))
        from httpx import Response
        return Response(200, text="Ph;Nq\nseo;1000\nsem;500\n")

    httpx_mock.add_callback(_capture, method="GET", url=re.compile(rf"{API}\?.*phrase_these.*"))
    result = BatchKeywordOverviewOutput.model_validate(
        await batch_keyword_overview.ainvoke(_args(keywords=["seo", "sem"], database="us"))
    )
    assert result.success is True
    # Keywords are joined with `;` into the `phrase` parameter.
    assert captured["phrase"] == ["seo;sem"]


@pytest.mark.asyncio
async def test_related_keywords(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}\?type=phrase_related.*"),
        text="Ph;Nq\nseo tools;500\n",
    )
    result = RelatedKeywordsOutput.model_validate(
        await related_keywords.ainvoke(_args(keyword="seo"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_keyword_organic_results(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}\?type=phrase_organic.*"),
        text="Po;Dn;Ur\n1;example.com;https://example.com\n",
    )
    result = KeywordOrganicResultsOutput.model_validate(
        await keyword_organic_results.ainvoke(_args(keyword="seo", database="us"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_keyword_difficulty(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{API}\?type=phrase_kdi.*"),
        text="Ph;Kd\nseo;72.5\nrank;68.0\n",
    )
    result = KeywordDifficultyOutput.model_validate(
        await keyword_difficulty.ainvoke(_args(keywords=["seo", "rank"], database="us"))
    )
    assert result.success is True
    assert len(result.records) == 2


@pytest.mark.asyncio
async def test_traffic_summary_json(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{TRENDS}summary\?.*"),
        json={"summary": [{"target": "example.com", "visits": 1000}]},
        headers={"content-type": "application/json"},
    )
    result = TrafficSummaryOutput.model_validate(
        await traffic_summary.ainvoke(_args(domains=["example.com"]))
    )
    assert result.success is True
    assert isinstance(result.data, dict)


@pytest.mark.asyncio
async def test_traffic_sources_json(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"{TRENDS}sources\?.*"),
        json={"sources": {"direct": 0.4, "search": 0.5, "referral": 0.1}},
        headers={"content-type": "application/json"},
    )
    result = TrafficSourcesOutput.model_validate(
        await traffic_sources.ainvoke(_args(domain="example.com"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_api_units_balance(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}?type=api_units&key={_API_KEY}",
        text="9999",
    )
    result = ApiUnitsBalanceOutput.model_validate(
        await api_units_balance.ainvoke(_args())
    )
    assert result.success is True
    assert result.units == "9999"


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result = DomainOverviewOutput.model_validate(
        await domain_overview.ainvoke({"api_key": "", "domain": "example.com"})
    )
    assert result.success is False
    assert result.error is not None and "API key" in result.error
