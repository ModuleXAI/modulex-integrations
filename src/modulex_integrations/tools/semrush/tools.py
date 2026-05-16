"""SEMrush LangChain ``@tool`` functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.semrush.outputs import (
    ApiUnitsBalanceOutput,
    BacklinksDomainsOutput,
    BacklinksOutput,
    BatchKeywordOverviewOutput,
    BroadMatchKeywordsOutput,
    CompetitorsOutput,
    DomainOrganicKeywordsOutput,
    DomainOverviewOutput,
    DomainPaidKeywordsOutput,
    KeywordAdsHistoryOutput,
    KeywordDifficultyOutput,
    KeywordOrganicResultsOutput,
    KeywordOverviewOutput,
    KeywordOverviewSingleDbOutput,
    KeywordPaidResultsOutput,
    PhraseQuestionsOutput,
    RelatedKeywordsOutput,
    TrafficSourcesOutput,
    TrafficSummaryOutput,
)

__all__ = [
    "api_units_balance",
    "backlinks",
    "backlinks_domains",
    "batch_keyword_overview",
    "broad_match_keywords",
    "competitors",
    "domain_organic_keywords",
    "domain_overview",
    "domain_paid_keywords",
    "keyword_ads_history",
    "keyword_difficulty",
    "keyword_organic_results",
    "keyword_overview",
    "keyword_overview_single_db",
    "keyword_paid_results",
    "phrase_questions",
    "related_keywords",
    "traffic_sources",
    "traffic_summary",
]

_API_BASE = "https://api.semrush.com/"
_TRENDS_BASE = "https://api.semrush.com/analytics/ta/api/v3/"
_TIMEOUT = 30.0


def _empty_key_error(name: str) -> str:
    return (
        f"SEMrush API key is empty for {name}. "
        "Please configure a valid credential."
    )


def _parse_csv(text: str) -> list[dict[str, str]]:
    """SEMrush CSV is semicolon-separated; first line is the column header."""
    if not text or not text.strip():
        return []
    lines = text.strip().split("\n")
    if not lines:
        return []
    headers = [h.strip() for h in lines[0].split(";")]
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = line.split(";")
        rows.append(
            {h: (values[i].strip() if i < len(values) else "") for i, h in enumerate(headers)}
        )
    return rows


async def _call_csv(
    api_key: str, params: dict[str, Any]
) -> tuple[bool, str | None, list[dict[str, str]], str]:
    """SEMrush v1 CSV endpoint. Returns (ok, error, records, raw_text)."""
    full_params: dict[str, Any] = dict(params)
    full_params["key"] = api_key
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(_API_BASE, params=full_params)
    except Exception as exc:
        return False, f"SEMrush request failed: {exc}", [], ""

    if response.status_code != 200:
        return (
            False,
            f"SEMrush API error: HTTP {response.status_code} - {response.text}",
            [],
            response.text,
        )

    text = response.text or ""
    # SEMrush returns plain-text "ERROR …" messages on logical failure
    # while still returning HTTP 200.
    if "ERROR" in text.split("\n", 1)[0]:
        return False, f"SEMrush API error: {text.strip()}", [], text

    return True, None, _parse_csv(text), text


async def _call_trends(
    api_key: str, path: str, params: dict[str, Any]
) -> tuple[bool, str | None, Any]:
    """SEMrush .Trends v3 endpoint. Returns (ok, error, body)."""
    full_params: dict[str, Any] = dict(params)
    full_params["key"] = api_key
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_TRENDS_BASE}{path}", params=full_params)
    except Exception as exc:
        return False, f"SEMrush trends request failed: {exc}", None

    if response.status_code != 200:
        return False, (
            f"Traffic API error: HTTP {response.status_code} - {response.text}"
        ), None

    if (response.headers.get("content-type") or "").startswith("application/json"):
        try:
            return True, None, response.json()
        except Exception:
            return True, None, response.text
    return True, None, response.text


# --- Input schemas ---------------------------------------------------------


class _ApiKey(BaseModel):
    api_key: str = Field(description="SEMrush API key (provided by credential system)")


class DomainOverviewInput(_ApiKey):
    domain: str = Field(description="Domain to analyze")
    database: str = Field(default="us", description="Regional database")


class DomainKeywordsInput(_ApiKey):
    domain: str = Field(description="Domain to analyze")
    database: str = Field(default="us", description="Regional database")
    limit: int = Field(default=10, description="Maximum records")


class CompetitorsInput(_ApiKey):
    domain: str = Field(description="Domain to analyze")
    database: str = Field(default="us", description="Regional database")
    limit: int = Field(default=10, description="Maximum records")


class BacklinksInput(_ApiKey):
    target: str = Field(description="Domain or URL to analyze")
    limit: int = Field(default=10, description="Maximum records")


class KeywordOverviewInput(_ApiKey):
    keyword: str = Field(description="Keyword to analyze")
    database: str = Field(default="us", description="Database to use")


class KeywordOverviewSingleDbInput(_ApiKey):
    keyword: str = Field(description="Keyword to analyze")
    database: str = Field(description="Database to use")


class BatchKeywordOverviewInput(_ApiKey):
    keywords: list[str] = Field(description="Array of keywords (max 100)")
    database: str = Field(description="Database to use")


class RelatedKeywordsInput(_ApiKey):
    keyword: str = Field(description="Keyword to find related terms for")
    database: str = Field(default="us", description="Database to use")
    limit: int = Field(default=10, description="Maximum records")


class KeywordResultsInput(_ApiKey):
    keyword: str = Field(description="Keyword to analyze")
    database: str = Field(description="Database to use")
    limit: int = Field(default=10, description="Maximum records")


class KeywordDifficultyInput(_ApiKey):
    keywords: list[str] = Field(description="Array of keywords (max 100)")
    database: str = Field(description="Database to use")


class TrafficSummaryInput(_ApiKey):
    domains: list[str] = Field(description="Domains to analyze")
    country: str = Field(default="us", description="Country code")


class TrafficSourcesInput(_ApiKey):
    domain: str = Field(description="Domain to analyze")
    country: str = Field(default="us", description="Country code")


class ApiUnitsBalanceInput(_ApiKey):
    pass


# --- Tools -----------------------------------------------------------------


@tool(args_schema=DomainOverviewInput)
@serialize_pydantic_return
async def domain_overview(
    api_key: str, domain: str, database: str = "us"
) -> DomainOverviewOutput:
    """Get domain overview from SEMrush."""
    if not api_key or not api_key.strip():
        return DomainOverviewOutput(success=False, error=_empty_key_error("domain_overview"))
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "domain_ranks",
            "domain": domain,
            "database": database,
            "export_columns": "Db,Dn,Rk,Or,Ot,Oc,Ad,At,Ac,Sh,Sv",
        },
    )
    return DomainOverviewOutput(success=ok, error=err, records=records)


@tool(args_schema=DomainKeywordsInput)
@serialize_pydantic_return
async def domain_organic_keywords(
    api_key: str, domain: str, database: str = "us", limit: int = 10
) -> DomainOrganicKeywordsOutput:
    """Get organic keywords for a domain."""
    if not api_key or not api_key.strip():
        return DomainOrganicKeywordsOutput(
            success=False, error=_empty_key_error("domain_organic_keywords")
        )
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "domain_organic",
            "domain": domain,
            "database": database,
            "display_limit": limit,
            "export_columns": "Ph,Po,Pp,Pd,Nq,Cp,Ur,Tr,Tc,Co,Nr,Td",
        },
    )
    return DomainOrganicKeywordsOutput(success=ok, error=err, records=records)


@tool(args_schema=DomainKeywordsInput)
@serialize_pydantic_return
async def domain_paid_keywords(
    api_key: str, domain: str, database: str = "us", limit: int = 10
) -> DomainPaidKeywordsOutput:
    """Get paid keywords for a domain."""
    if not api_key or not api_key.strip():
        return DomainPaidKeywordsOutput(
            success=False, error=_empty_key_error("domain_paid_keywords")
        )
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "domain_adwords",
            "domain": domain,
            "database": database,
            "display_limit": limit,
            "export_columns": "Ph,Po,Pp,Pd,Ab,Nq,Cp,Tr,Tc,Co,Nr,Td",
        },
    )
    return DomainPaidKeywordsOutput(success=ok, error=err, records=records)


@tool(args_schema=CompetitorsInput)
@serialize_pydantic_return
async def competitors(
    api_key: str, domain: str, database: str = "us", limit: int = 10
) -> CompetitorsOutput:
    """Get organic-search competitors for a domain."""
    if not api_key or not api_key.strip():
        return CompetitorsOutput(success=False, error=_empty_key_error("competitors"))
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "domain_organic_organic",
            "domain": domain,
            "database": database,
            "display_limit": limit,
            "export_columns": "Dn,Cr,Np,Or,Ot,Oc,Ad,At,Ac",
        },
    )
    return CompetitorsOutput(success=ok, error=err, records=records)


@tool(args_schema=BacklinksInput)
@serialize_pydantic_return
async def backlinks(api_key: str, target: str, limit: int = 10) -> BacklinksOutput:
    """Get backlinks for a domain or URL."""
    if not api_key or not api_key.strip():
        return BacklinksOutput(success=False, error=_empty_key_error("backlinks"))
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "backlinks",
            "target": target,
            "display_limit": limit,
            "export_columns": (
                "source_title,source_url,target_url,anchor,page_score,"
                "domain_score,external_num,internal_num,first_seen,last_seen"
            ),
        },
    )
    return BacklinksOutput(success=ok, error=err, records=records)


@tool(args_schema=BacklinksInput)
@serialize_pydantic_return
async def backlinks_domains(
    api_key: str, target: str, limit: int = 10
) -> BacklinksDomainsOutput:
    """Get referring domains for a target."""
    if not api_key or not api_key.strip():
        return BacklinksDomainsOutput(
            success=False, error=_empty_key_error("backlinks_domains")
        )
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "backlinks_refdomains",
            "target": target,
            "display_limit": limit,
            "export_columns": (
                "domain,domain_score,backlinks_num,ip,country,first_seen,last_seen"
            ),
        },
    )
    return BacklinksDomainsOutput(success=ok, error=err, records=records)


@tool(args_schema=KeywordOverviewInput)
@serialize_pydantic_return
async def keyword_overview(
    api_key: str, keyword: str, database: str = "us"
) -> KeywordOverviewOutput:
    """Get overview metrics for a keyword across all databases."""
    if not api_key or not api_key.strip():
        return KeywordOverviewOutput(
            success=False, error=_empty_key_error("keyword_overview")
        )
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "phrase_all",
            "phrase": keyword,
            "database": database,
            "export_columns": "Ph,Nq,Cp,Co,Nr,Td",
        },
    )
    return KeywordOverviewOutput(success=ok, error=err, records=records)


@tool(args_schema=KeywordOverviewSingleDbInput)
@serialize_pydantic_return
async def keyword_overview_single_db(
    api_key: str, keyword: str, database: str
) -> KeywordOverviewSingleDbOutput:
    """Get detailed keyword overview from a specific database."""
    if not api_key or not api_key.strip():
        return KeywordOverviewSingleDbOutput(
            success=False, error=_empty_key_error("keyword_overview_single_db")
        )
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "phrase_this",
            "phrase": keyword,
            "database": database,
            "export_columns": "Ph,Nq,Cp,Co,Nr,Td,In,Kd",
        },
    )
    return KeywordOverviewSingleDbOutput(success=ok, error=err, records=records)


@tool(args_schema=BatchKeywordOverviewInput)
@serialize_pydantic_return
async def batch_keyword_overview(
    api_key: str, keywords: list[str], database: str
) -> BatchKeywordOverviewOutput:
    """Analyze up to 100 keywords in a single call."""
    if not api_key or not api_key.strip():
        return BatchKeywordOverviewOutput(
            success=False, error=_empty_key_error("batch_keyword_overview")
        )
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "phrase_these",
            "phrase": ";".join(keywords[:100]),
            "database": database,
            "export_columns": "Ph,Nq,Cp,Co,Nr,Td,In,Kd",
        },
    )
    return BatchKeywordOverviewOutput(success=ok, error=err, records=records)


@tool(args_schema=RelatedKeywordsInput)
@serialize_pydantic_return
async def related_keywords(
    api_key: str, keyword: str, database: str = "us", limit: int = 10
) -> RelatedKeywordsOutput:
    """Get semantically related keywords."""
    if not api_key or not api_key.strip():
        return RelatedKeywordsOutput(
            success=False, error=_empty_key_error("related_keywords")
        )
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "phrase_related",
            "phrase": keyword,
            "database": database,
            "display_limit": limit,
            "export_columns": "Ph,Nq,Cp,Co,Nr,Td",
        },
    )
    return RelatedKeywordsOutput(success=ok, error=err, records=records)


@tool(args_schema=KeywordResultsInput)
@serialize_pydantic_return
async def keyword_organic_results(
    api_key: str, keyword: str, database: str, limit: int = 10
) -> KeywordOrganicResultsOutput:
    """Get domains ranking in Google's top 100 for a keyword."""
    if not api_key or not api_key.strip():
        return KeywordOrganicResultsOutput(
            success=False, error=_empty_key_error("keyword_organic_results")
        )
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "phrase_organic",
            "phrase": keyword,
            "database": database,
            "display_limit": limit,
            "export_columns": "Po,Pt,Dn,Ur,Fk,Fp,Fl",
        },
    )
    return KeywordOrganicResultsOutput(success=ok, error=err, records=records)


@tool(args_schema=KeywordResultsInput)
@serialize_pydantic_return
async def keyword_paid_results(
    api_key: str, keyword: str, database: str, limit: int = 10
) -> KeywordPaidResultsOutput:
    """Get domains in Google's paid search results for a keyword."""
    if not api_key or not api_key.strip():
        return KeywordPaidResultsOutput(
            success=False, error=_empty_key_error("keyword_paid_results")
        )
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "phrase_adwords",
            "phrase": keyword,
            "database": database,
            "display_limit": limit,
            "export_columns": "Dn,Ur,Vu",
        },
    )
    return KeywordPaidResultsOutput(success=ok, error=err, records=records)


@tool(args_schema=KeywordResultsInput)
@serialize_pydantic_return
async def keyword_ads_history(
    api_key: str, keyword: str, database: str, limit: int = 10
) -> KeywordAdsHistoryOutput:
    """Get domains that bid on a keyword in the last 12 months."""
    if not api_key or not api_key.strip():
        return KeywordAdsHistoryOutput(
            success=False, error=_empty_key_error("keyword_ads_history")
        )
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "phrase_adwords_historical",
            "phrase": keyword,
            "database": database,
            "display_limit": limit,
            "export_columns": "Dn,Dt,Po,Ur,Tt,Ds,Vu",
        },
    )
    return KeywordAdsHistoryOutput(success=ok, error=err, records=records)


@tool(args_schema=KeywordResultsInput)
@serialize_pydantic_return
async def broad_match_keywords(
    api_key: str, keyword: str, database: str, limit: int = 10
) -> BroadMatchKeywordsOutput:
    """Get broad matches for a keyword."""
    if not api_key or not api_key.strip():
        return BroadMatchKeywordsOutput(
            success=False, error=_empty_key_error("broad_match_keywords")
        )
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "phrase_fullsearch",
            "phrase": keyword,
            "database": database,
            "display_limit": limit,
            "export_columns": "Ph,Nq,Cp,Co,Nr,Td,Fk,In,Kd",
        },
    )
    return BroadMatchKeywordsOutput(success=ok, error=err, records=records)


@tool(args_schema=KeywordResultsInput)
@serialize_pydantic_return
async def phrase_questions(
    api_key: str, keyword: str, database: str, limit: int = 10
) -> PhraseQuestionsOutput:
    """Get question-based keywords for a term."""
    if not api_key or not api_key.strip():
        return PhraseQuestionsOutput(
            success=False, error=_empty_key_error("phrase_questions")
        )
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "phrase_questions",
            "phrase": keyword,
            "database": database,
            "display_limit": limit,
            "export_columns": "Ph,Nq,Cp,Co,Nr,Td,In,Kd",
        },
    )
    return PhraseQuestionsOutput(success=ok, error=err, records=records)


@tool(args_schema=KeywordDifficultyInput)
@serialize_pydantic_return
async def keyword_difficulty(
    api_key: str, keywords: list[str], database: str
) -> KeywordDifficultyOutput:
    """Get difficulty index (0-100) for ranking keywords in Google's top 10."""
    if not api_key or not api_key.strip():
        return KeywordDifficultyOutput(
            success=False, error=_empty_key_error("keyword_difficulty")
        )
    ok, err, records, _ = await _call_csv(
        api_key,
        {
            "type": "phrase_kdi",
            "phrase": ";".join(keywords[:100]),
            "database": database,
            "export_columns": "Ph,Kd",
        },
    )
    return KeywordDifficultyOutput(success=ok, error=err, records=records)


@tool(args_schema=TrafficSummaryInput)
@serialize_pydantic_return
async def traffic_summary(
    api_key: str, domains: list[str], country: str = "us"
) -> TrafficSummaryOutput:
    """Get .Trends traffic summary for one or more domains."""
    if not api_key or not api_key.strip():
        return TrafficSummaryOutput(
            success=False, error=_empty_key_error("traffic_summary")
        )
    ok, err, data = await _call_trends(
        api_key,
        "summary",
        {
            "targets": ",".join(domains),
            "country": country,
            "display_date": "monthly",
            "display_limit": 12,
        },
    )
    return TrafficSummaryOutput(success=ok, error=err, data=data)


@tool(args_schema=TrafficSourcesInput)
@serialize_pydantic_return
async def traffic_sources(
    api_key: str, domain: str, country: str = "us"
) -> TrafficSourcesOutput:
    """Get .Trends traffic sources breakdown for a domain."""
    if not api_key or not api_key.strip():
        return TrafficSourcesOutput(
            success=False, error=_empty_key_error("traffic_sources")
        )
    ok, err, data = await _call_trends(
        api_key,
        "sources",
        {"target": domain, "country": country, "display_date": "monthly"},
    )
    return TrafficSourcesOutput(success=ok, error=err, data=data)


@tool(args_schema=ApiUnitsBalanceInput)
@serialize_pydantic_return
async def api_units_balance(api_key: str) -> ApiUnitsBalanceOutput:
    """Check the remaining API units balance in your SEMrush account."""
    if not api_key or not api_key.strip():
        return ApiUnitsBalanceOutput(
            success=False, error=_empty_key_error("api_units_balance")
        )

    full_params: dict[str, Any] = {"type": "api_units", "key": api_key}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(_API_BASE, params=full_params)
    except Exception as exc:
        return ApiUnitsBalanceOutput(
            success=False, error=f"api_units_balance failed: {exc}"
        )

    if response.status_code != 200:
        return ApiUnitsBalanceOutput(
            success=False,
            error=f"SEMrush API error: HTTP {response.status_code} - {response.text}",
        )

    text = (response.text or "").strip()
    if text.startswith("ERROR"):
        return ApiUnitsBalanceOutput(success=False, error=f"SEMrush API error: {text}")
    return ApiUnitsBalanceOutput(success=True, units=text)
