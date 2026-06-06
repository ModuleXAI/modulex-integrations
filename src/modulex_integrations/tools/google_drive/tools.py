"""Google Drive / Docs / Sheets / Slides LangChain ``@tool`` functions.

Pure HTTP across four Google APIs (Drive v3, Docs v1, Sheets v4,
Slides v1). Token-based runtime convention with paired
``oauth2 + bearer_token``.

16 actions. Key shapes preserved verbatim from legacy:

- **`create_text_file`** uses a manual multipart/related upload
  (Google Drive's media-upload pattern). Pre-formats the JSON
  metadata in-line.
- **`update_text_file`** uses the media-upload endpoint with a raw
  body; if ``name`` is given it does a second PATCH to rename.
- **`update_google_doc`** is a 3-step flow: GET doc to find end
  index, build batchUpdate with `deleteContentRange` + `insertText`.
- **`read_google_sheet` / `update_google_sheet`** resolve localized
  sheet names (e.g. `Sayfa1` for Turkish) via `_get_first_sheet_name`
  before composing the A1 range.
- **`format_sheet_*`** convert A1 notation to `GridRange` for the
  Sheets batchUpdate API.

All actions wrap in try/except → unified ``success=False`` envelope.
"""
from __future__ import annotations

import re
import uuid
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_drive.outputs import (
    AddSlideOutput,
    AppendToGoogleDocOutput,
    CreateFolderOutput,
    CreateGoogleDocOutput,
    CreateGoogleSheetOutput,
    CreateGoogleSlidesOutput,
    CreateTextFileOutput,
    FormatSheetCellsOutput,
    FormatSheetTextOutput,
    ReadGoogleDocOutput,
    ReadGoogleSheetOutput,
    ReadGoogleSlidesOutput,
    UpdateGoogleDocOutput,
    UpdateGoogleSheetOutput,
    UpdateSlideContentOutput,
    UpdateTextFileOutput,
)

__all__ = [
    "add_slide",
    "append_to_google_doc",
    "create_folder",
    "create_google_doc",
    "create_google_sheet",
    "create_google_slides",
    "create_text_file",
    "format_sheet_cells",
    "format_sheet_text",
    "read_google_doc",
    "read_google_sheet",
    "read_google_slides",
    "update_google_doc",
    "update_google_sheet",
    "update_slide_content",
    "update_text_file",
]

_DRIVE = "https://www.googleapis.com/drive/v3"
_UPLOAD = "https://www.googleapis.com/upload/drive/v3"
_DOCS = "https://docs.googleapis.com/v1"
_SHEETS = "https://sheets.googleapis.com/v4"
_SLIDES = "https://slides.googleapis.com/v1"
_TIMEOUT = 30.0
_LONG_TIMEOUT = 60.0

_FOLDER_MIME = "application/vnd.google-apps.folder"
_GDOC_MIME = "application/vnd.google-apps.document"
_GSHEET_MIME = "application/vnd.google-apps.spreadsheet"

_TEXT_MIME = {"txt": "text/plain", "md": "text/markdown"}


def _headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if auth_type == "oauth2":
        token = auth_data.get("access_token")
    elif auth_type == "bearer_token":
        token = auth_data.get("token") or auth_data.get("bearer_token")
    else:
        token = auth_data.get("access_token") or auth_data.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _validate(auth_data: dict[str, Any], action: str) -> str | None:
    if not (
        auth_data.get("access_token")
        or auth_data.get("token")
        or auth_data.get("bearer_token")
    ):
        return f"Google access token missing for {action}"
    return None


def _api_err(prefix: str, response: httpx.Response) -> str:
    return f"{prefix}: {response.status_code} - {response.text}"


async def _call(
    method: str,
    url: str,
    auth_type: str,
    auth_data: dict[str, Any],
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    success_codes: tuple[int, ...] = (200,),
    timeout: float = _TIMEOUT,
) -> tuple[bool, str | None, dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method,
                url,
                headers=_headers(auth_type, auth_data),
                json=json_body,
                params=params,
            )
        if response.status_code not in success_codes:
            return False, _api_err("API error", response), {}
        if response.status_code == 204 or not response.content:
            return True, None, {}
        return True, None, response.json() or {}
    except Exception as exc:
        return False, str(exc), {}


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2 or bearer_token)")
    auth_data: dict[str, Any] = Field(description="Auth data with access_token")


class CreateTextFileInput(_AuthFields):
    name: str
    content: str
    parent_folder_id: str | None = None


class UpdateTextFileInput(_AuthFields):
    file_id: str
    content: str
    name: str | None = None


class CreateFolderInput(_AuthFields):
    name: str
    parent_folder_id: str | None = None


class CreateGoogleDocInput(_AuthFields):
    name: str
    content: str = ""
    parent_folder_id: str | None = None


class ReadGoogleDocInput(_AuthFields):
    document_id: str


class UpdateGoogleDocInput(_AuthFields):
    document_id: str
    content: str


class AppendToGoogleDocInput(_AuthFields):
    document_id: str
    content: str


class CreateGoogleSheetInput(_AuthFields):
    name: str
    data: list[list[str]] | None = None
    parent_folder_id: str | None = None


class ReadGoogleSheetInput(_AuthFields):
    spreadsheet_id: str
    range: str = "Sheet1"


class UpdateGoogleSheetInput(_AuthFields):
    spreadsheet_id: str
    range: str
    data: list[list[str]]


class FormatSheetCellsInput(_AuthFields):
    spreadsheet_id: str
    range: str
    background_color: dict[str, float] | None = None
    horizontal_alignment: str | None = None
    vertical_alignment: str | None = None


class FormatSheetTextInput(_AuthFields):
    spreadsheet_id: str
    range: str
    bold: bool | None = None
    italic: bool | None = None
    font_size: int | None = None
    foreground_color: dict[str, float] | None = None


class CreateGoogleSlidesInput(_AuthFields):
    name: str
    parent_folder_id: str | None = None


class ReadGoogleSlidesInput(_AuthFields):
    presentation_id: str


class AddSlideInput(_AuthFields):
    presentation_id: str
    layout: str = "BLANK"
    insertion_index: int | None = None


class UpdateSlideContentInput(_AuthFields):
    presentation_id: str
    slide_id: str
    placeholder_id: str
    text: str


# --- Drive tools -----------------------------------------------------------


@tool(args_schema=CreateTextFileInput)
@serialize_pydantic_return
async def create_text_file(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    content: str,
    parent_folder_id: str | None = None,
) -> CreateTextFileOutput:
    """Create a plain text (.txt) or markdown (.md) file via multipart upload."""
    err = _validate(auth_data, "create_text_file")
    if err:
        return CreateTextFileOutput(success=False, error=err)
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in _TEXT_MIME:
        return CreateTextFileOutput(
            success=False, error="File name must end with .txt or .md"
        )
    mime_type = _TEXT_MIME[ext]

    boundary = "modulex_boundary_12345"
    metadata_json = f'{{"name": "{name}", "mimeType": "{mime_type}"'
    if parent_folder_id:
        metadata_json += f', "parents": ["{parent_folder_id}"]'
    metadata_json += "}"
    body = (
        f"--{boundary}\r\n"
        f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{metadata_json}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {mime_type}\r\n\r\n"
        f"{content}\r\n"
        f"--{boundary}--"
    )

    base_headers = _headers(auth_type, auth_data)
    upload_headers = {
        "Authorization": base_headers["Authorization"],
        "Content-Type": f"multipart/related; boundary={boundary}",
    }
    try:
        async with httpx.AsyncClient(timeout=_LONG_TIMEOUT) as client:
            response = await client.post(
                f"{_UPLOAD}/files",
                headers=upload_headers,
                params={
                    "uploadType": "multipart",
                    "fields": "id,name,mimeType,webViewLink",
                },
                content=body.encode("utf-8"),
            )
        if response.status_code not in (200, 201):
            return CreateTextFileOutput(
                success=False, error=_api_err("Failed to create file", response)
            )
        data = response.json() or {}
    except Exception as exc:
        return CreateTextFileOutput(success=False, error=str(exc))
    return CreateTextFileOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        mime_type=data.get("mimeType"),
        web_view_link=data.get("webViewLink"),
    )


@tool(args_schema=UpdateTextFileInput)
@serialize_pydantic_return
async def update_text_file(
    auth_type: str,
    auth_data: dict[str, Any],
    file_id: str,
    content: str,
    name: str | None = None,
) -> UpdateTextFileOutput:
    """Replace a text file's content; optionally rename in a follow-up PATCH."""
    err = _validate(auth_data, "update_text_file")
    if err:
        return UpdateTextFileOutput(success=False, error=err)
    headers = _headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_LONG_TIMEOUT) as client:
            meta = await client.get(
                f"{_DRIVE}/files/{file_id}",
                headers=headers,
                params={"fields": "mimeType,name"},
            )
            if meta.status_code != 200:
                return UpdateTextFileOutput(
                    success=False,
                    error=f"Failed to get file info: {meta.status_code}",
                )
            mime_type = (meta.json() or {}).get("mimeType", "text/plain")
            upload_headers = {
                "Authorization": headers["Authorization"],
                "Content-Type": mime_type,
            }
            response = await client.patch(
                f"{_UPLOAD}/files/{file_id}",
                headers=upload_headers,
                params={
                    "uploadType": "media",
                    "fields": "id,name,mimeType,webViewLink,modifiedTime",
                },
                content=content.encode("utf-8"),
            )
            if response.status_code != 200:
                return UpdateTextFileOutput(
                    success=False, error=_api_err("Failed to update", response)
                )
            data = response.json() or {}
            if name:
                rename = await client.patch(
                    f"{_DRIVE}/files/{file_id}",
                    headers=headers,
                    json={"name": name},
                )
                # Legacy: rename failures are logged-but-not-fatal; preserved.
                _ = rename
    except Exception as exc:
        return UpdateTextFileOutput(success=False, error=str(exc))
    return UpdateTextFileOutput(
        success=True,
        id=data.get("id"),
        name=name or data.get("name"),
        mime_type=data.get("mimeType"),
        modified_time=data.get("modifiedTime"),
        web_view_link=data.get("webViewLink"),
    )


@tool(args_schema=CreateFolderInput)
@serialize_pydantic_return
async def create_folder(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    parent_folder_id: str | None = None,
) -> CreateFolderOutput:
    """Create a folder."""
    err = _validate(auth_data, "create_folder")
    if err:
        return CreateFolderOutput(success=False, error=err)
    body: dict[str, Any] = {"name": name, "mimeType": _FOLDER_MIME}
    if parent_folder_id:
        body["parents"] = [parent_folder_id]
    ok, e, data = await _call(
        "POST",
        f"{_DRIVE}/files",
        auth_type,
        auth_data,
        json_body=body,
        params={"fields": "id,name,mimeType,webViewLink"},
        success_codes=(200, 201),
    )
    if not ok:
        return CreateFolderOutput(success=False, error=e)
    return CreateFolderOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        web_view_link=data.get("webViewLink"),
    )


# --- Docs tools -----------------------------------------------------------


def _doc_end_index(doc_data: dict[str, Any]) -> int:
    end = 1
    for element in (doc_data.get("body") or {}).get("content") or []:
        if "endIndex" in element:
            end = max(end, element["endIndex"])
    return end


@tool(args_schema=CreateGoogleDocInput)
@serialize_pydantic_return
async def create_google_doc(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    content: str = "",
    parent_folder_id: str | None = None,
) -> CreateGoogleDocOutput:
    """Create a Google Doc (Drive create + optional Docs batchUpdate)."""
    err = _validate(auth_data, "create_google_doc")
    if err:
        return CreateGoogleDocOutput(success=False, error=err)
    body: dict[str, Any] = {"name": name, "mimeType": _GDOC_MIME}
    if parent_folder_id:
        body["parents"] = [parent_folder_id]
    ok, e, doc = await _call(
        "POST",
        f"{_DRIVE}/files",
        auth_type,
        auth_data,
        json_body=body,
        params={"fields": "id,name,webViewLink"},
        success_codes=(200, 201),
    )
    if not ok:
        return CreateGoogleDocOutput(success=False, error=e)
    doc_id = doc.get("id")
    if content and doc_id:
        await _call(
            "POST",
            f"{_DOCS}/documents/{doc_id}:batchUpdate",
            auth_type,
            auth_data,
            json_body={
                "requests": [
                    {"insertText": {"location": {"index": 1}, "text": content}}
                ]
            },
            timeout=_LONG_TIMEOUT,
        )
    return CreateGoogleDocOutput(
        success=True,
        id=doc_id,
        name=doc.get("name"),
        web_view_link=doc.get("webViewLink"),
    )


@tool(args_schema=ReadGoogleDocInput)
@serialize_pydantic_return
async def read_google_doc(
    auth_type: str, auth_data: dict[str, Any], document_id: str
) -> ReadGoogleDocOutput:
    """Read a Google Doc's full text content."""
    err = _validate(auth_data, "read_google_doc")
    if err:
        return ReadGoogleDocOutput(success=False, error=err)
    ok, e, doc = await _call(
        "GET",
        f"{_DOCS}/documents/{document_id}",
        auth_type,
        auth_data,
        timeout=_LONG_TIMEOUT,
    )
    if not ok:
        return ReadGoogleDocOutput(success=False, error=e)
    parts: list[str] = []
    for element in (doc.get("body") or {}).get("content") or []:
        for elem in (element.get("paragraph") or {}).get("elements") or []:
            tr = elem.get("textRun")
            if tr:
                parts.append(tr.get("content", ""))
    return ReadGoogleDocOutput(
        success=True,
        id=document_id,
        title=doc.get("title"),
        content="".join(parts),
        revision_id=doc.get("revisionId"),
    )


@tool(args_schema=UpdateGoogleDocInput)
@serialize_pydantic_return
async def update_google_doc(
    auth_type: str,
    auth_data: dict[str, Any],
    document_id: str,
    content: str,
) -> UpdateGoogleDocOutput:
    """Replace all content in a Doc (read end-index, delete, insert)."""
    err = _validate(auth_data, "update_google_doc")
    if err:
        return UpdateGoogleDocOutput(success=False, error=err)
    ok, e, doc = await _call(
        "GET", f"{_DOCS}/documents/{document_id}", auth_type, auth_data
    )
    if not ok:
        return UpdateGoogleDocOutput(success=False, error=e)
    end_index = _doc_end_index(doc)
    requests: list[dict[str, Any]] = []
    if end_index > 2:
        requests.append(
            {
                "deleteContentRange": {
                    "range": {"startIndex": 1, "endIndex": end_index - 1}
                }
            }
        )
    requests.append({"insertText": {"location": {"index": 1}, "text": content}})
    ok, e, _ = await _call(
        "POST",
        f"{_DOCS}/documents/{document_id}:batchUpdate",
        auth_type,
        auth_data,
        json_body={"requests": requests},
        timeout=_LONG_TIMEOUT,
    )
    if not ok:
        return UpdateGoogleDocOutput(success=False, error=e)
    return UpdateGoogleDocOutput(
        success=True,
        id=document_id,
        title=doc.get("title"),
        message="Document updated successfully",
    )


@tool(args_schema=AppendToGoogleDocInput)
@serialize_pydantic_return
async def append_to_google_doc(
    auth_type: str,
    auth_data: dict[str, Any],
    document_id: str,
    content: str,
) -> AppendToGoogleDocOutput:
    """Append content at the end of a Doc."""
    err = _validate(auth_data, "append_to_google_doc")
    if err:
        return AppendToGoogleDocOutput(success=False, error=err)
    ok, e, doc = await _call(
        "GET", f"{_DOCS}/documents/{document_id}", auth_type, auth_data
    )
    if not ok:
        return AppendToGoogleDocOutput(success=False, error=e)
    insert_index = max(1, _doc_end_index(doc) - 1)
    ok, e, _ = await _call(
        "POST",
        f"{_DOCS}/documents/{document_id}:batchUpdate",
        auth_type,
        auth_data,
        json_body={
            "requests": [
                {"insertText": {"location": {"index": insert_index}, "text": content}}
            ]
        },
        timeout=_LONG_TIMEOUT,
    )
    if not ok:
        return AppendToGoogleDocOutput(success=False, error=e)
    return AppendToGoogleDocOutput(
        success=True,
        id=document_id,
        title=doc.get("title"),
        message="Content appended successfully",
    )


# --- Sheets helpers + tools -----------------------------------------------


async def _get_first_sheet_name(
    auth_type: str, auth_data: dict[str, Any], spreadsheet_id: str
) -> str | None:
    ok, _e, data = await _call(
        "GET",
        f"{_SHEETS}/spreadsheets/{spreadsheet_id}",
        auth_type,
        auth_data,
        params={"fields": "sheets.properties.title"},
    )
    if not ok:
        return None
    sheets = data.get("sheets") or []
    if not sheets:
        return None
    return (sheets[0].get("properties") or {}).get("title")


def _resolve_range(range_str: str, actual_sheet_name: str | None) -> str:
    if not actual_sheet_name:
        return range_str
    if range_str.startswith("Sheet1!"):
        return f"{actual_sheet_name}!{range_str[7:]}"
    if range_str == "Sheet1":
        return actual_sheet_name
    return range_str


@tool(args_schema=CreateGoogleSheetInput)
@serialize_pydantic_return
async def create_google_sheet(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    data: list[list[str]] | None = None,
    parent_folder_id: str | None = None,
) -> CreateGoogleSheetOutput:
    """Create a Sheet (Sheets API + optional Drive move + optional values write)."""
    err = _validate(auth_data, "create_google_sheet")
    if err:
        return CreateGoogleSheetOutput(success=False, error=err)
    ok, e, sheet_data = await _call(
        "POST",
        f"{_SHEETS}/spreadsheets",
        auth_type,
        auth_data,
        json_body={"properties": {"title": name}},
        params={"fields": "spreadsheetId,sheets.properties.title"},
        success_codes=(200, 201),
    )
    if not ok:
        return CreateGoogleSheetOutput(success=False, error=e)
    spreadsheet_id = sheet_data.get("spreadsheetId")
    if parent_folder_id and spreadsheet_id:
        await _call(
            "PATCH",
            f"{_DRIVE}/files/{spreadsheet_id}",
            auth_type,
            auth_data,
            params={"addParents": parent_folder_id, "removeParents": "root"},
        )
    if data and spreadsheet_id:
        actual_sheet = (
            (sheet_data.get("sheets") or [{}])[0]
            .get("properties", {})
            .get("title", "Sheet1")
        )
        await _call(
            "PUT",
            f"{_SHEETS}/spreadsheets/{spreadsheet_id}/values/{actual_sheet}!A1",
            auth_type,
            auth_data,
            json_body={"values": data},
            params={"valueInputOption": "RAW"},
            timeout=_LONG_TIMEOUT,
        )
    return CreateGoogleSheetOutput(
        success=True,
        id=spreadsheet_id,
        name=name,
        web_view_link=f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
    )


@tool(args_schema=ReadGoogleSheetInput)
@serialize_pydantic_return
async def read_google_sheet(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    range: str = "Sheet1",
) -> ReadGoogleSheetOutput:
    """Read values from an A1 range (handles localized sheet names)."""
    err = _validate(auth_data, "read_google_sheet")
    if err:
        return ReadGoogleSheetOutput(success=False, error=err)
    actual = await _get_first_sheet_name(auth_type, auth_data, spreadsheet_id)
    resolved = _resolve_range(range, actual)
    ok, e, data = await _call(
        "GET",
        f"{_SHEETS}/spreadsheets/{spreadsheet_id}/values/{resolved}",
        auth_type,
        auth_data,
        timeout=_LONG_TIMEOUT,
    )
    if not ok:
        return ReadGoogleSheetOutput(success=False, error=e)
    values = data.get("values") or []
    return ReadGoogleSheetOutput(
        success=True,
        spreadsheet_id=spreadsheet_id,
        range=data.get("range"),
        values=values,
        row_count=len(values),
    )


@tool(args_schema=UpdateGoogleSheetInput)
@serialize_pydantic_return
async def update_google_sheet(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    range: str,
    data: list[list[str]],
) -> UpdateGoogleSheetOutput:
    """PUT values into an A1 range."""
    err = _validate(auth_data, "update_google_sheet")
    if err:
        return UpdateGoogleSheetOutput(success=False, error=err)
    actual = await _get_first_sheet_name(auth_type, auth_data, spreadsheet_id)
    resolved = _resolve_range(range, actual)
    ok, e, result = await _call(
        "PUT",
        f"{_SHEETS}/spreadsheets/{spreadsheet_id}/values/{resolved}",
        auth_type,
        auth_data,
        json_body={"values": data},
        params={"valueInputOption": "RAW"},
        timeout=_LONG_TIMEOUT,
    )
    if not ok:
        return UpdateGoogleSheetOutput(success=False, error=e)
    return UpdateGoogleSheetOutput(
        success=True,
        spreadsheet_id=spreadsheet_id,
        updated_range=result.get("updatedRange"),
        updated_rows=result.get("updatedRows"),
        updated_columns=result.get("updatedColumns"),
        updated_cells=result.get("updatedCells"),
    )


def _a1_to_grid(a1: str, sheet_id: int = 0) -> dict[str, Any]:
    """Convert A1 notation to a Sheets GridRange."""
    if "!" in a1:
        _, a1 = a1.split("!", 1)
    match = re.match(r"^([A-Z]*)(\d*)(?::([A-Z]*)(\d*))?$", a1)
    if not match:
        raise ValueError(f"Invalid A1 notation: {a1}")
    start_col, start_row, end_col, end_row = match.groups()

    def col_to_num(col: str) -> int:
        result = 0
        for char in col:
            result = result * 26 + (ord(char) - ord("A") + 1)
        return result - 1

    grid: dict[str, Any] = {"sheetId": sheet_id}
    if start_col:
        grid["startColumnIndex"] = col_to_num(start_col)
    if start_row:
        grid["startRowIndex"] = int(start_row) - 1
    if end_col:
        grid["endColumnIndex"] = col_to_num(end_col) + 1
    elif start_col:
        grid["endColumnIndex"] = grid["startColumnIndex"] + 1
    if end_row:
        grid["endRowIndex"] = int(end_row)
    elif start_row:
        grid["endRowIndex"] = grid["startRowIndex"] + 1
    return grid


@tool(args_schema=FormatSheetCellsInput)
@serialize_pydantic_return
async def format_sheet_cells(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    range: str,
    background_color: dict[str, float] | None = None,
    horizontal_alignment: str | None = None,
    vertical_alignment: str | None = None,
) -> FormatSheetCellsOutput:
    """Format cells (background + alignment)."""
    err = _validate(auth_data, "format_sheet_cells")
    if err:
        return FormatSheetCellsOutput(success=False, error=err)
    try:
        grid = _a1_to_grid(range)
    except ValueError as exc:
        return FormatSheetCellsOutput(success=False, error=str(exc))

    cell_format: dict[str, Any] = {}
    fields: list[str] = []
    if background_color:
        cell_format["backgroundColor"] = background_color
        fields.append("userEnteredFormat.backgroundColor")
    if horizontal_alignment:
        cell_format["horizontalAlignment"] = horizontal_alignment
        fields.append("userEnteredFormat.horizontalAlignment")
    if vertical_alignment:
        cell_format["verticalAlignment"] = vertical_alignment
        fields.append("userEnteredFormat.verticalAlignment")
    if not fields:
        return FormatSheetCellsOutput(
            success=False, error="No formatting options specified"
        )
    ok, e, _ = await _call(
        "POST",
        f"{_SHEETS}/spreadsheets/{spreadsheet_id}:batchUpdate",
        auth_type,
        auth_data,
        json_body={
            "requests": [
                {
                    "repeatCell": {
                        "range": grid,
                        "cell": {"userEnteredFormat": cell_format},
                        "fields": ",".join(fields),
                    }
                }
            ]
        },
        timeout=_LONG_TIMEOUT,
    )
    if not ok:
        return FormatSheetCellsOutput(success=False, error=e)
    return FormatSheetCellsOutput(
        success=True,
        spreadsheet_id=spreadsheet_id,
        range=range,
        message="Cells formatted successfully",
    )


@tool(args_schema=FormatSheetTextInput)
@serialize_pydantic_return
async def format_sheet_text(
    auth_type: str,
    auth_data: dict[str, Any],
    spreadsheet_id: str,
    range: str,
    bold: bool | None = None,
    italic: bool | None = None,
    font_size: int | None = None,
    foreground_color: dict[str, float] | None = None,
) -> FormatSheetTextOutput:
    """Format text in cells (bold/italic/font_size/color)."""
    err = _validate(auth_data, "format_sheet_text")
    if err:
        return FormatSheetTextOutput(success=False, error=err)
    try:
        grid = _a1_to_grid(range)
    except ValueError as exc:
        return FormatSheetTextOutput(success=False, error=str(exc))

    text_format: dict[str, Any] = {}
    fields: list[str] = []
    if bold is not None:
        text_format["bold"] = bold
        fields.append("userEnteredFormat.textFormat.bold")
    if italic is not None:
        text_format["italic"] = italic
        fields.append("userEnteredFormat.textFormat.italic")
    if font_size is not None:
        text_format["fontSize"] = font_size
        fields.append("userEnteredFormat.textFormat.fontSize")
    if foreground_color:
        text_format["foregroundColor"] = foreground_color
        fields.append("userEnteredFormat.textFormat.foregroundColor")
    if not fields:
        return FormatSheetTextOutput(
            success=False, error="No text formatting options specified"
        )
    ok, e, _ = await _call(
        "POST",
        f"{_SHEETS}/spreadsheets/{spreadsheet_id}:batchUpdate",
        auth_type,
        auth_data,
        json_body={
            "requests": [
                {
                    "repeatCell": {
                        "range": grid,
                        "cell": {"userEnteredFormat": {"textFormat": text_format}},
                        "fields": ",".join(fields),
                    }
                }
            ]
        },
        timeout=_LONG_TIMEOUT,
    )
    if not ok:
        return FormatSheetTextOutput(success=False, error=e)
    return FormatSheetTextOutput(
        success=True,
        spreadsheet_id=spreadsheet_id,
        range=range,
        message="Text formatted successfully",
    )


# --- Slides tools ---------------------------------------------------------


@tool(args_schema=CreateGoogleSlidesInput)
@serialize_pydantic_return
async def create_google_slides(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    parent_folder_id: str | None = None,
) -> CreateGoogleSlidesOutput:
    """Create a blank Slides presentation."""
    err = _validate(auth_data, "create_google_slides")
    if err:
        return CreateGoogleSlidesOutput(success=False, error=err)
    ok, e, data = await _call(
        "POST",
        f"{_SLIDES}/presentations",
        auth_type,
        auth_data,
        json_body={"title": name},
        success_codes=(200, 201),
    )
    if not ok:
        return CreateGoogleSlidesOutput(success=False, error=e)
    presentation_id = data.get("presentationId")
    if parent_folder_id and presentation_id:
        await _call(
            "PATCH",
            f"{_DRIVE}/files/{presentation_id}",
            auth_type,
            auth_data,
            params={"addParents": parent_folder_id, "removeParents": "root"},
        )
    return CreateGoogleSlidesOutput(
        success=True,
        id=presentation_id,
        name=name,
        web_view_link=f"https://docs.google.com/presentation/d/{presentation_id}",
    )


@tool(args_schema=ReadGoogleSlidesInput)
@serialize_pydantic_return
async def read_google_slides(
    auth_type: str, auth_data: dict[str, Any], presentation_id: str
) -> ReadGoogleSlidesOutput:
    """Read slide metadata + text + placeholder IDs."""
    err = _validate(auth_data, "read_google_slides")
    if err:
        return ReadGoogleSlidesOutput(success=False, error=err)
    ok, e, data = await _call(
        "GET",
        f"{_SLIDES}/presentations/{presentation_id}",
        auth_type,
        auth_data,
        timeout=_LONG_TIMEOUT,
    )
    if not ok:
        return ReadGoogleSlidesOutput(success=False, error=e)
    slides_in = data.get("slides") or []
    slide_info: list[dict[str, Any]] = []
    for slide in slides_in:
        text_content: list[str] = []
        elements: list[dict[str, Any]] = []
        for element in slide.get("pageElements") or []:
            info: dict[str, Any] = {"id": element.get("objectId"), "type": None}
            shape = element.get("shape")
            if shape:
                info["type"] = shape.get("shapeType", "SHAPE")
                placeholder = shape.get("placeholder")
                if placeholder:
                    info["placeholder_type"] = placeholder.get("type")
                if "text" in shape:
                    info["has_text"] = True
                    for text_elem in shape["text"].get("textElements") or []:
                        tr = text_elem.get("textRun")
                        if tr:
                            text_content.append(tr.get("content", ""))
                else:
                    info["has_text"] = False
                elements.append(info)
        slide_info.append(
            {
                "id": slide.get("objectId"),
                "page_elements": len(slide.get("pageElements") or []),
                "text_content": "".join(text_content).strip(),
                "elements": elements,
            }
        )
    return ReadGoogleSlidesOutput(
        success=True,
        id=presentation_id,
        title=data.get("title"),
        slide_count=len(slides_in),
        slides=slide_info,
    )


@tool(args_schema=AddSlideInput)
@serialize_pydantic_return
async def add_slide(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    layout: str = "BLANK",
    insertion_index: int | None = None,
) -> AddSlideOutput:
    """Add a slide with a predefined layout."""
    err = _validate(auth_data, "add_slide")
    if err:
        return AddSlideOutput(success=False, error=err)
    slide_id = f"slide_{uuid.uuid4().hex[:8]}"
    create_req: dict[str, Any] = {
        "objectId": slide_id,
        "slideLayoutReference": {"predefinedLayout": layout},
    }
    if insertion_index is not None:
        create_req["insertionIndex"] = insertion_index
    ok, e, _ = await _call(
        "POST",
        f"{_SLIDES}/presentations/{presentation_id}:batchUpdate",
        auth_type,
        auth_data,
        json_body={"requests": [{"createSlide": create_req}]},
        timeout=_LONG_TIMEOUT,
    )
    if not ok:
        return AddSlideOutput(success=False, error=e)
    return AddSlideOutput(
        success=True,
        presentation_id=presentation_id,
        slide_id=slide_id,
        layout=layout,
        message="Slide added successfully",
    )


@tool(args_schema=UpdateSlideContentInput)
@serialize_pydantic_return
async def update_slide_content(
    auth_type: str,
    auth_data: dict[str, Any],
    presentation_id: str,
    slide_id: str,
    placeholder_id: str,
    text: str,
) -> UpdateSlideContentOutput:
    """Replace text in a slide placeholder."""
    err = _validate(auth_data, "update_slide_content")
    if err:
        return UpdateSlideContentOutput(success=False, error=err)
    ok, e, _ = await _call(
        "POST",
        f"{_SLIDES}/presentations/{presentation_id}:batchUpdate",
        auth_type,
        auth_data,
        json_body={
            "requests": [
                {
                    "deleteText": {
                        "objectId": placeholder_id,
                        "textRange": {"type": "ALL"},
                    }
                },
                {
                    "insertText": {
                        "objectId": placeholder_id,
                        "text": text,
                        "insertionIndex": 0,
                    }
                },
            ]
        },
        timeout=_LONG_TIMEOUT,
    )
    if not ok:
        return UpdateSlideContentOutput(success=False, error=e)
    return UpdateSlideContentOutput(
        success=True,
        presentation_id=presentation_id,
        slide_id=slide_id,
        placeholder_id=placeholder_id,
        message="Slide content updated successfully",
    )
