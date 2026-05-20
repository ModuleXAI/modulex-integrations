"""Happy-path tests for every google_appsheet @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_appsheet import (
    TOOLS,
    add_row,
    delete_row,
    get_rows,
    manifest,
    update_row,
)
from modulex_integrations.tools.google_appsheet.outputs import (
    AddRowOutput,
    DeleteRowOutput,
    GetRowsOutput,
    UpdateRowOutput,
)

API = "https://api.appsheet.com/api/v2/apps"

_APP_ID = "fake-app-id"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(app_id=_APP_ID, api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_add_row(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{_APP_ID}/tables/MyTable/Action",
        json={
            "Rows": [{"Name": "Alice", "Age": "30"}],
        },
    )

    result_dict = await add_row.ainvoke(_args(table_name="MyTable", row={"Name": "Alice", "Age": "30"}))

    assert isinstance(result_dict, dict)
    result = AddRowOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.rows) == 1


@pytest.mark.asyncio
async def test_delete_row(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{_APP_ID}/tables/MyTable/Action",
        json={
            "Rows": [{"_RowNumber": "1"}],
        },
    )

    result_dict = await delete_row.ainvoke(_args(table_name="MyTable", row={"_RowNumber": "1"}))

    assert isinstance(result_dict, dict)
    result = DeleteRowOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_rows(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{_APP_ID}/tables/MyTable/Action",
        json=[
            {"Name": "Alice", "Age": "30"},
            {"Name": "Bob", "Age": "25"},
        ],
    )

    result_dict = await get_rows.ainvoke(_args(table_name="MyTable"))

    assert isinstance(result_dict, dict)
    result = GetRowsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.rows) == 2


@pytest.mark.asyncio
async def test_update_row(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/{_APP_ID}/tables/MyTable/Action",
        json={
            "Rows": [{"Name": "Alice", "Age": "31"}],
        },
    )

    result_dict = await update_row.ainvoke(_args(table_name="MyTable", row={"Name": "Alice", "Age": "31"}))

    assert isinstance(result_dict, dict)
    result = UpdateRowOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.rows) == 1


@pytest.mark.asyncio
async def test_add_row_validates_empty_api_key() -> None:
    result_dict = await add_row.ainvoke({"table_name": "T", "row": {}, "app_id": "x", "api_key": ""})
    result = AddRowOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")
