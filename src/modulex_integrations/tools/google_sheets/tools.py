"""Google Sheets LangChain @tool functions."""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
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
    WorksheetInfo,
    WorksheetSummary,
)

__all__ = [
    "add_rows",
    "add_worksheet",
    "clear_rows",
    "delete_rows",
    "delete_worksheet",
    "find_rows",
    "get_spreadsheet_info",
    "get_values_in_range",
    "list_worksheets",
    "new_spreadsheet",
    "read_rows",
    "update_cell",
    "update_row",
]

_SHEETS_BASE = "https://sheets.googleapis.com/v4"
_TIMEOUT = 30.0


# --- Auth helpers ----------------------------------------------------------


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the upstream API based on auth_type/auth_data."""
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    token: str | None = None
    if auth_type == "oauth2":
        token = auth_data.get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _format_http_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
        message = (
            payload.get("error", {}).get("message")
            if isinstance(payload, dict)
            else None
        )
        if message:
            return f"Google Sheets API error ({response.status_code}): {message}"
    except (ValueError, KeyError):
        pass
    return f"Google Sheets API error ({response.status_code}): {response.text}"


def _encode_range(sheet_name: str, sub_range: str | None = None) -> str:
    range_str = f"'{sheet_name}'" if " " in sheet_name or "!" in sheet_name else sheet_name
    if sub_range:
        range_str = f"{range_str}!{sub_range}"
    return quote(range_str, safe="")


def _row_index(letter_or_index: int) -> str:
    return str(letter_or_index)


def _index_to_column_letter(index: int) -> str:
    letter = ""
    i = index
    while i >= 0:
        letter = chr((i % 26) + 65) + letter
        i = i // 26 - 1
    return letter


def _rows_to_objects(headers: list[Any], data_rows: list[list[Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row_idx, row in enumerate(data_rows):
        obj: dict[str, Any] = {"_row": row_idx + 2}  # data starts at row 2
        for i, header in enumerate(headers):
            key = str(header) if header is not None else f"col_{i}"
            obj[key] = row[i] if i < len(row) else None
        out.append(obj)
    return out


# --- Input schemas ---------------------------------------------------------


class NewSpreadsheetInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    title: str = Field(description="The title of the new spreadsheet.")
    sheet_name: str | None = Field(
        default=None,
        description="Name for the first worksheet. Default: 'Sheet1'.",
    )
    headers: list[str] | None = Field(
        default=None,
        description='Optional column headers to add as row 1. Example: ["Name", "Email"].',
    )


class GetSpreadsheetInfoInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    spreadsheet_id: str = Field(description="The spreadsheet ID from the Google Sheets URL.")


class ListWorksheetsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    spreadsheet_id: str = Field(description="The spreadsheet ID from the Google Sheets URL.")


class AddWorksheetInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    spreadsheet_id: str = Field(description="The spreadsheet ID from the Google Sheets URL.")
    title: str = Field(description="The name of the new worksheet (tab).")
    headers: list[str] | None = Field(
        default=None,
        description='Optional column headers to add as row 1. Example: ["Name", "Email"].',
    )


class DeleteWorksheetInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    spreadsheet_id: str = Field(description="The spreadsheet ID from the Google Sheets URL.")
    worksheet_id: int = Field(description="The numeric sheet ID to delete.")


class ReadRowsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    spreadsheet_id: str = Field(description="The spreadsheet ID from the Google Sheets URL.")
    sheet_name: str = Field(description="The worksheet (tab) name.")
    range: str | None = Field(
        default=None,
        description="Optional A1 range within the sheet (e.g. 'A1:D10').",
    )
    has_headers: bool = Field(
        default=True,
        description="Whether row 1 contains column headers.",
    )


class GetValuesInRangeInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    spreadsheet_id: str = Field(description="The spreadsheet ID from the Google Sheets URL.")
    sheet_name: str = Field(description="The worksheet (tab) name.")
    range: str | None = Field(
        default=None,
        description="A1 range within the sheet (e.g. 'A1:E5'). Omit to read the whole sheet.",
    )


class FindRowsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    spreadsheet_id: str = Field(description="The spreadsheet ID from the Google Sheets URL.")
    sheet_name: str = Field(description="The worksheet (tab) name.")
    column: str = Field(description="Column header name or column letter (e.g. 'Name' or 'A').")
    search_value: str = Field(description="The value to search for.")
    match_type: str = Field(
        default="contains",
        description="How to match: 'exact', 'contains', or 'starts_with'.",
    )


class AddRowsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    spreadsheet_id: str = Field(description="The spreadsheet ID from the Google Sheets URL.")
    sheet_name: str = Field(description="The worksheet (tab) name.")
    rows: list[Any] = Field(
        description=(
            "Array of rows. Each row is either an array of positional cell "
            "values, or an object whose keys match the worksheet's column headers."
        ),
    )
    has_headers: bool = Field(
        default=True,
        description="Whether row 1 contains column headers (required for object rows).",
    )


class UpdateRowInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    spreadsheet_id: str = Field(description="The spreadsheet ID from the Google Sheets URL.")
    sheet_name: str = Field(description="The worksheet (tab) name.")
    row: int = Field(description="1-indexed row number to update.")
    values: list[Any] = Field(description="Array of cell values for the row, in column order.")


class UpdateCellInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    spreadsheet_id: str = Field(description="The spreadsheet ID from the Google Sheets URL.")
    sheet_name: str = Field(description="The worksheet (tab) name.")
    cell: str = Field(description="A1 notation for the cell (e.g. 'B5').")
    value: str = Field(description="The new cell value.")


class ClearRowsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    spreadsheet_id: str = Field(description="The spreadsheet ID from the Google Sheets URL.")
    sheet_name: str = Field(description="The worksheet (tab) name.")
    start_index: int = Field(description="1-indexed row to start clearing (inclusive).")
    end_index: int | None = Field(
        default=None,
        description="1-indexed row to stop clearing (inclusive). Omit for a single row.",
    )


class DeleteRowsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    spreadsheet_id: str = Field(description="The spreadsheet ID from the Google Sheets URL.")
    worksheet_id: int = Field(description="The numeric worksheet (sheet) ID.")
    start_index: int = Field(description="1-indexed first row to delete (inclusive).")
    end_index: int | None = Field(
        default=None,
        description="1-indexed last row to delete (inclusive). Omit for a single row.",
    )


# --- @tool functions ------------------------------------------------------


@tool(args_schema=NewSpreadsheetInput)
@serialize_pydantic_return
async def new_spreadsheet(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
    sheet_name: str | None = None,
    headers: list[str] | None = None,
) -> NewSpreadsheetOutput:
    """Create a new Google Spreadsheet with optional first-worksheet name and headers."""
    if not auth_data.get("access_token"):
        return NewSpreadsheetOutput(success=False, error="Missing or empty OAuth access token.")
    request_headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {"properties": {"title": title}}
    if sheet_name:
        body["sheets"] = [{"properties": {"title": sheet_name}}]
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_SHEETS_BASE}/spreadsheets",
                headers=request_headers,
                json=body,
            )
            if response.status_code not in (200, 201):
                return NewSpreadsheetOutput(success=False, error=_format_http_error(response))
            created = response.json()
            spreadsheet_id = created.get("spreadsheetId")
            sheets = created.get("sheets", []) or []
            worksheet_name = (
                sheet_name
                or (sheets[0].get("properties", {}).get("title") if sheets else None)
                or "Sheet1"
            )
            if headers and spreadsheet_id:
                append_range = _encode_range(worksheet_name)
                append_url = (
                    f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}"
                    f"/values/{append_range}:append"
                    "?valueInputOption=USER_ENTERED"
                )
                append_resp = await client.post(
                    append_url,
                    headers=request_headers,
                    json={"values": [headers]},
                )
                if append_resp.status_code not in (200, 201):
                    return NewSpreadsheetOutput(
                        success=False,
                        error=_format_http_error(append_resp),
                    )
    except httpx.TimeoutException:
        return NewSpreadsheetOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return NewSpreadsheetOutput(success=False, error=f"Call failed: {exc}")

    return NewSpreadsheetOutput(
        success=True,
        spreadsheet_id=spreadsheet_id,
        title=title,
        url=(
            f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
            if spreadsheet_id
            else None
        ),
        worksheet_name=worksheet_name,
    )


@tool(args_schema=GetSpreadsheetInfoInput)
@serialize_pydantic_return
async def get_spreadsheet_info(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
) -> GetSpreadsheetInfoOutput:
    """Return spreadsheet metadata: worksheet names, sheet IDs, row counts, and headers."""
    if not auth_data.get("access_token"):
        return GetSpreadsheetInfoOutput(success=False, error="Missing or empty OAuth access token.")
    request_headers = _get_auth_headers(auth_type, auth_data)
    fields = "spreadsheetId,properties.title,sheets.properties"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            meta_resp = await client.get(
                f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}",
                headers=request_headers,
                params={"fields": fields},
            )
            if meta_resp.status_code != 200:
                return GetSpreadsheetInfoOutput(
                    success=False,
                    error=_format_http_error(meta_resp),
                )
            meta = meta_resp.json()
            sheets = meta.get("sheets", []) or []
            results: list[WorksheetInfo] = []
            for sheet in sheets:
                props = sheet.get("properties", {}) or {}
                title = props.get("title")
                sheet_id = props.get("sheetId")
                row_count = (props.get("gridProperties") or {}).get("rowCount")
                row_headers: list[str] = []
                if title:
                    encoded = _encode_range(title, "1:1")
                    header_resp = await client.get(
                        f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}/values/{encoded}",
                        headers=request_headers,
                    )
                    if header_resp.status_code == 200:
                        values = header_resp.json().get("values") or []
                        if values:
                            row_headers = [str(v) for v in values[0]]
                results.append(
                    WorksheetInfo(
                        sheet_name=title,
                        sheet_id=sheet_id,
                        row_count=row_count,
                        headers=row_headers,
                    )
                )
    except httpx.TimeoutException:
        return GetSpreadsheetInfoOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSpreadsheetInfoOutput(success=False, error=f"Call failed: {exc}")

    title = (meta.get("properties") or {}).get("title")
    return GetSpreadsheetInfoOutput(
        success=True,
        spreadsheet_id=meta.get("spreadsheetId") or spreadsheet_id,
        title=title,
        worksheets=results,
    )


@tool(args_schema=ListWorksheetsInput)
@serialize_pydantic_return
async def list_worksheets(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
) -> ListWorksheetsOutput:
    """List all worksheets (tabs) in a spreadsheet."""
    if not auth_data.get("access_token"):
        return ListWorksheetsOutput(success=False, error="Missing or empty OAuth access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}",
                headers=headers,
                params={"fields": "sheets.properties"},
            )
        if response.status_code != 200:
            return ListWorksheetsOutput(success=False, error=_format_http_error(response))
        data = response.json()
    except httpx.TimeoutException:
        return ListWorksheetsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListWorksheetsOutput(success=False, error=f"Call failed: {exc}")

    sheets = data.get("sheets", []) or []
    worksheets: list[WorksheetSummary] = []
    for sheet in sheets:
        props = sheet.get("properties", {}) or {}
        grid = props.get("gridProperties") or {}
        worksheets.append(
            WorksheetSummary(
                sheet_id=props.get("sheetId"),
                title=props.get("title"),
                index=props.get("index"),
                sheet_type=props.get("sheetType"),
                row_count=grid.get("rowCount"),
                column_count=grid.get("columnCount"),
            )
        )
    return ListWorksheetsOutput(
        success=True,
        worksheets=worksheets,
        count=len(worksheets),
    )


@tool(args_schema=AddWorksheetInput)
@serialize_pydantic_return
async def add_worksheet(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    title: str,
    headers: list[str] | None = None,
) -> AddWorksheetOutput:
    """Add a new worksheet (tab) to an existing spreadsheet."""
    if not auth_data.get("access_token"):
        return AddWorksheetOutput(success=False, error="Missing or empty OAuth access token.")
    request_headers = _get_auth_headers(auth_type, auth_data)
    body = {"requests": [{"addSheet": {"properties": {"title": title}}}]}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}:batchUpdate",
                headers=request_headers,
                json=body,
            )
            if response.status_code != 200:
                return AddWorksheetOutput(success=False, error=_format_http_error(response))
            data = response.json()
            replies = data.get("replies", []) or []
            add_props = (
                (replies[0].get("addSheet", {}).get("properties") or {})
                if replies
                else {}
            )
            sheet_id = add_props.get("sheetId")
            if headers and sheet_id is not None:
                append_range = _encode_range(title)
                append_url = (
                    f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}"
                    f"/values/{append_range}:append"
                    "?valueInputOption=USER_ENTERED"
                )
                append_resp = await client.post(
                    append_url,
                    headers=request_headers,
                    json={"values": [headers]},
                )
                if append_resp.status_code not in (200, 201):
                    return AddWorksheetOutput(
                        success=False,
                        error=_format_http_error(append_resp),
                    )
    except httpx.TimeoutException:
        return AddWorksheetOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddWorksheetOutput(success=False, error=f"Call failed: {exc}")

    return AddWorksheetOutput(
        success=True,
        sheet_id=sheet_id,
        title=add_props.get("title") or title,
        index=add_props.get("index"),
    )


@tool(args_schema=DeleteWorksheetInput)
@serialize_pydantic_return
async def delete_worksheet(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    worksheet_id: int,
) -> DeleteWorksheetOutput:
    """Delete a worksheet (tab) by its numeric sheet ID."""
    if not auth_data.get("access_token"):
        return DeleteWorksheetOutput(success=False, error="Missing or empty OAuth access token.")
    request_headers = _get_auth_headers(auth_type, auth_data)
    body = {"requests": [{"deleteSheet": {"sheetId": worksheet_id}}]}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}:batchUpdate",
                headers=request_headers,
                json=body,
            )
        if response.status_code != 200:
            return DeleteWorksheetOutput(success=False, error=_format_http_error(response))
    except httpx.TimeoutException:
        return DeleteWorksheetOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteWorksheetOutput(success=False, error=f"Call failed: {exc}")

    return DeleteWorksheetOutput(
        success=True,
        spreadsheet_id=spreadsheet_id,
        deleted_sheet_id=worksheet_id,
    )


@tool(args_schema=ReadRowsInput)
@serialize_pydantic_return
async def read_rows(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    sheet_name: str,
    range: str | None = None,
    has_headers: bool = True,
) -> ReadRowsOutput:
    """Read rows from a worksheet. Returns objects keyed by header when has_headers is True."""
    if not auth_data.get("access_token"):
        return ReadRowsOutput(success=False, error="Missing or empty OAuth access token.")
    request_headers = _get_auth_headers(auth_type, auth_data)
    sub = range
    encoded = _encode_range(sheet_name, sub)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}/values/{encoded}",
                headers=request_headers,
            )
        if response.status_code != 200:
            return ReadRowsOutput(success=False, error=_format_http_error(response))
        data = response.json()
    except httpx.TimeoutException:
        return ReadRowsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ReadRowsOutput(success=False, error=f"Call failed: {exc}")

    values = data.get("values") or []
    if not values:
        return ReadRowsOutput(success=True, rows=[], row_count=0, headers=[])
    if has_headers:
        headers_row = [str(v) for v in values[0]]
        data_rows = values[1:]
        rows_as_objects = _rows_to_objects(headers_row, data_rows)
        return ReadRowsOutput(
            success=True,
            headers=headers_row,
            rows=rows_as_objects,
            row_count=len(rows_as_objects),
        )
    return ReadRowsOutput(success=True, rows=values, row_count=len(values))


@tool(args_schema=GetValuesInRangeInput)
@serialize_pydantic_return
async def get_values_in_range(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    sheet_name: str,
    range: str | None = None,
) -> GetValuesInRangeOutput:
    """Get raw cell values from a worksheet range, returned as a list-of-lists."""
    if not auth_data.get("access_token"):
        return GetValuesInRangeOutput(success=False, error="Missing or empty OAuth access token.")
    request_headers = _get_auth_headers(auth_type, auth_data)
    encoded = _encode_range(sheet_name, range)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}/values/{encoded}",
                headers=request_headers,
            )
        if response.status_code != 200:
            return GetValuesInRangeOutput(success=False, error=_format_http_error(response))
        data = response.json()
    except httpx.TimeoutException:
        return GetValuesInRangeOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetValuesInRangeOutput(success=False, error=f"Call failed: {exc}")

    values = data.get("values") or []
    return GetValuesInRangeOutput(
        success=True,
        range=data.get("range"),
        values=values,
        row_count=len(values),
    )


@tool(args_schema=FindRowsInput)
@serialize_pydantic_return
async def find_rows(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    sheet_name: str,
    column: str,
    search_value: str,
    match_type: str = "contains",
) -> FindRowsOutput:
    """Search a worksheet for rows matching a value in a specific column."""
    if not auth_data.get("access_token"):
        return FindRowsOutput(success=False, error="Missing or empty OAuth access token.")
    request_headers = _get_auth_headers(auth_type, auth_data)
    encoded = _encode_range(sheet_name)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}/values/{encoded}",
                headers=request_headers,
            )
        if response.status_code != 200:
            return FindRowsOutput(success=False, error=_format_http_error(response))
        data = response.json()
    except httpx.TimeoutException:
        return FindRowsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindRowsOutput(success=False, error=f"Call failed: {exc}")

    values = data.get("values") or []
    if not values:
        return FindRowsOutput(success=True, matches=[], match_count=0)

    headers_row = [str(v) for v in values[0]]
    data_rows = values[1:]

    col_index = -1
    column_lower = column.lower() if column else ""
    for idx, header in enumerate(headers_row):
        if header.lower() == column_lower:
            col_index = idx
            break
    if col_index < 0 and column and column.upper().isalpha():
        running = 0
        for ch in column.upper():
            running = running * 26 + (ord(ch) - 64)
        col_index = running - 1
    if col_index < 0:
        return FindRowsOutput(
            success=False,
            error=(
                f"Column '{column}' not found. Available headers: "
                f"{', '.join(headers_row)}"
            ),
        )

    needle = (search_value or "").lower()
    col_header = headers_row[col_index] if col_index < len(headers_row) else f"col_{col_index}"
    matches: list[dict[str, Any]] = []
    for row_idx, row in enumerate(data_rows):
        cell = str(row[col_index]) if col_index < len(row) else ""
        cell_lower = cell.lower()
        if match_type == "exact":
            hit = cell_lower == needle
        elif match_type == "starts_with":
            hit = cell_lower.startswith(needle)
        else:
            hit = needle in cell_lower
        if hit:
            obj: dict[str, Any] = {
                "_row": row_idx + 2,
                col_header: cell,
            }
            for i, header in enumerate(headers_row):
                key = header if header else f"col_{i}"
                obj[key] = row[i] if i < len(row) else None
            matches.append(obj)

    return FindRowsOutput(success=True, matches=matches, match_count=len(matches))


@tool(args_schema=AddRowsInput)
@serialize_pydantic_return
async def add_rows(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    sheet_name: str,
    rows: list[Any],
    has_headers: bool = True,
) -> AddRowsOutput:
    """Append one or more rows to a worksheet."""
    if not auth_data.get("access_token"):
        return AddRowsOutput(success=False, error="Missing or empty OAuth access token.")
    request_headers = _get_auth_headers(auth_type, auth_data)

    parsed_rows: list[Any] = rows
    if isinstance(parsed_rows, str):
        try:
            parsed_rows = json.loads(parsed_rows)
        except json.JSONDecodeError as exc:
            return AddRowsOutput(success=False, error=f"rows must be valid JSON: {exc}")
    if not isinstance(parsed_rows, list):
        parsed_rows = [parsed_rows]

    needs_headers = any(isinstance(r, dict) for r in parsed_rows)
    headers_row: list[str] = []
    if needs_headers and has_headers:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                encoded = _encode_range(sheet_name, "1:1")
                header_resp = await client.get(
                    f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}/values/{encoded}",
                    headers=request_headers,
                )
            if header_resp.status_code != 200:
                return AddRowsOutput(success=False, error=_format_http_error(header_resp))
            header_values = header_resp.json().get("values") or []
            if not header_values:
                return AddRowsOutput(
                    success=False,
                    error="No headers found in row 1. Add headers or pass rows as arrays.",
                )
            headers_row = [str(v) for v in header_values[0]]
        except httpx.TimeoutException:
            return AddRowsOutput(success=False, error="Request timed out.")
        except Exception as exc:
            return AddRowsOutput(success=False, error=f"Call failed: {exc}")

    row_arrays: list[list[Any]] = []
    for row in parsed_rows:
        if isinstance(row, list):
            row_arrays.append(row)
        elif isinstance(row, dict):
            if not headers_row:
                return AddRowsOutput(
                    success=False,
                    error="Cannot map object rows without headers. Set has_headers=True.",
                )
            row_arrays.append([row.get(header, "") for header in headers_row])
        else:
            row_arrays.append([row])

    encoded = _encode_range(sheet_name)
    url = (
        f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}"
        f"/values/{encoded}:append"
        "?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                url,
                headers=request_headers,
                json={"values": row_arrays},
            )
        if response.status_code not in (200, 201):
            return AddRowsOutput(success=False, error=_format_http_error(response))
        data = response.json()
    except httpx.TimeoutException:
        return AddRowsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddRowsOutput(success=False, error=f"Call failed: {exc}")

    updates = data.get("updates") or {}
    return AddRowsOutput(
        success=True,
        rows_added=len(row_arrays),
        updated_range=updates.get("updatedRange"),
        updated_rows=updates.get("updatedRows"),
        updated_columns=updates.get("updatedColumns"),
        updated_cells=updates.get("updatedCells"),
    )


@tool(args_schema=UpdateRowInput)
@serialize_pydantic_return
async def update_row(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    sheet_name: str,
    row: int,
    values: list[Any],
) -> UpdateRowOutput:
    """Overwrite a specific row with a positional list of values."""
    if not auth_data.get("access_token"):
        return UpdateRowOutput(success=False, error="Missing or empty OAuth access token.")
    request_headers = _get_auth_headers(auth_type, auth_data)
    if row < 1:
        return UpdateRowOutput(success=False, error="row must be >= 1.")
    encoded = _encode_range(sheet_name, f"{_row_index(row)}:{_row_index(row)}")
    url = (
        f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}"
        f"/values/{encoded}"
        "?valueInputOption=USER_ENTERED"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                url,
                headers=request_headers,
                json={"values": [values]},
            )
        if response.status_code != 200:
            return UpdateRowOutput(success=False, error=_format_http_error(response))
        data = response.json()
    except httpx.TimeoutException:
        return UpdateRowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateRowOutput(success=False, error=f"Call failed: {exc}")

    return UpdateRowOutput(
        success=True,
        updated_range=data.get("updatedRange"),
        updated_rows=data.get("updatedRows"),
        updated_columns=data.get("updatedColumns"),
        updated_cells=data.get("updatedCells"),
    )


@tool(args_schema=UpdateCellInput)
@serialize_pydantic_return
async def update_cell(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    sheet_name: str,
    cell: str,
    value: str,
) -> UpdateCellOutput:
    """Update a single cell by A1 notation."""
    if not auth_data.get("access_token"):
        return UpdateCellOutput(success=False, error="Missing or empty OAuth access token.")
    request_headers = _get_auth_headers(auth_type, auth_data)
    encoded = _encode_range(sheet_name, f"{cell}:{cell}")
    url = (
        f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}"
        f"/values/{encoded}"
        "?valueInputOption=USER_ENTERED"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                url,
                headers=request_headers,
                json={"values": [[value]]},
            )
        if response.status_code != 200:
            return UpdateCellOutput(success=False, error=_format_http_error(response))
        data = response.json()
    except httpx.TimeoutException:
        return UpdateCellOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateCellOutput(success=False, error=f"Call failed: {exc}")

    return UpdateCellOutput(
        success=True,
        updated_range=data.get("updatedRange"),
        updated_cells=data.get("updatedCells"),
    )


@tool(args_schema=ClearRowsInput)
@serialize_pydantic_return
async def clear_rows(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    sheet_name: str,
    start_index: int,
    end_index: int | None = None,
) -> ClearRowsOutput:
    """Clear values from a row or range of rows (the rows remain, but become blank)."""
    if not auth_data.get("access_token"):
        return ClearRowsOutput(success=False, error="Missing or empty OAuth access token.")
    request_headers = _get_auth_headers(auth_type, auth_data)
    if start_index < 1:
        return ClearRowsOutput(success=False, error="start_index must be >= 1.")
    last = end_index if end_index is not None else start_index
    if last < start_index:
        return ClearRowsOutput(success=False, error="end_index must be >= start_index.")
    encoded = _encode_range(sheet_name, f"{start_index}:{last}")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}/values/{encoded}:clear",
                headers=request_headers,
                json={},
            )
        if response.status_code != 200:
            return ClearRowsOutput(success=False, error=_format_http_error(response))
        data = response.json()
    except httpx.TimeoutException:
        return ClearRowsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ClearRowsOutput(success=False, error=f"Call failed: {exc}")

    return ClearRowsOutput(
        success=True,
        spreadsheet_id=data.get("spreadsheetId") or spreadsheet_id,
        cleared_range=data.get("clearedRange"),
    )


@tool(args_schema=DeleteRowsInput)
@serialize_pydantic_return
async def delete_rows(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    worksheet_id: int,
    start_index: int,
    end_index: int | None = None,
) -> DeleteRowsOutput:
    """Delete rows from a worksheet via batchUpdate's deleteDimension."""
    if not auth_data.get("access_token"):
        return DeleteRowsOutput(success=False, error="Missing or empty OAuth access token.")
    request_headers = _get_auth_headers(auth_type, auth_data)
    if start_index < 1:
        return DeleteRowsOutput(success=False, error="start_index must be >= 1.")
    # API ranges are 0-indexed and end-exclusive.
    api_start = start_index - 1
    api_end = end_index if end_index is not None else start_index
    if api_end < start_index:
        return DeleteRowsOutput(success=False, error="end_index must be >= start_index.")
    body = {
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": worksheet_id,
                        "dimension": "ROWS",
                        "startIndex": api_start,
                        "endIndex": api_end,
                    },
                },
            },
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_SHEETS_BASE}/spreadsheets/{spreadsheet_id}:batchUpdate",
                headers=request_headers,
                json=body,
            )
        if response.status_code != 200:
            return DeleteRowsOutput(success=False, error=_format_http_error(response))
    except httpx.TimeoutException:
        return DeleteRowsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteRowsOutput(success=False, error=f"Call failed: {exc}")

    return DeleteRowsOutput(
        success=True,
        spreadsheet_id=spreadsheet_id,
        deleted_count=max(0, api_end - api_start),
    )


# `_index_to_column_letter` is kept as a public-ish helper for future actions.
_ = _index_to_column_letter
