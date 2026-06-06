"""Happy-path tests for every google_sheets @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_sheets import (
    TOOLS,
    add_rows,
    add_worksheet,
    clear_rows,
    delete_rows,
    delete_worksheet,
    find_rows,
    get_spreadsheet_info,
    get_values_in_range,
    list_worksheets,
    manifest,
    new_spreadsheet,
    read_rows,
    update_cell,
    update_row,
)
from modulex_integrations.tools.google_sheets.outputs import (
    AddRowsOutput,
    AddWorksheetOutput,
    ClearRowsOutput,
    DeleteRowsOutput,
    DeleteWorksheetOutput,
    FindRowsOutput,
    GetSpreadsheetInfoOutput,
    GetValuesInRangeOutput,
    ListWorksheetsOutput,
    NewSpreadsheetOutput,
    ReadRowsOutput,
    UpdateCellOutput,
    UpdateRowOutput,
)

SHEETS_API = "https://sheets.googleapis.com/v4"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_13_actions(self) -> None:
        assert len(manifest.actions) == 13

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_new_spreadsheet(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: replace with a real Sheets create response from
    #       https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/create
    httpx_mock.add_response(
        method="POST",
        url=f"{SHEETS_API}/spreadsheets",
        json={
            "spreadsheetId": "new-id-123",
            "properties": {"title": "My Sheet"},
            "sheets": [{"properties": {"title": "Sheet1", "sheetId": 0}}],
        },
    )

    result_dict = await new_spreadsheet.ainvoke(_args(title="My Sheet"))

    assert isinstance(result_dict, dict)
    result = NewSpreadsheetOutput.model_validate(result_dict)
    assert result.success is True
    assert result.spreadsheet_id == "new-id-123"
    assert result.url == "https://docs.google.com/spreadsheets/d/new-id-123/edit"


@pytest.mark.asyncio
async def test_get_spreadsheet_info(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: tighten this fixture once real Sheets API payloads are wired up.
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{SHEETS_API}/spreadsheets/abc123"
            "?fields=spreadsheetId%2Cproperties.title%2Csheets.properties"
        ),
        json={
            "spreadsheetId": "abc123",
            "properties": {"title": "Demo"},
            "sheets": [
                {
                    "properties": {
                        "sheetId": 0,
                        "title": "Sheet1",
                        "gridProperties": {"rowCount": 100, "columnCount": 26},
                    },
                },
            ],
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{SHEETS_API}/spreadsheets/abc123/values/Sheet1%211%3A1",
        json={"values": [["Name", "Email"]]},
    )

    result_dict = await get_spreadsheet_info.ainvoke(_args(spreadsheet_id="abc123"))

    assert isinstance(result_dict, dict)
    result = GetSpreadsheetInfoOutput.model_validate(result_dict)
    assert result.success is True
    assert result.title == "Demo"
    assert result.worksheets is not None
    assert result.worksheets[0].headers == ["Name", "Email"]


@pytest.mark.asyncio
async def test_list_worksheets(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: substitute a real spreadsheets.get response with multiple sheets.
    httpx_mock.add_response(
        method="GET",
        url=f"{SHEETS_API}/spreadsheets/sheet-id?fields=sheets.properties",
        json={
            "sheets": [
                {
                    "properties": {
                        "sheetId": 0,
                        "title": "Sheet1",
                        "index": 0,
                        "sheetType": "GRID",
                        "gridProperties": {"rowCount": 100, "columnCount": 26},
                    },
                },
            ],
        },
    )

    result_dict = await list_worksheets.ainvoke(_args(spreadsheet_id="sheet-id"))

    assert isinstance(result_dict, dict)
    result = ListWorksheetsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.worksheets is not None
    assert result.worksheets[0].title == "Sheet1"


@pytest.mark.asyncio
async def test_add_worksheet(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: replace with a real batchUpdate addSheet response.
    httpx_mock.add_response(
        method="POST",
        url=f"{SHEETS_API}/spreadsheets/sheet-id:batchUpdate",
        json={
            "replies": [
                {
                    "addSheet": {
                        "properties": {
                            "sheetId": 42,
                            "title": "NewTab",
                            "index": 1,
                        },
                    },
                },
            ],
        },
    )

    result_dict = await add_worksheet.ainvoke(
        _args(spreadsheet_id="sheet-id", title="NewTab"),
    )

    assert isinstance(result_dict, dict)
    result = AddWorksheetOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sheet_id == 42
    assert result.title == "NewTab"


@pytest.mark.asyncio
async def test_delete_worksheet(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: substitute a real batchUpdate deleteSheet response (usually empty replies).
    httpx_mock.add_response(
        method="POST",
        url=f"{SHEETS_API}/spreadsheets/sheet-id:batchUpdate",
        json={"replies": [{}]},
    )

    result_dict = await delete_worksheet.ainvoke(
        _args(spreadsheet_id="sheet-id", worksheet_id=42),
    )

    assert isinstance(result_dict, dict)
    result = DeleteWorksheetOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted_sheet_id == 42


@pytest.mark.asyncio
async def test_read_rows(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: replace with a real spreadsheets.values.get response.
    httpx_mock.add_response(
        method="GET",
        url=f"{SHEETS_API}/spreadsheets/sheet-id/values/Sheet1",
        json={
            "values": [
                ["Name", "Email"],
                ["Alice", "alice@example.com"],
                ["Bob", "bob@example.com"],
            ],
        },
    )

    result_dict = await read_rows.ainvoke(
        _args(spreadsheet_id="sheet-id", sheet_name="Sheet1"),
    )

    assert isinstance(result_dict, dict)
    result = ReadRowsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.row_count == 2
    assert result.headers == ["Name", "Email"]


@pytest.mark.asyncio
async def test_get_values_in_range(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: replace with a real spreadsheets.values.get response.
    httpx_mock.add_response(
        method="GET",
        url=f"{SHEETS_API}/spreadsheets/sheet-id/values/Sheet1%21A1%3AB2",
        json={
            "range": "Sheet1!A1:B2",
            "values": [["A1-val", "B1-val"], ["A2-val", "B2-val"]],
        },
    )

    result_dict = await get_values_in_range.ainvoke(
        _args(spreadsheet_id="sheet-id", sheet_name="Sheet1", range="A1:B2"),
    )

    assert isinstance(result_dict, dict)
    result = GetValuesInRangeOutput.model_validate(result_dict)
    assert result.success is True
    assert result.row_count == 2
    assert result.range == "Sheet1!A1:B2"


@pytest.mark.asyncio
async def test_find_rows(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: replace with a real spreadsheets.values.get response covering the sheet.
    httpx_mock.add_response(
        method="GET",
        url=f"{SHEETS_API}/spreadsheets/sheet-id/values/Sheet1",
        json={
            "values": [
                ["Name", "Email"],
                ["Alice", "alice@example.com"],
                ["Bob", "bob@example.com"],
            ],
        },
    )

    result_dict = await find_rows.ainvoke(
        _args(
            spreadsheet_id="sheet-id",
            sheet_name="Sheet1",
            column="Name",
            search_value="alice",
            match_type="exact",
        ),
    )

    assert isinstance(result_dict, dict)
    result = FindRowsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.match_count == 1


@pytest.mark.asyncio
async def test_add_rows(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: substitute a real spreadsheets.values.append response.
    httpx_mock.add_response(
        method="POST",
        url=(
            f"{SHEETS_API}/spreadsheets/sheet-id/values/Sheet1:append"
            "?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS"
        ),
        json={
            "spreadsheetId": "sheet-id",
            "updates": {
                "updatedRange": "Sheet1!A5:B6",
                "updatedRows": 2,
                "updatedColumns": 2,
                "updatedCells": 4,
            },
        },
    )

    result_dict = await add_rows.ainvoke(
        _args(
            spreadsheet_id="sheet-id",
            sheet_name="Sheet1",
            rows=[["Alice", "alice@example.com"], ["Bob", "bob@example.com"]],
            has_headers=False,
        ),
    )

    assert isinstance(result_dict, dict)
    result = AddRowsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.rows_added == 2


@pytest.mark.asyncio
async def test_update_row(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: substitute a real spreadsheets.values.update response.
    httpx_mock.add_response(
        method="PUT",
        url=(
            f"{SHEETS_API}/spreadsheets/sheet-id/values/Sheet1%213%3A3"
            "?valueInputOption=USER_ENTERED"
        ),
        json={
            "spreadsheetId": "sheet-id",
            "updatedRange": "Sheet1!3:3",
            "updatedRows": 1,
            "updatedColumns": 2,
            "updatedCells": 2,
        },
    )

    result_dict = await update_row.ainvoke(
        _args(
            spreadsheet_id="sheet-id",
            sheet_name="Sheet1",
            row=3,
            values=["Carol", "carol@example.com"],
        ),
    )

    assert isinstance(result_dict, dict)
    result = UpdateRowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.updated_rows == 1


@pytest.mark.asyncio
async def test_update_cell(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: substitute a real spreadsheets.values.update response for a single cell.
    httpx_mock.add_response(
        method="PUT",
        url=(
            f"{SHEETS_API}/spreadsheets/sheet-id/values/Sheet1%21B5%3AB5"
            "?valueInputOption=USER_ENTERED"
        ),
        json={
            "spreadsheetId": "sheet-id",
            "updatedRange": "Sheet1!B5",
            "updatedCells": 1,
        },
    )

    result_dict = await update_cell.ainvoke(
        _args(
            spreadsheet_id="sheet-id",
            sheet_name="Sheet1",
            cell="B5",
            value="hello",
        ),
    )

    assert isinstance(result_dict, dict)
    result = UpdateCellOutput.model_validate(result_dict)
    assert result.success is True
    assert result.updated_cells == 1


@pytest.mark.asyncio
async def test_clear_rows(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: replace with a real spreadsheets.values.clear response.
    httpx_mock.add_response(
        method="POST",
        url=f"{SHEETS_API}/spreadsheets/sheet-id/values/Sheet1%212%3A4:clear",
        json={
            "spreadsheetId": "sheet-id",
            "clearedRange": "Sheet1!A2:Z4",
        },
    )

    result_dict = await clear_rows.ainvoke(
        _args(
            spreadsheet_id="sheet-id",
            sheet_name="Sheet1",
            start_index=2,
            end_index=4,
        ),
    )

    assert isinstance(result_dict, dict)
    result = ClearRowsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.cleared_range == "Sheet1!A2:Z4"


@pytest.mark.asyncio
async def test_delete_rows(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: substitute a real batchUpdate deleteDimension response.
    httpx_mock.add_response(
        method="POST",
        url=f"{SHEETS_API}/spreadsheets/sheet-id:batchUpdate",
        json={"replies": [{}]},
    )

    result_dict = await delete_rows.ainvoke(
        _args(
            spreadsheet_id="sheet-id",
            worksheet_id=0,
            start_index=2,
            end_index=5,
        ),
    )

    assert isinstance(result_dict, dict)
    result = DeleteRowsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted_count == 4


@pytest.mark.asyncio
async def test_new_spreadsheet_empty_credentials(httpx_mock):  # type: ignore[no-untyped-def]
    """Verify that empty credentials return a clear error without hitting the wire."""
    result_dict = await new_spreadsheet.ainvoke(
        _args(**{"auth_type": "oauth2", "auth_data": {}, "title": "My Sheet"}),
    )
    assert isinstance(result_dict, dict)
    result = NewSpreadsheetOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
