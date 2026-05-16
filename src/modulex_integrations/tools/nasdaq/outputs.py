"""Pydantic response models for the Nasdaq Data Link integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "GetBalanceSheetOutput",
    "GetCashFlowOutput",
    "GetCompanyStatsOutput",
    "GetFundamentalDetailsOutput",
    "GetFundamentalSummaryOutput",
    "GetReferenceDataOutput",
    "ListAvailableFieldsOutput",
    "NasdaqField",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _TableQueryOutput(_Base):
    """Common shape for table-query actions.

    Legacy returns ``result: list-of-dicts`` (one row per record from
    the DataFrame). We keep ``records`` open as ``list[dict]`` because
    Nasdaq's tables carry dozens of heterogeneous columns and locking
    them down would harden the schema for no real validation benefit.
    """

    success: bool
    error: str | None = None
    records: list[dict[str, Any]] = Field(default_factory=list)
    # Mirrors legacy's "No data found" message on empty result sets.
    message: str | None = None


class GetBalanceSheetOutput(_TableQueryOutput):
    pass


class GetCashFlowOutput(_TableQueryOutput):
    pass


class GetCompanyStatsOutput(_TableQueryOutput):
    pass


class GetFundamentalDetailsOutput(_TableQueryOutput):
    pass


class GetFundamentalSummaryOutput(_TableQueryOutput):
    pass


class GetReferenceDataOutput(_TableQueryOutput):
    pass


class NasdaqField(_Base):
    name: str
    description: str
    type: str
    filterable: bool = False


class ListAvailableFieldsOutput(_Base):
    success: bool
    error: str | None = None
    table_type: str | None = None
    fields: list[NasdaqField] = Field(default_factory=list)
