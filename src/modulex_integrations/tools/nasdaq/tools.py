"""Nasdaq Data Link LangChain ``@tool`` functions.

SDK-wrapping integration (``nasdaqdatalink``). Same lazy-import +
graceful-degradation pattern as tavily: the SDK is imported inside
each tool, so the package itself imports fine without
``nasdaq-data-link`` installed. ``ApiConfig.api_key`` is set as
global state per call (the SDK's documented auth pattern — ugly, but
it's the contract).

DataFrames returned by ``get_table`` are converted to a list of dicts
with ``NaN`` → ``None`` so the result is JSON-serializable. The
helper handles both real ``pandas.DataFrame`` objects and the
"empty" iterable case.
"""
from __future__ import annotations

import math
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.nasdaq.fields import FIELD_MAPPINGS
from modulex_integrations.tools.nasdaq.outputs import (
    GetBalanceSheetOutput,
    GetCashFlowOutput,
    GetCompanyStatsOutput,
    GetFundamentalDetailsOutput,
    GetFundamentalSummaryOutput,
    GetReferenceDataOutput,
    ListAvailableFieldsOutput,
    NasdaqField,
)

__all__ = [
    "get_balance_sheet",
    "get_cash_flow",
    "get_company_stats",
    "get_fundamental_details",
    "get_fundamental_summary",
    "get_reference_data",
    "list_available_fields",
]


def _empty_key_error(name: str) -> str:
    return (
        f"Nasdaq Data Link API key is empty for {name}. "
        "Please configure a valid credential."
    )


def _missing_sdk_error() -> str:
    return (
        "nasdaq-data-link package not installed. "
        "Install with: pip install nasdaq-data-link"
    )


def _missing_filter_error(name: str) -> str:
    return f"Either symbol or figi must be provided for {name}."


def _clean_nan(value: Any) -> Any:
    """Convert float NaN to None so the value is JSON-serializable."""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _dataframe_to_records(df: Any) -> list[dict[str, Any]]:
    """Coerce a Nasdaq SDK DataFrame return value to JSON-safe records.

    Pandas 3.x ignores the ``other`` argument to ``DataFrame.where``
    for numeric columns, so explicit per-cell NaN→None cleanup is
    needed regardless. We try the legacy ``.where(notnull, None)``
    chain first (cheap on pandas 2.x), then post-walk every record
    to replace any remaining NaN.
    """
    if df is None:
        return []
    try:
        records = df.where(df.notnull(), None).to_dict(orient="records")
    except Exception:
        try:
            records = df.to_dict(orient="records")
        except Exception:
            return []
    return [
        {k: _clean_nan(v) for k, v in r.items()}
        for r in records
        if isinstance(r, dict)
    ]


class _PeriodicQueryInput(BaseModel):
    """Shared input shape for the balance-sheet / cash-flow / fundamental tools."""

    api_key: str = Field(description="Nasdaq Data Link API key (provided by credential system)")
    symbol: str | None = Field(default=None, description="Stock ticker symbol")
    figi: str | None = Field(default=None, description="Bloomberg FIGI identifier")
    calendardate: str | None = Field(default=None, description="Calendar date YYYY-MM-DD")
    dimension: str | None = Field(default=None, description="MRQ, MRY, or MRT")


class _PointInTimeInput(BaseModel):
    """Shared shape for stats + reference-data tools (no date/dimension)."""

    api_key: str = Field(description="Nasdaq Data Link API key (provided by credential system)")
    symbol: str | None = Field(default=None, description="Stock ticker symbol")
    figi: str | None = Field(default=None, description="Bloomberg FIGI identifier")


class GetBalanceSheetInput(_PeriodicQueryInput):
    pass


class GetCashFlowInput(_PeriodicQueryInput):
    pass


class GetCompanyStatsInput(_PointInTimeInput):
    pass


class GetFundamentalDetailsInput(_PeriodicQueryInput):
    pass


class GetFundamentalSummaryInput(_PeriodicQueryInput):
    pass


class GetReferenceDataInput(_PointInTimeInput):
    pass


class ListAvailableFieldsInput(BaseModel):
    api_key: str = Field(description="Nasdaq Data Link API key (provided by credential system)")
    table_type: str = Field(description="Table to list fields for")


def _build_params(
    symbol: str | None,
    figi: str | None,
    calendardate: str | None = None,
    dimension: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if symbol:
        params["symbol"] = symbol
    if figi:
        params["figi"] = figi
    if calendardate:
        params["calendardate"] = calendardate
    if dimension:
        params["dimension"] = dimension
    return params


async def _fetch_table(
    table_code: str,
    api_key: str,
    params: dict[str, Any],
) -> tuple[bool, str | None, list[dict[str, Any]] | None, str | None]:
    """Run an SDK get_table call. Returns (success, error, records, msg)."""
    try:
        import nasdaqdatalink  # type: ignore[import-untyped]
    except ImportError:
        return False, _missing_sdk_error(), None, None

    try:
        nasdaqdatalink.ApiConfig.api_key = api_key
        data = nasdaqdatalink.get_table(table_code, **params)
    except Exception as exc:
        return False, f"Failed to fetch {table_code} data: {exc}", None, None

    # DataFrame .empty raises AttributeError on Nones; guard.
    if data is None or getattr(data, "empty", False):
        return True, None, [], "No data found for the specified criteria."

    return True, None, _dataframe_to_records(data), None


@tool(args_schema=GetBalanceSheetInput)
@serialize_pydantic_return
async def get_balance_sheet(
    api_key: str,
    symbol: str | None = None,
    figi: str | None = None,
    calendardate: str | None = None,
    dimension: str | None = None,
) -> GetBalanceSheetOutput:
    """Fetch balance sheet data from Nasdaq Data Link (NDAQ/BS)."""
    if not symbol and not figi:
        return GetBalanceSheetOutput(
            success=False, error=_missing_filter_error("get_balance_sheet")
        )
    if not api_key or not api_key.strip():
        return GetBalanceSheetOutput(
            success=False, error=_empty_key_error("get_balance_sheet")
        )

    ok, err, records, msg = await _fetch_table(
        "NDAQ/BS",
        api_key,
        _build_params(symbol, figi, calendardate, dimension),
    )
    return GetBalanceSheetOutput(
        success=ok, error=err, records=records or [], message=msg
    )


@tool(args_schema=GetCashFlowInput)
@serialize_pydantic_return
async def get_cash_flow(
    api_key: str,
    symbol: str | None = None,
    figi: str | None = None,
    calendardate: str | None = None,
    dimension: str | None = None,
) -> GetCashFlowOutput:
    """Fetch cash flow statement data from Nasdaq Data Link (NDAQ/CF)."""
    if not symbol and not figi:
        return GetCashFlowOutput(
            success=False, error=_missing_filter_error("get_cash_flow")
        )
    if not api_key or not api_key.strip():
        return GetCashFlowOutput(success=False, error=_empty_key_error("get_cash_flow"))

    ok, err, records, msg = await _fetch_table(
        "NDAQ/CF",
        api_key,
        _build_params(symbol, figi, calendardate, dimension),
    )
    return GetCashFlowOutput(success=ok, error=err, records=records or [], message=msg)


@tool(args_schema=GetCompanyStatsInput)
@serialize_pydantic_return
async def get_company_stats(
    api_key: str,
    symbol: str | None = None,
    figi: str | None = None,
) -> GetCompanyStatsOutput:
    """Fetch company statistics from Nasdaq Data Link (NDAQ/STAT)."""
    if not symbol and not figi:
        return GetCompanyStatsOutput(
            success=False, error=_missing_filter_error("get_company_stats")
        )
    if not api_key or not api_key.strip():
        return GetCompanyStatsOutput(
            success=False, error=_empty_key_error("get_company_stats")
        )

    ok, err, records, msg = await _fetch_table(
        "NDAQ/STAT", api_key, _build_params(symbol, figi)
    )
    return GetCompanyStatsOutput(
        success=ok, error=err, records=records or [], message=msg
    )


@tool(args_schema=GetFundamentalDetailsInput)
@serialize_pydantic_return
async def get_fundamental_details(
    api_key: str,
    symbol: str | None = None,
    figi: str | None = None,
    calendardate: str | None = None,
    dimension: str | None = None,
) -> GetFundamentalDetailsOutput:
    """Fetch detailed fundamental data from Nasdaq Data Link (NDAQ/FD)."""
    if not symbol and not figi:
        return GetFundamentalDetailsOutput(
            success=False, error=_missing_filter_error("get_fundamental_details")
        )
    if not api_key or not api_key.strip():
        return GetFundamentalDetailsOutput(
            success=False, error=_empty_key_error("get_fundamental_details")
        )

    ok, err, records, msg = await _fetch_table(
        "NDAQ/FD",
        api_key,
        _build_params(symbol, figi, calendardate, dimension),
    )
    return GetFundamentalDetailsOutput(
        success=ok, error=err, records=records or [], message=msg
    )


@tool(args_schema=GetFundamentalSummaryInput)
@serialize_pydantic_return
async def get_fundamental_summary(
    api_key: str,
    symbol: str | None = None,
    figi: str | None = None,
    calendardate: str | None = None,
    dimension: str | None = None,
) -> GetFundamentalSummaryOutput:
    """Fetch fundamental summary data from Nasdaq Data Link (NDAQ/FS)."""
    if not symbol and not figi:
        return GetFundamentalSummaryOutput(
            success=False, error=_missing_filter_error("get_fundamental_summary")
        )
    if not api_key or not api_key.strip():
        return GetFundamentalSummaryOutput(
            success=False, error=_empty_key_error("get_fundamental_summary")
        )

    ok, err, records, msg = await _fetch_table(
        "NDAQ/FS",
        api_key,
        _build_params(symbol, figi, calendardate, dimension),
    )
    return GetFundamentalSummaryOutput(
        success=ok, error=err, records=records or [], message=msg
    )


@tool(args_schema=GetReferenceDataInput)
@serialize_pydantic_return
async def get_reference_data(
    api_key: str,
    symbol: str | None = None,
    figi: str | None = None,
) -> GetReferenceDataOutput:
    """Fetch reference data from Nasdaq Data Link (NDAQ/RD).

    Unlike the other table-query actions, legacy does NOT require
    symbol/figi here — preserving that permissive behavior.
    """
    if not api_key or not api_key.strip():
        return GetReferenceDataOutput(
            success=False, error=_empty_key_error("get_reference_data")
        )

    ok, err, records, msg = await _fetch_table(
        "NDAQ/RD", api_key, _build_params(symbol, figi)
    )
    return GetReferenceDataOutput(
        success=ok,
        error=err,
        records=records or [],
        message=(
            msg
            if msg is None
            else "No reference data found for the specified criteria."
        ),
    )


@tool(args_schema=ListAvailableFieldsInput)
@serialize_pydantic_return
async def list_available_fields(
    api_key: str, table_type: str
) -> ListAvailableFieldsOutput:
    """List available fields for a Nasdaq Data Link table (no API call)."""
    normalized = table_type.lower().replace(" ", "_")
    if normalized not in FIELD_MAPPINGS:
        return ListAvailableFieldsOutput(
            success=False,
            error=(
                f"Invalid table_type: {table_type}. Valid options: "
                f"{list(FIELD_MAPPINGS.keys())}"
            ),
        )

    fields = [NasdaqField.model_validate(f) for f in FIELD_MAPPINGS[normalized]]
    return ListAvailableFieldsOutput(
        success=True, table_type=normalized, fields=fields
    )
