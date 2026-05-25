"""Tests for the Nasdaq Data Link integration.

SDK pattern: mocks ``nasdaqdatalink`` via ``patch.dict(sys.modules)``
so the real SDK isn't exercised. Real ``pandas.DataFrame`` objects
are used for the SDK mock return values so the ``_dataframe_to_records``
NaN→None coercion is genuinely tested.
"""
from __future__ import annotations

import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd  # type: ignore[import-untyped]
import pytest

from modulex_integrations.tools.nasdaq import (
    TOOLS,
    get_balance_sheet,
    get_cash_flow,
    get_company_stats,
    get_reference_data,
    list_available_fields,
    manifest,
)
from modulex_integrations.tools.nasdaq.outputs import (
    GetBalanceSheetOutput,
    GetCashFlowOutput,
    GetCompanyStatsOutput,
    GetReferenceDataOutput,
    ListAvailableFieldsOutput,
)

_API_KEY = "nasdaq-fake-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


def _mock_nasdaq(get_table_return: Any) -> MagicMock:
    """Build a MagicMock substituting for the nasdaqdatalink module."""
    sdk = MagicMock()
    sdk.ApiConfig = MagicMock()
    sdk.get_table = MagicMock(return_value=get_table_return)
    return sdk


class TestManifest:
    def test_manifest_exposes_seven_actions(self) -> None:
        assert len(manifest.actions) == 7

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]

    def test_test_endpoint_embeds_api_key_in_url(self) -> None:
        # ``params`` placeholders are NOT substituted by the modulex runtime
        # — the credential must live in the URL query string directly.
        auth = manifest.auth_schemas[0]
        assert auth.test_endpoint is not None
        assert auth.test_endpoint.params == {}
        assert "api_key={api_key}" in auth.test_endpoint.url
        assert "qopts.per_page=1" in auth.test_endpoint.url


@pytest.mark.asyncio
async def test_get_balance_sheet_success() -> None:
    df = pd.DataFrame(
        [
            {"symbol": "AAPL", "calendardate": "2026-03-31", "assets": 350_000_000_000},
            {"symbol": "AAPL", "calendardate": "2025-12-31", "assets": 340_000_000_000},
        ]
    )
    sdk = _mock_nasdaq(df)

    with patch.dict(sys.modules, {"nasdaqdatalink": sdk}):
        result_dict = await get_balance_sheet.ainvoke(_args(symbol="AAPL", dimension="MRQ"))

    assert isinstance(result_dict, dict)
    result = GetBalanceSheetOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.records) == 2
    assert result.records[0]["symbol"] == "AAPL"

    # SDK was called with the right table + params, and ApiConfig was set.
    assert sdk.ApiConfig.api_key == _API_KEY
    sdk.get_table.assert_called_once_with("NDAQ/BS", symbol="AAPL", dimension="MRQ")


@pytest.mark.asyncio
async def test_get_balance_sheet_requires_symbol_or_figi() -> None:
    result = GetBalanceSheetOutput.model_validate(
        await get_balance_sheet.ainvoke(_args())
    )
    assert result.success is False
    assert result.error is not None and "symbol or figi" in result.error


@pytest.mark.asyncio
async def test_get_balance_sheet_empty_dataframe() -> None:
    df = pd.DataFrame()
    sdk = _mock_nasdaq(df)

    with patch.dict(sys.modules, {"nasdaqdatalink": sdk}):
        result = GetBalanceSheetOutput.model_validate(
            await get_balance_sheet.ainvoke(_args(symbol="ZZZZ"))
        )
    assert result.success is True
    assert result.records == []
    assert result.message is not None and "No data" in result.message


@pytest.mark.asyncio
async def test_get_balance_sheet_handles_nan() -> None:
    # NaN should be coerced to None for JSON serializability.
    df = pd.DataFrame([{"symbol": "AAPL", "assets": 1.0, "ppnenet": float("nan")}])
    sdk = _mock_nasdaq(df)

    with patch.dict(sys.modules, {"nasdaqdatalink": sdk}):
        result = GetBalanceSheetOutput.model_validate(
            await get_balance_sheet.ainvoke(_args(symbol="AAPL"))
        )
    assert result.success is True
    assert result.records[0]["ppnenet"] is None


@pytest.mark.asyncio
async def test_get_cash_flow_with_figi() -> None:
    df = pd.DataFrame([{"figi": "BBG000B9XRY4", "ncfo": 100}])
    sdk = _mock_nasdaq(df)

    with patch.dict(sys.modules, {"nasdaqdatalink": sdk}):
        result = GetCashFlowOutput.model_validate(
            await get_cash_flow.ainvoke(_args(figi="BBG000B9XRY4"))
        )
    assert result.success is True
    assert result.records[0]["ncfo"] == 100
    sdk.get_table.assert_called_once_with("NDAQ/CF", figi="BBG000B9XRY4")


@pytest.mark.asyncio
async def test_get_company_stats() -> None:
    df = pd.DataFrame([{"symbol": "MSFT", "marketcap": 3_000_000_000_000, "pe": 35.2}])
    sdk = _mock_nasdaq(df)

    with patch.dict(sys.modules, {"nasdaqdatalink": sdk}):
        result = GetCompanyStatsOutput.model_validate(
            await get_company_stats.ainvoke(_args(symbol="MSFT"))
        )
    assert result.success is True
    assert result.records[0]["pe"] == 35.2


@pytest.mark.asyncio
async def test_get_reference_data_does_not_require_symbol_or_figi() -> None:
    # Legacy permissive behavior: reference data is callable without
    # symbol/figi (returns the whole table).
    df = pd.DataFrame([{"symbol": "AAPL", "exchange": "NASDAQ"}])
    sdk = _mock_nasdaq(df)

    with patch.dict(sys.modules, {"nasdaqdatalink": sdk}):
        result = GetReferenceDataOutput.model_validate(
            await get_reference_data.ainvoke(_args())
        )
    assert result.success is True
    assert result.records[0]["exchange"] == "NASDAQ"


@pytest.mark.asyncio
async def test_list_available_fields() -> None:
    result = ListAvailableFieldsOutput.model_validate(
        await list_available_fields.ainvoke(_args(table_type="balance_sheet"))
    )
    assert result.success is True
    assert result.table_type == "balance_sheet"
    assert len(result.fields) > 10
    assert any(f.name == "assets" for f in result.fields)


@pytest.mark.asyncio
async def test_list_available_fields_rejects_unknown_table() -> None:
    result = ListAvailableFieldsOutput.model_validate(
        await list_available_fields.ainvoke(_args(table_type="bogus_table"))
    )
    assert result.success is False
    assert result.error is not None and "Invalid table_type" in result.error


@pytest.mark.asyncio
async def test_missing_sdk_returns_install_message() -> None:
    # If the SDK isn't importable, every API-calling tool should
    # surface a clear install message instead of crashing.
    with patch.dict(sys.modules, {"nasdaqdatalink": None}):
        result = GetBalanceSheetOutput.model_validate(
            await get_balance_sheet.ainvoke(_args(symbol="AAPL"))
        )
    assert result.success is False
    assert result.error is not None and "nasdaq-data-link" in result.error


@pytest.mark.asyncio
async def test_sdk_exception_surfaces_as_failure() -> None:
    sdk = MagicMock()
    sdk.ApiConfig = MagicMock()
    sdk.get_table = MagicMock(side_effect=RuntimeError("rate limited"))

    with patch.dict(sys.modules, {"nasdaqdatalink": sdk}):
        result = GetBalanceSheetOutput.model_validate(
            await get_balance_sheet.ainvoke(_args(symbol="AAPL"))
        )
    assert result.success is False
    assert result.error is not None and "rate limited" in result.error


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result = GetBalanceSheetOutput.model_validate(
        await get_balance_sheet.ainvoke({"api_key": "", "symbol": "AAPL"})
    )
    assert result.success is False
    assert result.error is not None and "API key" in result.error
