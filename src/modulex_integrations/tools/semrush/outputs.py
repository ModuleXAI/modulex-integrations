"""Pydantic response models for the SEMrush integration.

SEMrush returns CSV (semicolon-separated) bodies that we parse into
``list[dict[str, str]]``. The two ``traffic_*`` Trends actions return
JSON instead, surfaced as ``dict[str, Any]``. ``api_units_balance``
returns a bare number string which we surface on ``units``.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ApiUnitsBalanceOutput",
    "BacklinksDomainsOutput",
    "BacklinksOutput",
    "BatchKeywordOverviewOutput",
    "BroadMatchKeywordsOutput",
    "CompetitorsOutput",
    "DomainOrganicKeywordsOutput",
    "DomainOverviewOutput",
    "DomainPaidKeywordsOutput",
    "KeywordAdsHistoryOutput",
    "KeywordDifficultyOutput",
    "KeywordOrganicResultsOutput",
    "KeywordOverviewOutput",
    "KeywordOverviewSingleDbOutput",
    "KeywordPaidResultsOutput",
    "PhraseQuestionsOutput",
    "RelatedKeywordsOutput",
    "TrafficSourcesOutput",
    "TrafficSummaryOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class _CsvBase(_Base):
    # Parsed CSV: list of dicts with the column names from the first row.
    records: list[dict[str, str]] = Field(default_factory=list)


class DomainOverviewOutput(_CsvBase):
    pass


class DomainOrganicKeywordsOutput(_CsvBase):
    pass


class DomainPaidKeywordsOutput(_CsvBase):
    pass


class CompetitorsOutput(_CsvBase):
    pass


class BacklinksOutput(_CsvBase):
    pass


class BacklinksDomainsOutput(_CsvBase):
    pass


class KeywordOverviewOutput(_CsvBase):
    pass


class KeywordOverviewSingleDbOutput(_CsvBase):
    pass


class BatchKeywordOverviewOutput(_CsvBase):
    pass


class RelatedKeywordsOutput(_CsvBase):
    pass


class KeywordOrganicResultsOutput(_CsvBase):
    pass


class KeywordPaidResultsOutput(_CsvBase):
    pass


class KeywordAdsHistoryOutput(_CsvBase):
    pass


class BroadMatchKeywordsOutput(_CsvBase):
    pass


class PhraseQuestionsOutput(_CsvBase):
    pass


class KeywordDifficultyOutput(_CsvBase):
    pass


class TrafficSummaryOutput(_Base):
    # Trends API returns JSON when content-type matches; legacy falls
    # back to text if not. We keep the raw body on ``data``.
    data: Any = None


class TrafficSourcesOutput(_Base):
    data: Any = None


class ApiUnitsBalanceOutput(_Base):
    units: str | None = None
