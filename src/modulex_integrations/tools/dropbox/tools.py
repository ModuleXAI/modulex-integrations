"""Dropbox LangChain @tool functions."""
from __future__ import annotations

import json
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.dropbox.outputs import (
    CreateFolderOutput,
    CreateOrAppendToTextFileOutput,
    CreateTextFileOutput,
    CreateUpdateShareLinkOutput,
    DeleteFileFolderOutput,
    FileMetadata,
    GetSharedLinkMetadataOutput,
    ListFileFoldersOutput,
    ListFileRevisionsOutput,
    ListSharedLinksOutput,
    MoveFileFolderOutput,
    RenameFileFolderOutput,
    SearchFileFoldersOutput,
    SearchMatch,
    SharedLinkInfo,
)

__all__ = [
    "create_a_text_file",
    "create_folder",
    "create_or_append_to_a_text_file",
    "create_update_share_link",
    "delete_file_folder",
    "get_shared_link_metadata",
    "list_file_folders_in_a_folder",
    "list_file_revisions",
    "list_shared_links",
    "move_file_folder",
    "rename_file_folder",
    "search_files_folders",
]

_BASE_URL = "https://api.dropboxapi.com/2"
_CONTENT_URL = "https://content.dropboxapi.com/2"
_TIMEOUT = 60.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Dropbox API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _parse_file_metadata(data: dict[str, Any]) -> FileMetadata:
    """Parse a Dropbox file/folder metadata dict into a FileMetadata model."""
    return FileMetadata.model_validate({
        ".tag": data.get(".tag"),
        "name": data.get("name"),
        "id": data.get("id"),
        "path_display": data.get("path_display"),
        "path_lower": data.get("path_lower"),
        "size": data.get("size"),
        "rev": data.get("rev"),
        "content_hash": data.get("content_hash"),
        "server_modified": data.get("server_modified"),
        "client_modified": data.get("client_modified"),
        "is_downloadable": data.get("is_downloadable"),
    })


# --- Input schemas --------------------------------------------------------


class CreateFolderInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="The new folder name")
    path: str = Field(default="", description="Parent folder path (empty for root)")
    autorename: bool = Field(default=True, description="Autorename on conflict")


class SearchFileFoldersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str = Field(description="The search query string")
    path: str = Field(default="", description="Folder path to restrict search to")
    order_by: str | None = Field(default=None, description="Sort: relevance, last_modified_time")
    file_status: str | None = Field(default=None, description="Filter: active, deleted")
    filename_only: bool | None = Field(default=None, description="Restrict to filenames only")
    limit: int | None = Field(default=None, description="Maximum results to return")


class ListFileFoldersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    path: str = Field(description="Folder path to list (empty string for root)")
    recursive: bool = Field(default=True, description="List subfolders recursively")
    include_deleted: bool = Field(default=False, description="Include deleted items")
    include_mounted_folders: bool = Field(default=False, description="Include mounted folders")
    include_non_downloadable_files: bool = Field(default=True, description="Include non-downloadable files")
    limit: int | None = Field(default=None, description="Maximum entries to return")


class DeleteFileFolderInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    path: str = Field(description="Path of file or folder to delete")


class MoveFileFolderInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    path_from: str = Field(description="Source path of file or folder")
    path_to: str = Field(description="Destination folder path")
    autorename: bool = Field(default=False, description="Autorename on conflict")
    allow_ownership_transfer: bool = Field(default=False, description="Allow ownership transfer")


class RenameFileFolderInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    path_from: str = Field(description="Path of file or folder to rename")
    new_name: str = Field(description="New name (include extension for files)")
    autorename: bool = Field(default=False, description="Autorename on conflict")
    allow_ownership_transfer: bool = Field(default=False, description="Allow ownership transfer")


class CreateTextFileInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="File name including extension")
    path: str = Field(default="", description="Folder path (empty for root)")
    content: str = Field(description="Text content of the file")


class CreateOrAppendToTextFileInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="File name including extension")
    path: str = Field(default="", description="Folder path (empty for root)")
    content: str = Field(description="Text content to write or append")


class CreateUpdateShareLinkInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    path: str = Field(description="Path of file or folder to share")
    require_password: bool = Field(default=False, description="Enable password protection")
    link_password: str | None = Field(default=None, description="Password for the link")
    expires: str | None = Field(default=None, description="Expiration in ISO 8601 format")
    audience: str | None = Field(default=None, description="Audience: public, team, no_one")


class ListSharedLinksInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    path: str | None = Field(default=None, description="Path to list shared links for")


class GetSharedLinkMetadataInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    shared_link_url: str = Field(description="The URL of the shared link")
    link_password: str | None = Field(default=None, description="Password if link is protected")


class ListFileRevisionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    path: str = Field(description="File path to list revisions for")
    mode: str | None = Field(default=None, description="Mode: path or id")
    limit: int | None = Field(default=None, description="Maximum revision entries to return")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateFolderInput)
@serialize_pydantic_return
async def create_folder(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    path: str = "",
    autorename: bool = True,
) -> CreateFolderOutput:
    """Create a new folder in the user's Dropbox."""
    headers = _get_auth_headers(auth_type, auth_data)
    folder_path = f"{path}/{name}" if path else f"/{name}"
    payload = {"path": folder_path, "autorename": autorename}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/files/create_folder_v2",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            return CreateFolderOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
        metadata = data.get("metadata", {})
    except httpx.TimeoutException:
        return CreateFolderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateFolderOutput(success=False, error=f"Call failed: {exc}")
    return CreateFolderOutput(
        success=True,
        metadata=_parse_file_metadata(metadata),
    )


@tool(args_schema=SearchFileFoldersInput)
@serialize_pydantic_return
async def search_files_folders(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    path: str = "",
    order_by: str | None = None,
    file_status: str | None = None,
    filename_only: bool | None = None,
    limit: int | None = None,
) -> SearchFileFoldersOutput:
    """Search for files and folders by name or content."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"query": query}
    options: dict[str, Any] = {}
    if path:
        options["path"] = path
    if order_by:
        options["order_by"] = {".tag": order_by}
    if file_status:
        options["file_status"] = {".tag": file_status}
    if filename_only is not None:
        options["filename_only"] = filename_only
    if options:
        payload["options"] = options
    if limit:
        payload["options"] = payload.get("options", {})
        payload["options"]["max_results"] = limit
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/files/search_v2",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            return SearchFileFoldersOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchFileFoldersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchFileFoldersOutput(success=False, error=f"Call failed: {exc}")
    matches = []
    for m in data.get("matches", []):
        meta_wrapper = m.get("metadata", {})
        meta = meta_wrapper.get("metadata", {})
        matches.append(SearchMatch(
            match_type=m.get("match_type", {}).get(".tag"),
            metadata=_parse_file_metadata(meta),
        ))
    return SearchFileFoldersOutput(
        success=True,
        matches=matches,
        has_more=data.get("has_more"),
    )


@tool(args_schema=ListFileFoldersInput)
@serialize_pydantic_return
async def list_file_folders_in_a_folder(
    auth_type: str,
    auth_data: dict[str, Any],
    path: str,
    recursive: bool = True,
    include_deleted: bool = False,
    include_mounted_folders: bool = False,
    include_non_downloadable_files: bool = True,
    limit: int | None = None,
) -> ListFileFoldersOutput:
    """List all files and subfolders in a specified folder."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {
        "path": path if path else "",
        "recursive": recursive,
        "include_deleted": include_deleted,
        "include_mounted_folders": include_mounted_folders,
        "include_non_downloadable_files": include_non_downloadable_files,
    }
    if limit:
        payload["limit"] = min(limit, 2000)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/files/list_folder",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            return ListFileFoldersOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListFileFoldersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFileFoldersOutput(success=False, error=f"Call failed: {exc}")
    entries = [_parse_file_metadata(e) for e in data.get("entries", [])]
    return ListFileFoldersOutput(
        success=True,
        entries=entries,
        has_more=data.get("has_more"),
    )


@tool(args_schema=DeleteFileFolderInput)
@serialize_pydantic_return
async def delete_file_folder(
    auth_type: str,
    auth_data: dict[str, Any],
    path: str,
) -> DeleteFileFolderOutput:
    """Permanently delete a file or folder from Dropbox."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload = {"path": path}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/files/delete_v2",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            return DeleteFileFolderOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
        metadata = data.get("metadata", {})
    except httpx.TimeoutException:
        return DeleteFileFolderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteFileFolderOutput(success=False, error=f"Call failed: {exc}")
    return DeleteFileFolderOutput(
        success=True,
        metadata=_parse_file_metadata(metadata),
    )


@tool(args_schema=MoveFileFolderInput)
@serialize_pydantic_return
async def move_file_folder(
    auth_type: str,
    auth_data: dict[str, Any],
    path_from: str,
    path_to: str,
    autorename: bool = False,
    allow_ownership_transfer: bool = False,
) -> MoveFileFolderOutput:
    """Move a file or folder to a different location in Dropbox."""
    headers = _get_auth_headers(auth_type, auth_data)
    from_name = path_from.rstrip("/").rsplit("/", 1)[-1]
    to_path = f"{path_to.rstrip('/')}/{from_name}"
    payload: dict[str, Any] = {
        "from_path": path_from,
        "to_path": to_path,
        "autorename": autorename,
        "allow_ownership_transfer": allow_ownership_transfer,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/files/move_v2",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            return MoveFileFolderOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
        metadata = data.get("metadata", {})
    except httpx.TimeoutException:
        return MoveFileFolderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return MoveFileFolderOutput(success=False, error=f"Call failed: {exc}")
    return MoveFileFolderOutput(
        success=True,
        metadata=_parse_file_metadata(metadata),
    )


@tool(args_schema=RenameFileFolderInput)
@serialize_pydantic_return
async def rename_file_folder(
    auth_type: str,
    auth_data: dict[str, Any],
    path_from: str,
    new_name: str,
    autorename: bool = False,
    allow_ownership_transfer: bool = False,
) -> RenameFileFolderOutput:
    """Rename a file or folder in Dropbox."""
    headers = _get_auth_headers(auth_type, auth_data)
    parent = path_from.rstrip("/").rsplit("/", 1)[0] if "/" in path_from else ""
    to_path = f"{parent}/{new_name}"
    payload: dict[str, Any] = {
        "from_path": path_from,
        "to_path": to_path,
        "autorename": autorename,
        "allow_ownership_transfer": allow_ownership_transfer,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/files/move_v2",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            return RenameFileFolderOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
        metadata = data.get("metadata", {})
    except httpx.TimeoutException:
        return RenameFileFolderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RenameFileFolderOutput(success=False, error=f"Call failed: {exc}")
    return RenameFileFolderOutput(
        success=True,
        metadata=_parse_file_metadata(metadata),
    )


@tool(args_schema=CreateTextFileInput)
@serialize_pydantic_return
async def create_a_text_file(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    content: str,
    path: str = "",
) -> CreateTextFileOutput:
    """Create a new text file from plain text content."""
    headers: dict[str, str] = {"Content-Type": "application/octet-stream"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    if not name.endswith(".txt") and "." not in name:
        name = f"{name}.txt"
    file_path = f"{path}/{name}" if path else f"/{name}"
    api_arg = json.dumps({"path": file_path, "mode": "add", "autorename": True, "mute": False})
    headers["Dropbox-API-Arg"] = api_arg
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_CONTENT_URL}/files/upload",
                headers=headers,
                content=content.encode("utf-8"),
            )
        if response.status_code != 200:
            return CreateTextFileOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateTextFileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateTextFileOutput(success=False, error=f"Call failed: {exc}")
    return CreateTextFileOutput(
        success=True,
        name=data.get("name"),
        id=data.get("id"),
        path_display=data.get("path_display"),
        size=data.get("size"),
        rev=data.get("rev"),
        content_hash=data.get("content_hash"),
    )


@tool(args_schema=CreateOrAppendToTextFileInput)
@serialize_pydantic_return
async def create_or_append_to_a_text_file(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    content: str,
    path: str = "",
) -> CreateOrAppendToTextFileOutput:
    """Append a line to an existing text file, or create the file if it does not exist."""
    auth_headers: dict[str, str] = {}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            auth_headers["Authorization"] = f"Bearer {access_token}"
    file_path = f"{path}/{name}" if path else f"/{name}"
    existing_content = ""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            download_headers = {
                **auth_headers,
                "Dropbox-API-Arg": json.dumps({"path": file_path}),
            }
            dl_response = await client.post(
                f"{_CONTENT_URL}/files/download",
                headers=download_headers,
            )
            if dl_response.status_code == 200:
                existing_content = dl_response.text
    except Exception:
        pass
    new_content = f"{existing_content}\n{content}" if existing_content else content
    upload_headers = {
        **auth_headers,
        "Content-Type": "application/octet-stream",
        "Dropbox-API-Arg": json.dumps({
            "path": file_path,
            "mode": "overwrite",
            "autorename": False,
            "mute": False,
        }),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_CONTENT_URL}/files/upload",
                headers=upload_headers,
                content=new_content.encode("utf-8"),
            )
        if response.status_code != 200:
            return CreateOrAppendToTextFileOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateOrAppendToTextFileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateOrAppendToTextFileOutput(success=False, error=f"Call failed: {exc}")
    return CreateOrAppendToTextFileOutput(
        success=True,
        name=data.get("name"),
        id=data.get("id"),
        path_display=data.get("path_display"),
        size=data.get("size"),
        rev=data.get("rev"),
        content_hash=data.get("content_hash"),
    )


@tool(args_schema=CreateUpdateShareLinkInput)
@serialize_pydantic_return
async def create_update_share_link(
    auth_type: str,
    auth_data: dict[str, Any],
    path: str,
    require_password: bool = False,
    link_password: str | None = None,
    expires: str | None = None,
    audience: str | None = None,
) -> CreateUpdateShareLinkOutput:
    """Create or update a public share link for a file or folder."""
    headers = _get_auth_headers(auth_type, auth_data)
    settings: dict[str, Any] = {}
    if require_password and link_password:
        settings["requested_visibility"] = {".tag": "password"}
        settings["link_password"] = link_password
    elif audience:
        settings["requested_visibility"] = {".tag": audience}
    if expires:
        settings["expires"] = expires
    payload: dict[str, Any] = {"path": path, "settings": settings}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/sharing/create_shared_link_with_settings",
                headers=headers,
                json=payload,
            )
            if response.status_code == 409:
                list_payload: dict[str, Any] = {"path": path, "direct_only": True}
                list_resp = await client.post(
                    f"{_BASE_URL}/sharing/list_shared_links",
                    headers=headers,
                    json=list_payload,
                )
                if list_resp.status_code == 200:
                    links = list_resp.json().get("links", [])
                    if links:
                        link = links[0]
                        return CreateUpdateShareLinkOutput(
                            success=True,
                            url=link.get("url"),
                            name=link.get("name"),
                            path_lower=link.get("path_lower"),
                            link_permissions=link.get("link_permissions"),
                        )
                return CreateUpdateShareLinkOutput(
                    success=False,
                    error="A shared link already exists but could not be retrieved.",
                )
            if response.status_code != 200:
                return CreateUpdateShareLinkOutput(
                    success=False,
                    error=f"API error ({response.status_code}): {response.text}",
                )
            data = response.json()
    except httpx.TimeoutException:
        return CreateUpdateShareLinkOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateUpdateShareLinkOutput(success=False, error=f"Call failed: {exc}")
    return CreateUpdateShareLinkOutput(
        success=True,
        url=data.get("url"),
        name=data.get("name"),
        path_lower=data.get("path_lower"),
        link_permissions=data.get("link_permissions"),
    )


@tool(args_schema=ListSharedLinksInput)
@serialize_pydantic_return
async def list_shared_links(
    auth_type: str,
    auth_data: dict[str, Any],
    path: str | None = None,
) -> ListSharedLinksOutput:
    """List shared links for a file or folder path."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {}
    if path:
        payload["path"] = path
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/sharing/list_shared_links",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            return ListSharedLinksOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListSharedLinksOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListSharedLinksOutput(success=False, error=f"Call failed: {exc}")
    links = [
        SharedLinkInfo(
            url=link.get("url"),
            name=link.get("name"),
            path_lower=link.get("path_lower"),
            id=link.get("id"),
            expires=link.get("expires"),
            link_permissions=link.get("link_permissions"),
        )
        for link in data.get("links", [])
    ]
    return ListSharedLinksOutput(success=True, links=links)


@tool(args_schema=GetSharedLinkMetadataInput)
@serialize_pydantic_return
async def get_shared_link_metadata(
    auth_type: str,
    auth_data: dict[str, Any],
    shared_link_url: str,
    link_password: str | None = None,
) -> GetSharedLinkMetadataOutput:
    """Get metadata for a shared link URL."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"url": shared_link_url}
    if link_password:
        payload["link_password"] = link_password
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/sharing/get_shared_link_metadata",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            return GetSharedLinkMetadataOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetSharedLinkMetadataOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSharedLinkMetadataOutput(success=False, error=f"Call failed: {exc}")
    return GetSharedLinkMetadataOutput(
        success=True,
        url=data.get("url"),
        name=data.get("name"),
        path_lower=data.get("path_lower"),
        id=data.get("id"),
        link_permissions=data.get("link_permissions"),
    )


@tool(args_schema=ListFileRevisionsInput)
@serialize_pydantic_return
async def list_file_revisions(
    auth_type: str,
    auth_data: dict[str, Any],
    path: str,
    mode: str | None = None,
    limit: int | None = None,
) -> ListFileRevisionsOutput:
    """List revision history for a file."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"path": path}
    if mode:
        payload["mode"] = {".tag": mode}
    if limit:
        payload["limit"] = limit
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/files/list_revisions",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            return ListFileRevisionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListFileRevisionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFileRevisionsOutput(success=False, error=f"Call failed: {exc}")
    entries = [_parse_file_metadata(e) for e in data.get("entries", [])]
    return ListFileRevisionsOutput(
        success=True,
        entries=entries,
        is_deleted=data.get("is_deleted"),
    )
