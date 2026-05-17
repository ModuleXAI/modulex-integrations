"""Microsoft Excel LangChain @tool functions."""
from __future__ import annotations

import re
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.microsoft_excel.outputs import (
    AddAWorksheetTablerowOutput,
    AddRowOutput,
    FindRowOutput,
    FolderOption,
    GetColumnsOutput,
    GetSpreadsheetOutput,
    GetTableRowsOutput,
    ListFolderIdOptionsOutput,
    TableRow,
    UpdateCellOutput,
    UpdateWorksheetTablerowOutput,
)

__all__ = [
    "add_a_worksheet_tablerow",
    "add_row",
    "find_row",
    "get_columns",
    "get_spreadsheet",
    "get_table_rows",
    "list_folder_id_options",
    "update_cell",
    "update_worksheet_tablerow",
]

_BASE_URL = "https://graph.microsoft.com/v1.0"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Microsoft Graph API based on auth_type/auth_data."""
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _column_letter(index: int) -> str:
    """Convert a 1-based column index into an A1-style column letter."""
    letter = ""
    while index > 0:
        index, mod = divmod(index - 1, 26)
        letter = chr(65 + mod) + letter
    return letter


# --- Input schemas --------------------------------------------------------


class AddAWorksheetTablerowInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access token"
    )
    sheet_id: str = Field(
        description="Drive item ID of the workbook in OneDrive"
    )
    values: list[list[Any]] = Field(
        description=(
            "Two-dimensional array of unformatted row values, e.g. "
            "[[1, 2, 3], [4, 5, 6]]"
        )
    )
    table_id: str | None = Field(
        default=None,
        description="ID of the workbook table (use either table_id or table_name)",
    )
    table_name: str | None = Field(
        default=None,
        description="Name of the workbook table (used when table_id is unavailable)",
    )


class AddRowInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    sheet_id: str = Field(description="Drive item ID of the workbook in OneDrive")
    worksheet: str = Field(description="Name of the worksheet to append to")
    values: list[Any] = Field(
        description="Array of cell values for the new row, e.g. [1, 2, 3]"
    )


class FindRowInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    sheet_id: str = Field(description="Drive item ID of the workbook in OneDrive")
    worksheet: str = Field(description="Name of the worksheet to search")
    column: str = Field(description="Column letter to search, e.g. 'A'")
    value: str = Field(description="Value to search for")


class GetColumnsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    sheet_id: str = Field(description="Drive item ID of the workbook in OneDrive")
    worksheet: str = Field(description="Name of the worksheet to read")
    columns: list[str] = Field(
        description="Array of column letters to retrieve, e.g. ['A', 'C']"
    )


class GetSpreadsheetInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    sheet_id: str = Field(description="Drive item ID of the workbook in OneDrive")
    worksheet: str = Field(description="Name of the worksheet to read")
    range: str | None = Field(
        default=None,
        description=(
            "Range within the worksheet, e.g. 'A1:C4'. If omitted, the entire "
            "used range is returned."
        ),
    )


class GetTableRowsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    sheet_id: str = Field(description="Drive item ID of the workbook in OneDrive")
    table_id: str = Field(description="ID of the workbook table")


class ListFolderIdOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    max_pages: int = Field(
        default=50,
        description="Maximum number of batch pages to fetch (1-500). Default 50.",
        ge=1,
        le=500,
    )


class UpdateCellInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    sheet_id: str = Field(description="Drive item ID of the workbook in OneDrive")
    worksheet: str = Field(description="Name of the worksheet containing the cell")
    cell: str = Field(description="Cell address to update, e.g. 'A1'")
    value: str = Field(description="Value to write to the cell")


class UpdateWorksheetTablerowInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    sheet_id: str = Field(description="Drive item ID of the workbook in OneDrive")
    table_id: str = Field(description="ID of the workbook table")
    row_id: int = Field(description="Zero-based index of the row to update")
    values: list[Any] = Field(
        description="Array of cell values for the updated row, e.g. [1, 2, 3]"
    )


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AddAWorksheetTablerowInput)
@serialize_pydantic_return
async def add_a_worksheet_tablerow(
    auth_type: str,
    auth_data: dict[str, Any],
    sheet_id: str,
    values: list[list[Any]],
    table_id: str | None = None,
    table_name: str | None = None,
) -> AddAWorksheetTablerowOutput:
    """Adds rows to the end of a specific Excel table."""
    if not auth_data.get("access_token"):
        return AddAWorksheetTablerowOutput(
            success=False, error="Missing or empty access_token in auth_data."
        )
    table_ref = table_id or table_name
    if not table_ref:
        return AddAWorksheetTablerowOutput(
            success=False,
            error="Either table_id or table_name must be provided.",
        )
    url = (
        f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/tables/"
        f"{table_ref}/rows/add"
    )
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json={"values": values})
        if response.status_code not in (200, 201):
            return AddAWorksheetTablerowOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return AddAWorksheetTablerowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddAWorksheetTablerowOutput(
            success=False, error=f"Call failed: {exc}"
        )
    return AddAWorksheetTablerowOutput(
        success=True,
        row=TableRow(
            index=data.get("index"),
            values=data.get("values") or [],
        ),
    )


@tool(args_schema=AddRowInput)
@serialize_pydantic_return
async def add_row(
    auth_type: str,
    auth_data: dict[str, Any],
    sheet_id: str,
    worksheet: str,
    values: list[Any],
) -> AddRowOutput:
    """Insert a new row at the end of the used range of an Excel worksheet."""
    if not auth_data.get("access_token"):
        return AddRowOutput(
            success=False, error="Missing or empty access_token in auth_data."
        )
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # Step 1: find the used range to determine the next row.
            used_url = (
                f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/worksheets/"
                f"{worksheet}/usedRange"
            )
            used_resp = await client.get(used_url, headers=headers)
            if used_resp.status_code != 200:
                return AddRowOutput(
                    success=False,
                    error=(
                        f"usedRange error ({used_resp.status_code}): "
                        f"{used_resp.text}"
                    ),
                )
            used = used_resp.json()
            address = used.get("address", "")
            column_count = int(used.get("columnCount") or len(values))
            match = re.match(r"^(.+!)?([A-Z]+)(\d+):([A-Z]+)(\d+)$", address)
            if not match:
                return AddRowOutput(
                    success=False,
                    error=f"Could not parse usedRange address: {address!r}",
                )
            next_row = int(match.group(5)) + 1

            # Pad / truncate the values to the worksheet width.
            row_values = list(values)
            if len(row_values) < column_count:
                row_values = row_values + [None] * (column_count - len(row_values))
            col_end = _column_letter(len(row_values))
            new_range = f"A{next_row}:{col_end}{next_row}"

            # Step 2: insert the new range shifting cells down.
            insert_url = (
                f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/worksheets/"
                f"{worksheet}/range(address='{new_range}')/insert"
            )
            insert_resp = await client.post(
                insert_url, headers=headers, json={"shift": "Down"}
            )
            if insert_resp.status_code not in (200, 201):
                return AddRowOutput(
                    success=False,
                    error=(
                        f"insert error ({insert_resp.status_code}): "
                        f"{insert_resp.text}"
                    ),
                )

            # Step 3: write the values into the inserted range.
            update_url = (
                f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/worksheets/"
                f"{worksheet}/range(address='{new_range}')"
            )
            update_resp = await client.patch(
                update_url, headers=headers, json={"values": [row_values]}
            )
        if update_resp.status_code != 200:
            return AddRowOutput(
                success=False,
                error=f"update error ({update_resp.status_code}): {update_resp.text}",
            )
        data = update_resp.json()
    except httpx.TimeoutException:
        return AddRowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddRowOutput(success=False, error=f"Call failed: {exc}")
    return AddRowOutput(
        success=True,
        address=data.get("address"),
        values=data.get("values") or [],
    )


@tool(args_schema=FindRowInput)
@serialize_pydantic_return
async def find_row(
    auth_type: str,
    auth_data: dict[str, Any],
    sheet_id: str,
    worksheet: str,
    column: str,
    value: str,
) -> FindRowOutput:
    """Find the first row in a worksheet where the given column equals the given value."""
    if not auth_data.get("access_token"):
        return FindRowOutput(
            success=False, error="Missing or empty access_token in auth_data."
        )
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            used_url = (
                f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/worksheets/"
                f"{worksheet}/usedRange"
            )
            used_resp = await client.get(used_url, headers=headers)
            if used_resp.status_code != 200:
                return FindRowOutput(
                    success=False,
                    error=(
                        f"usedRange error ({used_resp.status_code}): "
                        f"{used_resp.text}"
                    ),
                )
            used = used_resp.json()
            row_count = int(used.get("rowCount") or 0)
            used_address = used.get("address", "")
            tail_match = re.search(r":([A-Z]+)\d+$", used_address)
            last_column = tail_match.group(1) if tail_match else column

            range_address = f"{column}1:{column}{row_count}"
            col_url = (
                f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/worksheets/"
                f"{worksheet}/range(address='{range_address}')"
            )
            col_resp = await client.get(col_url, headers=headers)
            if col_resp.status_code != 200:
                return FindRowOutput(
                    success=False,
                    error=(
                        f"column read error ({col_resp.status_code}): "
                        f"{col_resp.text}"
                    ),
                )
            col_data = col_resp.json()
            col_rows = col_data.get("values") or []
            column_values: list[Any] = [
                row[0] if row else None for row in col_rows
            ]

            index = -1
            for i, cell in enumerate(column_values):
                if cell == value:
                    index = i
                    break
            if index == -1:
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    numeric = None
                if numeric is not None:
                    for i, cell in enumerate(column_values):
                        if isinstance(cell, (int, float)) and cell == numeric:
                            index = i
                            break

            if index == -1:
                return FindRowOutput(
                    success=True,
                    found=False,
                    column_values=column_values,
                )

            row_number = index + 1
            row_range = f"A{row_number}:{last_column}{row_number}"
            row_url = (
                f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/worksheets/"
                f"{worksheet}/range(address='{row_range}')"
            )
            row_resp = await client.get(row_url, headers=headers)
        if row_resp.status_code != 200:
            return FindRowOutput(
                success=False,
                error=f"row read error ({row_resp.status_code}): {row_resp.text}",
            )
        row_data = row_resp.json()
    except httpx.TimeoutException:
        return FindRowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindRowOutput(success=False, error=f"Call failed: {exc}")
    return FindRowOutput(
        success=True,
        found=True,
        row_number=row_number,
        address=row_data.get("address"),
        values=row_data.get("values") or [],
        column_values=column_values,
    )


@tool(args_schema=GetColumnsInput)
@serialize_pydantic_return
async def get_columns(
    auth_type: str,
    auth_data: dict[str, Any],
    sheet_id: str,
    worksheet: str,
    columns: list[str],
) -> GetColumnsOutput:
    """Get the values of the requested columns in an Excel worksheet."""
    if not auth_data.get("access_token"):
        return GetColumnsOutput(
            success=False, error="Missing or empty access_token in auth_data."
        )
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            used_url = (
                f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/worksheets/"
                f"{worksheet}/usedRange"
            )
            used_resp = await client.get(used_url, headers=headers)
            if used_resp.status_code != 200:
                return GetColumnsOutput(
                    success=False,
                    error=(
                        f"usedRange error ({used_resp.status_code}): "
                        f"{used_resp.text}"
                    ),
                )
            used = used_resp.json()
            row_count = int(used.get("rowCount") or 0)
            values: dict[str, list[Any]] = {}
            for column in columns:
                rng = f"{column}1:{column}{row_count}"
                col_url = (
                    f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/"
                    f"worksheets/{worksheet}/range(address='{rng}')"
                )
                col_resp = await client.get(col_url, headers=headers)
                if col_resp.status_code != 200:
                    return GetColumnsOutput(
                        success=False,
                        error=(
                            f"column {column} error ({col_resp.status_code}): "
                            f"{col_resp.text}"
                        ),
                    )
                col_data = col_resp.json()
                values[column] = [
                    row[0] if row else None for row in (col_data.get("values") or [])
                ]
    except httpx.TimeoutException:
        return GetColumnsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetColumnsOutput(success=False, error=f"Call failed: {exc}")
    return GetColumnsOutput(success=True, values=values)


@tool(args_schema=GetSpreadsheetInput)
@serialize_pydantic_return
async def get_spreadsheet(
    auth_type: str,
    auth_data: dict[str, Any],
    sheet_id: str,
    worksheet: str,
    range: str | None = None,
) -> GetSpreadsheetOutput:
    """Get the values of a worksheet range (or the entire used range)."""
    if not auth_data.get("access_token"):
        return GetSpreadsheetOutput(
            success=False, error="Missing or empty access_token in auth_data."
        )
    headers = _get_auth_headers(auth_type, auth_data)
    if range:
        url = (
            f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/worksheets/"
            f"{worksheet}/range(address='{range}')"
        )
    else:
        url = (
            f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/worksheets/"
            f"{worksheet}/usedRange"
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return GetSpreadsheetOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetSpreadsheetOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSpreadsheetOutput(success=False, error=f"Call failed: {exc}")
    return GetSpreadsheetOutput(
        success=True,
        address=data.get("address"),
        row_count=data.get("rowCount"),
        column_count=data.get("columnCount"),
        values=data.get("values") or [],
    )


@tool(args_schema=GetTableRowsInput)
@serialize_pydantic_return
async def get_table_rows(
    auth_type: str,
    auth_data: dict[str, Any],
    sheet_id: str,
    table_id: str,
) -> GetTableRowsOutput:
    """Retrieve rows from a specified table in an Excel worksheet."""
    if not auth_data.get("access_token"):
        return GetTableRowsOutput(
            success=False, error="Missing or empty access_token in auth_data."
        )
    headers = _get_auth_headers(auth_type, auth_data)
    url = (
        f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/tables/{table_id}/rows"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return GetTableRowsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetTableRowsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetTableRowsOutput(success=False, error=f"Call failed: {exc}")
    rows = [
        TableRow(index=r.get("index"), values=r.get("values") or [])
        for r in (data.get("value") or [])
    ]
    return GetTableRowsOutput(success=True, rows=rows)


@tool(args_schema=ListFolderIdOptionsInput)
@serialize_pydantic_return
async def list_folder_id_options(
    auth_type: str,
    auth_data: dict[str, Any],
    max_pages: int = 50,
) -> ListFolderIdOptionsOutput:
    """List OneDrive folders accessible to the authenticated user."""
    if not auth_data.get("access_token"):
        return ListFolderIdOptionsOutput(
            success=False, error="Missing or empty access_token in auth_data."
        )
    headers = _get_auth_headers(auth_type, auth_data)
    options: list[FolderOption] = []
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # BFS over folder tree using the $batch endpoint, matching the
            # pipedream component's batched-fanout behaviour.
            stack: list[tuple[str | None, str]] = [(None, "")]
            history: list[tuple[str, str]] = []
            batch_limit = 20
            pages_seen = 0

            while stack and pages_seen < max_pages:
                pages_seen += 1
                current_batch: list[dict[str, Any]] = []
                while stack and len(current_batch) < batch_limit:
                    folder_id, prefix = stack.pop(0)
                    request_id = folder_id or "root"
                    history.append((request_id, prefix))
                    if folder_id:
                        url = (
                            f"/me/drive/items/{folder_id}/children?"
                            "$filter=folder ne null"
                        )
                    else:
                        url = "/me/drive/root/children?$filter=folder ne null"
                    current_batch.append({
                        "id": request_id,
                        "method": "GET",
                        "url": url,
                    })

                batch_resp = await client.post(
                    f"{_BASE_URL}/$batch",
                    headers=headers,
                    json={"requests": current_batch},
                )
                if batch_resp.status_code != 200:
                    return ListFolderIdOptionsOutput(
                        success=False,
                        error=(
                            f"batch error ({batch_resp.status_code}): "
                            f"{batch_resp.text}"
                        ),
                    )
                batch_body = batch_resp.json()
                for entry in batch_body.get("responses") or []:
                    if entry.get("status") != 200:
                        continue
                    body = entry.get("body") or {}
                    for item in body.get("value") or []:
                        item_id = item.get("id")
                        name = item.get("name") or ""
                        folder = item.get("folder") or {}
                        child_count = int(folder.get("childCount") or 0)
                        parent = (item.get("parentReference") or {}).get("id")
                        prefix = next(
                            (p for rid, p in history if rid == parent), ""
                        )
                        current_label = f"{prefix}{name}"
                        if item_id:
                            options.append(
                                FolderOption(value=item_id, label=current_label)
                            )
                        if child_count and item_id:
                            stack.append((item_id, f"{current_label}/"))
    except httpx.TimeoutException:
        return ListFolderIdOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFolderIdOptionsOutput(success=False, error=f"Call failed: {exc}")
    return ListFolderIdOptionsOutput(success=True, options=options)


@tool(args_schema=UpdateCellInput)
@serialize_pydantic_return
async def update_cell(
    auth_type: str,
    auth_data: dict[str, Any],
    sheet_id: str,
    worksheet: str,
    cell: str,
    value: str,
) -> UpdateCellOutput:
    """Update the value of a specific cell in an Excel worksheet."""
    if not auth_data.get("access_token"):
        return UpdateCellOutput(
            success=False, error="Missing or empty access_token in auth_data."
        )
    headers = _get_auth_headers(auth_type, auth_data)
    cell_range = f"{cell}:{cell}"
    url = (
        f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/worksheets/"
        f"{worksheet}/range(address='{cell_range}')"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                url, headers=headers, json={"values": [[value]]}
            )
        if response.status_code != 200:
            return UpdateCellOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateCellOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateCellOutput(success=False, error=f"Call failed: {exc}")
    return UpdateCellOutput(
        success=True,
        address=data.get("address"),
        values=data.get("values") or [],
    )


@tool(args_schema=UpdateWorksheetTablerowInput)
@serialize_pydantic_return
async def update_worksheet_tablerow(
    auth_type: str,
    auth_data: dict[str, Any],
    sheet_id: str,
    table_id: str,
    row_id: int,
    values: list[Any],
) -> UpdateWorksheetTablerowOutput:
    """Update the values of a workbook table row by zero-based index."""
    if not auth_data.get("access_token"):
        return UpdateWorksheetTablerowOutput(
            success=False, error="Missing or empty access_token in auth_data."
        )
    headers = _get_auth_headers(auth_type, auth_data)
    url = (
        f"{_BASE_URL}/me/drive/items/{sheet_id}/workbook/tables/{table_id}/"
        f"rows/ItemAt(index={row_id})"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                url, headers=headers, json={"values": [values]}
            )
        if response.status_code != 200:
            return UpdateWorksheetTablerowOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateWorksheetTablerowOutput(
            success=False, error="Request timed out."
        )
    except Exception as exc:
        return UpdateWorksheetTablerowOutput(
            success=False, error=f"Call failed: {exc}"
        )
    return UpdateWorksheetTablerowOutput(
        success=True,
        row=TableRow(
            index=data.get("index"),
            values=data.get("values") or [],
        ),
    )
