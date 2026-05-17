"""Microsoft OneDrive LangChain @tool functions."""
from __future__ import annotations

import base64
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.microsoft_onedrive.outputs import (
    CreateFolderOutput,
    CreateFolderResult,
    CreateLinkOutput,
    CreateLinkResult,
    DownloadFileOutput,
    DownloadFileResult,
    DriveItemSummary,
    DriveSummary,
    FindFileByNameOutput,
    GetExcelTableOutput,
    GetExcelTableResult,
    GetFileByIdOutput,
    ListFilesInFolderOutput,
    ListMyDrivesOutput,
    ListSharedFolderReferenceOptionsOutput,
    SearchFilesOutput,
    SharedFolderReferenceOption,
    UploadFileOutput,
    UploadFileResult,
)

__all__ = [
    "create_folder",
    "create_link",
    "download_file",
    "find_file_by_name",
    "get_excel_table",
    "get_file_by_id",
    "list_files_in_folder",
    "list_my_drives",
    "list_shared_folder_reference_options",
    "search_files",
    "upload_file",
]

_BASE_URL = "https://graph.microsoft.com/v1.0"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for Microsoft Graph based on auth_type/auth_data injected by the runtime."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _validate_token(auth_data: dict[str, Any], action_name: str) -> str | None:
    """Return an error string if the OAuth2 access token is missing/empty, else None."""
    token = auth_data.get("access_token")
    if not token or not isinstance(token, str) or not token.strip():
        return f"{action_name}: missing or empty access_token in auth_data"
    return None


def _items_from_value(payload: dict[str, Any]) -> list[DriveItemSummary]:
    """Coerce a Graph 'value' list into a list of DriveItemSummary models."""
    items: list[DriveItemSummary] = []
    for raw in payload.get("value", []) or []:
        if isinstance(raw, dict):
            items.append(DriveItemSummary.model_validate(raw))
    return items


# --- Input schemas --------------------------------------------------------


class CreateFolderInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    folder_name: str = Field(description="The name of the new folder to be created.")
    parent_folder_id: str | None = Field(
        default=None,
        description=(
            "The ID of the folder which the new folder should be created within. "
            "Omit to create at the drive root."
        ),
    )
    shared_folder_reference: str | None = Field(
        default=None,
        description=(
            "Reference of the shared folder (e.g. /drives/{driveId}/items/{folderId}/children). "
            "Mutually exclusive with parent_folder_id."
        ),
    )


class CreateLinkInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    drive_item_id: str = Field(description="The ID of the DriveItem to create a sharing link for.")
    type: str = Field(description="The type of sharing link: view, edit, or embed.")
    scope: str | None = Field(
        default=None,
        description="The scope of link: anonymous or organization.",
    )


class DownloadFileInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    new_file_name: str = Field(
        description=(
            "The file name to save the downloaded content as, under /tmp. Include extension."
        ),
    )
    file_id: str | None = Field(default=None, description="The ID of the file to download.")
    file_path: str | None = Field(
        default=None,
        description="Path to the file from the root folder (e.g. Documents/My Folder/File 1.docx).",
    )
    convert_to_format: str | None = Field(
        default=None,
        description="Optional format conversion: pdf or html.",
    )


class FindFileByNameInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    name: str = Field(description="The name of the file or folder to search for.")
    exclude_folders: bool = Field(default=False, description="Return only files if true.")


class GetExcelTableInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    item_id: str = Field(description="The ID of the Excel (.xlsx) file in OneDrive.")
    table_name: str = Field(description="Name of the table set in the Table Design tab.")
    remove_headers: bool = Field(default=False, description="Remove the header row from the response.")
    number_of_rows: int = Field(
        default=0,
        description="Number of rows to return. 0 means all rows.",
    )


class GetFileByIdInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    file_id: str = Field(description="The ID of the DriveItem to retrieve.")


class ListFilesInFolderInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    folder_id: str = Field(description="The ID of the folder whose children should be listed.")
    exclude_folders: bool = Field(default=False, description="Return only files if true.")


class ListMyDrivesInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")


class ListSharedFolderReferenceOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")


class SearchFilesInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    q: str = Field(description="Query text used to search OneDrive items.")
    exclude_folders: bool = Field(default=False, description="Filter out folders from results.")


class UploadFileInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    upload_folder_id: str = Field(description="The ID of the folder where you want to upload the file.")
    file_url: str = Field(description="Publicly accessible URL of the file to upload.")
    filename: str = Field(description="Name of the new uploaded file (including extension).")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateFolderInput)
@serialize_pydantic_return
async def create_folder(
    auth_type: str,
    auth_data: dict[str, Any],
    folder_name: str,
    parent_folder_id: str | None = None,
    shared_folder_reference: str | None = None,
) -> CreateFolderOutput:
    """Create a new folder in a drive."""
    if err := _validate_token(auth_data, "create_folder"):
        return CreateFolderOutput(success=False, error=err)

    if shared_folder_reference and parent_folder_id:
        return CreateFolderOutput(
            success=False,
            error="Provide either parent_folder_id or shared_folder_reference, not both.",
        )

    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {
        "name": folder_name,
        "folder": {},
        "@microsoft.graph.conflictBehavior": "rename",
    }

    if shared_folder_reference:
        url = f"{_BASE_URL}{shared_folder_reference}"
    elif parent_folder_id:
        url = f"{_BASE_URL}/me/drive/items/{parent_folder_id}/children"
    else:
        url = f"{_BASE_URL}/me/drive/root/children"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            return CreateFolderOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateFolderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateFolderOutput(success=False, error=f"Call failed: {exc}")

    return CreateFolderOutput(
        success=True,
        result=CreateFolderResult.model_validate(data),
    )


@tool(args_schema=CreateLinkInput)
@serialize_pydantic_return
async def create_link(
    auth_type: str,
    auth_data: dict[str, Any],
    drive_item_id: str,
    type: str,
    scope: str | None = None,
) -> CreateLinkOutput:
    """Create a sharing link for a DriveItem."""
    if err := _validate_token(auth_data, "create_link"):
        return CreateLinkOutput(success=False, error=err)

    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"type": type}
    if scope:
        payload["scope"] = scope

    url = f"{_BASE_URL}/me/drive/items/{drive_item_id}/createLink"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            return CreateLinkOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateLinkOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateLinkOutput(success=False, error=f"Call failed: {exc}")

    return CreateLinkOutput(
        success=True,
        result=CreateLinkResult.model_validate(data),
    )


@tool(args_schema=DownloadFileInput)
@serialize_pydantic_return
async def download_file(
    auth_type: str,
    auth_data: dict[str, Any],
    new_file_name: str,
    file_id: str | None = None,
    file_path: str | None = None,
    convert_to_format: str | None = None,
) -> DownloadFileOutput:
    """Download a file stored in OneDrive. Returns base64 content and saved /tmp path."""
    if err := _validate_token(auth_data, "download_file"):
        return DownloadFileOutput(success=False, error=err)

    if not file_id and not file_path:
        return DownloadFileOutput(
            success=False,
            error="Provide either file_id or file_path.",
        )

    headers = _get_auth_headers(auth_type, auth_data)

    if file_id:
        content_url = f"{_BASE_URL}/me/drive/items/{file_id}/content"
    else:
        content_url = f"{_BASE_URL}/me/drive/root:/{quote(file_path or '', safe='/')}:/content"

    params: dict[str, str] | None = None
    if convert_to_format:
        params = {"format": convert_to_format}

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(content_url, headers=headers, params=params)
        if response.status_code >= 400:
            return DownloadFileOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        content_bytes = response.content
    except httpx.TimeoutException:
        return DownloadFileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DownloadFileOutput(success=False, error=f"Call failed: {exc}")

    safe_name = new_file_name.split("/")[-1]
    tmp_path = f"/tmp/{safe_name}"
    try:
        with open(tmp_path, "wb") as fh:
            fh.write(content_bytes)
    except OSError as err:
        return DownloadFileOutput(
            success=False,
            error=f"Failed to write file: {err}",
        )

    return DownloadFileOutput(
        success=True,
        result=DownloadFileResult(
            tmp_file_path=tmp_path,
            file_name=safe_name,
            size_bytes=len(content_bytes),
            content_base64=base64.b64encode(content_bytes).decode("ascii"),
        ),
    )


@tool(args_schema=FindFileByNameInput)
@serialize_pydantic_return
async def find_file_by_name(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    exclude_folders: bool = False,
) -> FindFileByNameOutput:
    """Search for a file or folder by name."""
    if err := _validate_token(auth_data, "find_file_by_name"):
        return FindFileByNameOutput(success=False, error=err)

    headers = _get_auth_headers(auth_type, auth_data)
    url = f"{_BASE_URL}/me/drive/root/search(q='{quote(name, safe='')}')"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        if response.status_code >= 400:
            return FindFileByNameOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return FindFileByNameOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return FindFileByNameOutput(success=False, error=f"Call failed: {exc}")

    items = _items_from_value(data)
    lname = name.lower()
    items = [item for item in items if (item.name or "").lower().find(lname) >= 0]
    if exclude_folders:
        items = [item for item in items if not item.folder]

    return FindFileByNameOutput(
        success=True,
        count=len(items),
        items=items,
    )


@tool(args_schema=GetExcelTableInput)
@serialize_pydantic_return
async def get_excel_table(
    auth_type: str,
    auth_data: dict[str, Any],
    item_id: str,
    table_name: str,
    remove_headers: bool = False,
    number_of_rows: int = 0,
) -> GetExcelTableOutput:
    """Retrieve a table from an Excel spreadsheet stored in OneDrive."""
    if err := _validate_token(auth_data, "get_excel_table"):
        return GetExcelTableOutput(success=False, error=err)

    headers = _get_auth_headers(auth_type, auth_data)
    url = f"{_BASE_URL}/me/drive/items/{item_id}/workbook/tables/{table_name}/range"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        if response.status_code >= 400:
            return GetExcelTableOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetExcelTableOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetExcelTableOutput(success=False, error=f"Call failed: {exc}")

    rows: list[list[str]] = data.get("text") or []
    if remove_headers:
        if number_of_rows <= 0:
            rows = rows[1:]
        else:
            rows = rows[1 : number_of_rows + 1]
    else:
        if number_of_rows > 0:
            rows = rows[: number_of_rows + 1]

    return GetExcelTableOutput(
        success=True,
        result=GetExcelTableResult(rows=rows, row_count=len(rows)),
    )


@tool(args_schema=GetFileByIdInput)
@serialize_pydantic_return
async def get_file_by_id(
    auth_type: str,
    auth_data: dict[str, Any],
    file_id: str,
) -> GetFileByIdOutput:
    """Retrieve a file by ID."""
    if err := _validate_token(auth_data, "get_file_by_id"):
        return GetFileByIdOutput(success=False, error=err)

    headers = _get_auth_headers(auth_type, auth_data)
    url = f"{_BASE_URL}/me/drive/items/{file_id}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        if response.status_code >= 400:
            return GetFileByIdOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetFileByIdOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetFileByIdOutput(success=False, error=f"Call failed: {exc}")

    return GetFileByIdOutput(
        success=True,
        item=DriveItemSummary.model_validate(data),
    )


@tool(args_schema=ListFilesInFolderInput)
@serialize_pydantic_return
async def list_files_in_folder(
    auth_type: str,
    auth_data: dict[str, Any],
    folder_id: str,
    exclude_folders: bool = False,
) -> ListFilesInFolderOutput:
    """Retrieve a list of the files and/or folders directly within a folder."""
    if err := _validate_token(auth_data, "list_files_in_folder"):
        return ListFilesInFolderOutput(success=False, error=err)

    headers = _get_auth_headers(auth_type, auth_data)
    url = f"{_BASE_URL}/me/drive/items/{folder_id}/children"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        if response.status_code >= 400:
            return ListFilesInFolderOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListFilesInFolderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFilesInFolderOutput(success=False, error=f"Call failed: {exc}")

    items = _items_from_value(data)
    if exclude_folders:
        items = [item for item in items if not item.folder]

    return ListFilesInFolderOutput(
        success=True,
        count=len(items),
        items=items,
    )


@tool(args_schema=ListMyDrivesInput)
@serialize_pydantic_return
async def list_my_drives(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListMyDrivesOutput:
    """Get the signed-in user's drives, including the personal OneDrive."""
    if err := _validate_token(auth_data, "list_my_drives"):
        return ListMyDrivesOutput(success=False, error=err)

    headers = _get_auth_headers(auth_type, auth_data)

    drives: list[DriveSummary] = []
    personal: DriveSummary | None = None

    try:
        async with httpx.AsyncClient() as client:
            personal_resp = await client.get(
                f"{_BASE_URL}/me/drive",
                headers=headers,
                params={"$select": "id,name,driveType,owner,quota"},
            )
            if personal_resp.status_code == 200:
                personal = DriveSummary.model_validate(personal_resp.json())
            elif personal_resp.status_code != 404:
                return ListMyDrivesOutput(
                    success=False,
                    error=f"API error ({personal_resp.status_code}): {personal_resp.text}",
                )

            next_url: str | None = (
                f"{_BASE_URL}/me/drives?$select=id,name,driveType,owner,quota"
            )
            pages_seen = 0
            while next_url and pages_seen < 50:
                pages_seen += 1
                resp = await client.get(next_url, headers=headers)
                if resp.status_code >= 400:
                    return ListMyDrivesOutput(
                        success=False,
                        error=f"API error ({resp.status_code}): {resp.text}",
                    )
                payload = resp.json()
                for raw in payload.get("value", []) or []:
                    if isinstance(raw, dict):
                        drives.append(DriveSummary.model_validate(raw))
                next_url = payload.get("@odata.nextLink")
    except httpx.TimeoutException:
        return ListMyDrivesOutput(success=False, error="Request timed out.")
    except httpx.HTTPError as err:
        return ListMyDrivesOutput(success=False, error=f"HTTP error: {err}")
    except Exception as exc:
        return ListMyDrivesOutput(success=False, error=f"Call failed: {exc}")

    seen_ids = {d.id for d in drives if d.id}
    if personal and personal.id and personal.id not in seen_ids:
        drives.append(personal)

    return ListMyDrivesOutput(
        success=True,
        count=len(drives),
        drives=drives,
    )


@tool(args_schema=ListSharedFolderReferenceOptionsInput)
@serialize_pydantic_return
async def list_shared_folder_reference_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListSharedFolderReferenceOptionsOutput:
    """Retrieve available shared folder references for use as shared_folder_reference."""
    if err := _validate_token(auth_data, "list_shared_folder_reference_options"):
        return ListSharedFolderReferenceOptionsOutput(success=False, error=err)

    headers = _get_auth_headers(auth_type, auth_data)
    url = f"{_BASE_URL}/me/drive/sharedWithMe"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        if response.status_code >= 400:
            return ListSharedFolderReferenceOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListSharedFolderReferenceOptionsOutput(
            success=False, error="Request timed out."
        )
    except Exception as exc:
        return ListSharedFolderReferenceOptionsOutput(
            success=False, error=f"Call failed: {exc}"
        )

    options: list[SharedFolderReferenceOption] = []
    for shared in data.get("value", []) or []:
        if not isinstance(shared, dict):
            continue
        remote = shared.get("remoteItem") or {}
        parent = remote.get("parentReference") or {}
        drive_id = parent.get("driveId")
        item_id = remote.get("id")
        if drive_id and item_id:
            options.append(
                SharedFolderReferenceOption(
                    label=shared.get("name") or "",
                    value=f"/drives/{drive_id}/items/{item_id}/children",
                )
            )

    return ListSharedFolderReferenceOptionsOutput(
        success=True,
        count=len(options),
        options=options,
    )


@tool(args_schema=SearchFilesInput)
@serialize_pydantic_return
async def search_files(
    auth_type: str,
    auth_data: dict[str, Any],
    q: str,
    exclude_folders: bool = False,
) -> SearchFilesOutput:
    """Search for files and folders in Microsoft OneDrive."""
    if err := _validate_token(auth_data, "search_files"):
        return SearchFilesOutput(success=False, error=err)

    headers = _get_auth_headers(auth_type, auth_data)
    url = f"{_BASE_URL}/me/drive/root/search(q='{quote(q, safe='')}')"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        if response.status_code >= 400:
            return SearchFilesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchFilesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchFilesOutput(success=False, error=f"Call failed: {exc}")

    items = _items_from_value(data)
    if exclude_folders:
        items = [item for item in items if not item.folder]

    return SearchFilesOutput(
        success=True,
        count=len(items),
        items=items,
    )


@tool(args_schema=UploadFileInput)
@serialize_pydantic_return
async def upload_file(
    auth_type: str,
    auth_data: dict[str, Any],
    upload_folder_id: str,
    file_url: str,
    filename: str,
) -> UploadFileOutput:
    """Upload a file to OneDrive by fetching it from a publicly-accessible URL."""
    if err := _validate_token(auth_data, "upload_file"):
        return UploadFileOutput(success=False, error=err)

    headers = _get_auth_headers(auth_type, auth_data)

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            src_resp = await client.get(file_url)
            if src_resp.status_code >= 400:
                return UploadFileOutput(
                    success=False,
                    error=f"Source URL error ({src_resp.status_code}): {src_resp.text}",
                )
            file_bytes = src_resp.content

            encoded_name = quote(filename, safe="")
            upload_url = (
                f"{_BASE_URL}/me/drive/items/{upload_folder_id}:/{encoded_name}:/content"
            )
            upload_headers = dict(headers)
            upload_headers["Content-Type"] = "application/octet-stream"

            response = await client.put(
                upload_url, headers=upload_headers, content=file_bytes
            )
        if response.status_code >= 400:
            return UploadFileOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UploadFileOutput(success=False, error="Request timed out.")
    except httpx.HTTPError as err:
        return UploadFileOutput(
            success=False, error=f"Failed to fetch source URL: {err}"
        )
    except Exception as exc:
        return UploadFileOutput(success=False, error=f"Call failed: {exc}")

    return UploadFileOutput(
        success=True,
        result=UploadFileResult.model_validate(data),
    )
