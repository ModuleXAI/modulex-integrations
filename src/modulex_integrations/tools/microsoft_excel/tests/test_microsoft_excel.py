"""Happy-path tests for every microsoft_excel @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.microsoft_excel import (
    TOOLS,
    add_a_worksheet_tablerow,
    add_row,
    find_row,
    get_columns,
    get_spreadsheet,
    get_table_rows,
    list_folder_id_options,
    manifest,
    update_cell,
    update_worksheet_tablerow,
)
from modulex_integrations.tools.microsoft_excel.outputs import (
    AddAWorksheetTablerowOutput,
    AddRowOutput,
    FindRowOutput,
    GetColumnsOutput,
    GetSpreadsheetOutput,
    GetTableRowsOutput,
    ListFolderIdOptionsOutput,
    UpdateCellOutput,
    UpdateWorksheetTablerowOutput,
)

API = "https://graph.microsoft.com/v1.0"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_9_actions(self) -> None:
        assert len(manifest.actions) == 9

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_add_a_worksheet_tablerow(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/me/drive/items/sheet1/workbook/tables/tbl1/rows/add",
        json={
            # TODO: fill in a representative response shape from
            # https://learn.microsoft.com/en-us/graph/api/tablerowcollection-add
            "index": 5,
            "values": [["a", "b", "c"]],
        },
    )

    result_dict = await add_a_worksheet_tablerow.ainvoke(
        _args(sheet_id="sheet1", table_id="tbl1", values=[["a", "b", "c"]])
    )

    assert isinstance(result_dict, dict)
    result = AddAWorksheetTablerowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.row is not None
    assert result.row.index == 5


@pytest.mark.asyncio
async def test_add_row(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drive/items/sheet1/workbook/worksheets/Sheet1/usedRange",
        json={
            # TODO: fill in a representative usedRange payload
            "address": "Sheet1!A1:C3",
            "rowCount": 3,
            "columnCount": 3,
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=(
            f"{API}/me/drive/items/sheet1/workbook/worksheets/"
            "Sheet1/range(address='A4:C4')/insert"
        ),
        json={},
    )
    httpx_mock.add_response(
        method="PATCH",
        url=(
            f"{API}/me/drive/items/sheet1/workbook/worksheets/"
            "Sheet1/range(address='A4:C4')"
        ),
        json={
            "address": "Sheet1!A4:C4",
            "values": [[1, 2, 3]],
        },
    )

    result_dict = await add_row.ainvoke(
        _args(sheet_id="sheet1", worksheet="Sheet1", values=[1, 2, 3])
    )

    assert isinstance(result_dict, dict)
    result = AddRowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.address == "Sheet1!A4:C4"


@pytest.mark.asyncio
async def test_find_row(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drive/items/sheet1/workbook/worksheets/Sheet1/usedRange",
        json={
            # TODO: representative usedRange
            "address": "Sheet1!A1:C3",
            "rowCount": 3,
            "columnCount": 3,
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}/me/drive/items/sheet1/workbook/worksheets/"
            "Sheet1/range(address='A1:A3')"
        ),
        json={
            # TODO: representative column read
            "values": [["alpha"], ["target"], ["gamma"]],
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}/me/drive/items/sheet1/workbook/worksheets/"
            "Sheet1/range(address='A2:C2')"
        ),
        json={
            "address": "Sheet1!A2:C2",
            "values": [["target", "x", "y"]],
        },
    )

    result_dict = await find_row.ainvoke(
        _args(sheet_id="sheet1", worksheet="Sheet1", column="A", value="target")
    )

    assert isinstance(result_dict, dict)
    result = FindRowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.found is True
    assert result.row_number == 2


@pytest.mark.asyncio
async def test_get_columns(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drive/items/sheet1/workbook/worksheets/Sheet1/usedRange",
        json={
            # TODO: representative usedRange
            "address": "Sheet1!A1:C2",
            "rowCount": 2,
            "columnCount": 3,
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}/me/drive/items/sheet1/workbook/worksheets/"
            "Sheet1/range(address='A1:A2')"
        ),
        json={"values": [["a1"], ["a2"]]},
    )

    result_dict = await get_columns.ainvoke(
        _args(sheet_id="sheet1", worksheet="Sheet1", columns=["A"])
    )

    assert isinstance(result_dict, dict)
    result = GetColumnsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.values == {"A": ["a1", "a2"]}


@pytest.mark.asyncio
async def test_get_spreadsheet(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drive/items/sheet1/workbook/worksheets/Sheet1/usedRange",
        json={
            # TODO: representative usedRange
            "address": "Sheet1!A1:B2",
            "rowCount": 2,
            "columnCount": 2,
            "values": [["a", "b"], ["c", "d"]],
        },
    )

    result_dict = await get_spreadsheet.ainvoke(
        _args(sheet_id="sheet1", worksheet="Sheet1")
    )

    assert isinstance(result_dict, dict)
    result = GetSpreadsheetOutput.model_validate(result_dict)
    assert result.success is True
    assert result.row_count == 2


@pytest.mark.asyncio
async def test_get_table_rows(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me/drive/items/sheet1/workbook/tables/tbl1/rows",
        json={
            # TODO: fill in a representative workbookTableRow list payload
            "value": [
                {"index": 0, "values": [["a", "b"]]},
                {"index": 1, "values": [["c", "d"]]},
            ],
        },
    )

    result_dict = await get_table_rows.ainvoke(
        _args(sheet_id="sheet1", table_id="tbl1")
    )

    assert isinstance(result_dict, dict)
    result = GetTableRowsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.rows) == 2


@pytest.mark.asyncio
async def test_list_folder_id_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/$batch",
        json={
            # TODO: fill in a representative $batch responses payload
            "responses": [
                {
                    "id": "root",
                    "status": 200,
                    "body": {
                        "value": [
                            {
                                "id": "fld1",
                                "name": "Folder1",
                                "folder": {"childCount": 0},
                                "parentReference": {"id": "root"},
                            }
                        ]
                    },
                }
            ]
        },
    )

    result_dict = await list_folder_id_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListFolderIdOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.options) == 1


@pytest.mark.asyncio
async def test_update_cell(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=(
            f"{API}/me/drive/items/sheet1/workbook/worksheets/"
            "Sheet1/range(address='A1:A1')"
        ),
        json={
            # TODO: representative range update payload
            "address": "Sheet1!A1",
            "values": [["hello"]],
        },
    )

    result_dict = await update_cell.ainvoke(
        _args(sheet_id="sheet1", worksheet="Sheet1", cell="A1", value="hello")
    )

    assert isinstance(result_dict, dict)
    result = UpdateCellOutput.model_validate(result_dict)
    assert result.success is True
    assert result.values == [["hello"]]


@pytest.mark.asyncio
async def test_update_worksheet_tablerow(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=(
            f"{API}/me/drive/items/sheet1/workbook/tables/"
            "tbl1/rows/ItemAt(index=0)"
        ),
        json={
            # TODO: representative table row update payload
            "index": 0,
            "values": [[1, 2, 3]],
        },
    )

    result_dict = await update_worksheet_tablerow.ainvoke(
        _args(sheet_id="sheet1", table_id="tbl1", row_id=0, values=[1, 2, 3])
    )

    assert isinstance(result_dict, dict)
    result = UpdateWorksheetTablerowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.row is not None
    assert result.row.index == 0


# --- Failure-path test (credential guard) ----------------------------------


@pytest.mark.asyncio
async def test_get_spreadsheet_empty_token() -> None:
    """Credential guard returns success=False when access_token is missing."""
    result_dict = await get_spreadsheet.ainvoke(
        _args(
            auth_data={},
            sheet_id="sheet1",
            worksheet="Sheet1",
        )
    )
    assert isinstance(result_dict, dict)
    result = GetSpreadsheetOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access_token" in result.error
