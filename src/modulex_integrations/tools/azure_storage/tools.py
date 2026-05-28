"""Azure Storage LangChain @tool functions."""
from __future__ import annotations

import mimetypes
from typing import Any
from xml.etree import ElementTree

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.azure_storage.outputs import (
    CreateContainerOutput,
    DeleteBlobOutput,
    ListContainersOutput,
    UploadBlobOutput,
)

__all__ = [
    "create_container",
    "delete_blob",
    "list_containers",
    "upload_blob",
]

_API_VERSION = "2021-12-02"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for Azure Blob Storage REST API."""
    headers: dict[str, str] = {
        "x-ms-version": _API_VERSION,
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _base_url(auth_data: dict[str, Any]) -> str:
    """Construct the dynamic base URL from the storage account name in auth_data."""
    account = auth_data.get("storage_account_name", "")
    return f"https://{account}.blob.core.windows.net"


# --- Input schemas --------------------------------------------------------


class CreateContainerInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    container_name: str = Field(description="Name of the container to create (lowercase, alphanumeric and hyphens only)")


class DeleteBlobInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    container_name: str = Field(description="Name of the container holding the blob")
    blob_name: str = Field(description="Name of the blob to delete")


class ListContainersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class UploadBlobInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    container_name: str = Field(description="Name of the target container")
    blob_name: str = Field(description="Name for the blob in the container")
    file_url: str = Field(description="Publicly accessible URL of the file to upload")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateContainerInput)
@serialize_pydantic_return
async def create_container(
    auth_type: str,
    auth_data: dict[str, Any],
    container_name: str,
) -> CreateContainerOutput:
    """Create a new container under the specified storage account."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{base}/{container_name}",
                headers=headers,
                params={"restype": "container"},
            )
        if response.status_code not in (201, 204):
            return CreateContainerOutput(
                success=False,
                error=f"Azure API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return CreateContainerOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateContainerOutput(success=False, error=f"Call failed: {exc}")
    return CreateContainerOutput(success=True)


@tool(args_schema=DeleteBlobInput)
@serialize_pydantic_return
async def delete_blob(
    auth_type: str,
    auth_data: dict[str, Any],
    container_name: str,
    blob_name: str,
) -> DeleteBlobOutput:
    """Delete a specific blob from a container in Azure Storage."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{base}/{container_name}/{blob_name}",
                headers=headers,
            )
        if response.status_code not in (200, 202, 204):
            return DeleteBlobOutput(
                success=False,
                error=f"Azure API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteBlobOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteBlobOutput(success=False, error=f"Call failed: {exc}")
    return DeleteBlobOutput(success=True)


@tool(args_schema=ListContainersInput)
@serialize_pydantic_return
async def list_containers(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListContainersOutput:
    """List all containers in the storage account."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                base,
                headers=headers,
                params={"comp": "list"},
            )
        if response.status_code != 200:
            return ListContainersOutput(
                success=False,
                error=f"Azure API error ({response.status_code}): {response.text}",
            )
        root = ElementTree.fromstring(response.text)
        containers = [
            elem.text
            for elem in root.iter("Name")
            if elem.text is not None
        ]
    except httpx.TimeoutException:
        return ListContainersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListContainersOutput(success=False, error=f"Call failed: {exc}")
    return ListContainersOutput(success=True, containers=containers)


@tool(args_schema=UploadBlobInput)
@serialize_pydantic_return
async def upload_blob(
    auth_type: str,
    auth_data: dict[str, Any],
    container_name: str,
    blob_name: str,
    file_url: str,
) -> UploadBlobOutput:
    """Upload content from a URL to a blob in Azure Storage."""
    headers = _get_auth_headers(auth_type, auth_data)
    base = _base_url(auth_data)
    content_type, _ = mimetypes.guess_type(blob_name)
    if not content_type:
        content_type = "application/octet-stream"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            download = await client.get(file_url)
            download.raise_for_status()
            blob_content = download.content

            upload_headers = {
                **headers,
                "x-ms-blob-type": "BlockBlob",
                "Content-Type": content_type,
            }
            response = await client.put(
                f"{base}/{container_name}/{blob_name}",
                headers=upload_headers,
                content=blob_content,
            )
        if response.status_code not in (200, 201):
            return UploadBlobOutput(
                success=False,
                error=f"Azure API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return UploadBlobOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UploadBlobOutput(success=False, error=f"Call failed: {exc}")
    return UploadBlobOutput(success=True)
