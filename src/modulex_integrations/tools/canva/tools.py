"""Canva LangChain @tool functions."""
from __future__ import annotations

import asyncio
import base64
import json
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.canva.outputs import (
    CreateDesignImportJobOutput,
    CreateDesignOutput,
    DesignSummary,
    ExportDesignOutput,
    ExportJob,
    ImportJob,
    ListDesignsOutput,
    UploadAssetOutput,
    UploadJob,
)

__all__ = [
    "create_design",
    "create_design_import_job",
    "export_design",
    "list_designs",
    "upload_asset",
]

_BASE_URL = "https://api.canva.com/rest/v1"
_TIMEOUT = 30.0
_POLL_INTERVAL = 3.0
_MAX_POLLS = 20


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Canva API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class CreateDesignInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    design_type: str = Field(description="The desired design type: 'preset' or 'custom'")
    title: str | None = Field(default=None, description="The name of the design")
    asset_id: str | None = Field(default=None, description="The ID of the asset to add to the new design")
    design_type_name: str | None = Field(default=None, description="Preset design type name: 'doc', 'whiteboard', or 'presentation'")
    width: int | None = Field(default=None, description="Width in pixels (40-8000) for custom design type")
    height: int | None = Field(default=None, description="Height in pixels (40-8000) for custom design type")


class CreateDesignImportJobInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    title: str = Field(description="The name for the imported design")
    file_url: str = Field(description="URL of the file to import into Canva")


class ExportDesignInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    design_id: str = Field(description="The ID of the design to export")
    format_type: str = Field(description="Export format: 'pdf', 'jpg', 'png', 'pptx', 'gif', or 'mp4'")
    pages: list[int] | None = Field(default=None, description="Page numbers to export (first page is 1)")
    quality: int | None = Field(default=None, description="JPG quality 1-100")
    mp4_quality: str | None = Field(default=None, description="MP4 resolution setting")
    size: str | None = Field(default=None, description="PDF paper size: 'a4', 'a3', 'letter', or 'legal'")
    lossless: bool | None = Field(default=None, description="Use lossless compression for PNG")
    as_single_image: bool | None = Field(default=None, description="Merge multi-page designs into a single PNG")
    export_quality: str | None = Field(default=None, description="Export quality tier: 'regular' or 'pro'")
    height: int | None = Field(default=None, description="Export height in pixels")
    width: int | None = Field(default=None, description="Export width in pixels")


class ListDesignsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str | None = Field(default=None, description="Search keyword or phrase")
    continuation: str | None = Field(default=None, description="Pagination cursor from a previous response")
    ownership: str = Field(default="any", description="Filter: 'any', 'owned', or 'shared'")
    sort_by: str = Field(default="relevance", description="Sort order")
    limit: int = Field(default=25, description="Maximum designs to return (1-100)")


class UploadAssetInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="The asset's name")
    file_url: str = Field(description="URL of the file to upload as an asset")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateDesignInput)
@serialize_pydantic_return
async def create_design(
    auth_type: str,
    auth_data: dict[str, Any],
    design_type: str,
    title: str | None = None,
    asset_id: str | None = None,
    design_type_name: str | None = None,
    width: int | None = None,
    height: int | None = None,
) -> CreateDesignOutput:
    """Creates a new Canva design with preset or custom dimensions."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    body: dict[str, Any] = {}
    if title:
        body["title"] = title
    if asset_id:
        body["asset_id"] = asset_id

    if design_type == "preset":
        body["design_type"] = {"type": "preset", "name": design_type_name or "doc"}
    else:
        body["design_type"] = {
            "type": "custom",
            "width": width or 1080,
            "height": height or 1080,
        }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/designs",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateDesignOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateDesignOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDesignOutput(success=False, error=f"Call failed: {exc}")

    design_data = data.get("design", data)
    return CreateDesignOutput(
        success=True,
        design=DesignSummary(
            id=design_data.get("id"),
            title=design_data.get("title"),
            urls=design_data.get("urls"),
            created_at=design_data.get("created_at"),
            updated_at=design_data.get("updated_at"),
        ),
    )


@tool(args_schema=CreateDesignImportJobInput)
@serialize_pydantic_return
async def create_design_import_job(
    auth_type: str,
    auth_data: dict[str, Any],
    title: str,
    file_url: str,
) -> CreateDesignImportJobOutput:
    """Starts a job to import an external file as a new Canva design."""
    headers = _get_auth_headers(auth_type, auth_data)

    metadata = base64.b64encode(json.dumps({"title": title}).encode()).decode()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            file_response = await client.get(file_url)
            file_response.raise_for_status()
            file_bytes = file_response.content

            import_headers = {
                **headers,
                "Content-Type": "application/octet-stream",
                "Import-Metadata": metadata,
            }
            response = await client.post(
                f"{_BASE_URL}/imports",
                headers=import_headers,
                content=file_bytes,
            )

        if response.status_code not in (200, 201):
            return CreateDesignImportJobOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
        job_data = data.get("job", data)

        job_id = job_data.get("id")
        status = job_data.get("status", {})
        state = status if isinstance(status, str) else status.get("state")

        if job_id and state not in ("completed", "failed"):
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                for _ in range(_MAX_POLLS):
                    await asyncio.sleep(_POLL_INTERVAL)
                    poll_resp = await client.get(
                        f"{_BASE_URL}/imports/{job_id}",
                        headers=_get_auth_headers(auth_type, auth_data),
                    )
                    if poll_resp.status_code == 200:
                        poll_data = poll_resp.json()
                        poll_job = poll_data.get("job", poll_data)
                        poll_status = poll_job.get("status", {})
                        poll_state = poll_status if isinstance(poll_status, str) else poll_status.get("state")
                        if poll_state in ("completed", "failed"):
                            job_data = poll_job
                            status = poll_status
                            break

        design_id = None
        if isinstance(status, dict):
            design_info = status.get("design")
            if design_info:
                design_id = design_info.get("id")

    except httpx.TimeoutException:
        return CreateDesignImportJobOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDesignImportJobOutput(success=False, error=f"Call failed: {exc}")

    final_state = status if isinstance(status, str) else status.get("state") if isinstance(status, dict) else None
    return CreateDesignImportJobOutput(
        success=True,
        job=ImportJob(
            id=job_id,
            status=final_state,
            design_id=design_id,
        ),
    )


@tool(args_schema=ExportDesignInput)
@serialize_pydantic_return
async def export_design(
    auth_type: str,
    auth_data: dict[str, Any],
    design_id: str,
    format_type: str,
    pages: list[int] | None = None,
    quality: int | None = None,
    mp4_quality: str | None = None,
    size: str | None = None,
    lossless: bool | None = None,
    as_single_image: bool | None = None,
    export_quality: str | None = None,
    height: int | None = None,
    width: int | None = None,
) -> ExportDesignOutput:
    """Starts a job to export a Canva design to a file format."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    format_spec: dict[str, Any] = {"type": format_type}
    if quality is not None and format_type == "jpg":
        format_spec["quality"] = quality
    if mp4_quality is not None and format_type == "mp4":
        format_spec["quality"] = mp4_quality
    if size is not None and format_type == "pdf":
        format_spec["size"] = size
    if lossless is not None and format_type == "png":
        format_spec["lossless"] = lossless
    if as_single_image is not None and format_type == "png":
        format_spec["as_single_image"] = as_single_image
    if export_quality is not None:
        format_spec["export_quality"] = export_quality
    if height is not None:
        format_spec["height"] = height
    if width is not None:
        format_spec["width"] = width

    body: dict[str, Any] = {
        "design_id": design_id,
        "format": format_spec,
    }
    if pages is not None:
        body["pages"] = pages

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/exports",
                headers=headers,
                json=body,
            )

        if response.status_code not in (200, 201):
            return ExportDesignOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
        job_data = data.get("job", data)
        job_id = job_data.get("id")
        job_status = job_data.get("status")

        if job_id and job_status not in ("completed", "failed"):
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                for _ in range(_MAX_POLLS):
                    await asyncio.sleep(_POLL_INTERVAL)
                    poll_resp = await client.get(
                        f"{_BASE_URL}/exports/{job_id}",
                        headers=_get_auth_headers(auth_type, auth_data),
                    )
                    if poll_resp.status_code == 200:
                        poll_data = poll_resp.json()
                        poll_job = poll_data.get("job", poll_data)
                        if poll_job.get("status") in ("completed", "failed"):
                            job_data = poll_job
                            break

        urls = job_data.get("urls") or []
        if isinstance(urls, dict):
            urls = list(urls.values())

    except httpx.TimeoutException:
        return ExportDesignOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ExportDesignOutput(success=False, error=f"Call failed: {exc}")

    return ExportDesignOutput(
        success=True,
        job=ExportJob(
            id=job_data.get("id"),
            status=job_data.get("status"),
            urls=urls if isinstance(urls, list) else [],
        ),
    )


@tool(args_schema=ListDesignsInput)
@serialize_pydantic_return
async def list_designs(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str | None = None,
    continuation: str | None = None,
    ownership: str = "any",
    sort_by: str = "relevance",
    limit: int = 25,
) -> ListDesignsOutput:
    """Lists designs owned by or shared with the authenticated Canva user."""
    headers = _get_auth_headers(auth_type, auth_data)

    params: dict[str, str | int] = {"ownership": ownership, "sort_by": sort_by, "limit": limit}
    if query:
        params["query"] = query
    if continuation:
        params["continuation"] = continuation

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/designs",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListDesignsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListDesignsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDesignsOutput(success=False, error=f"Call failed: {exc}")

    items_raw = data.get("items", [])
    items = [
        DesignSummary(
            id=item.get("id"),
            title=item.get("title"),
            owner=item.get("owner"),
            thumbnail=item.get("thumbnail"),
            urls=item.get("urls"),
            created_at=item.get("created_at"),
            updated_at=item.get("updated_at"),
        )
        for item in items_raw
    ]

    return ListDesignsOutput(
        success=True,
        items=items,
        continuation=data.get("continuation"),
    )


@tool(args_schema=UploadAssetInput)
@serialize_pydantic_return
async def upload_asset(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    file_url: str,
) -> UploadAssetOutput:
    """Uploads an asset to Canva from a URL."""
    headers = _get_auth_headers(auth_type, auth_data)

    metadata = base64.b64encode(json.dumps({"name_base64": base64.b64encode(name.encode()).decode()}).encode()).decode()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            file_response = await client.get(file_url)
            file_response.raise_for_status()
            file_bytes = file_response.content

            upload_headers = {
                **headers,
                "Content-Type": "application/octet-stream",
                "Asset-Upload-Metadata": metadata,
            }
            response = await client.post(
                f"{_BASE_URL}/asset-uploads",
                headers=upload_headers,
                content=file_bytes,
            )

        if response.status_code not in (200, 201):
            return UploadAssetOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
        job_data = data.get("job", data)
        job_id = job_data.get("id")
        job_status = job_data.get("status")

        if job_id and job_status not in ("completed", "failed"):
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                for _ in range(_MAX_POLLS):
                    await asyncio.sleep(_POLL_INTERVAL)
                    poll_resp = await client.get(
                        f"{_BASE_URL}/asset-uploads/{job_id}",
                        headers=_get_auth_headers(auth_type, auth_data),
                    )
                    if poll_resp.status_code == 200:
                        poll_data = poll_resp.json()
                        poll_job = poll_data.get("job", poll_data)
                        if poll_job.get("status") in ("completed", "failed"):
                            job_data = poll_job
                            break

    except httpx.TimeoutException:
        return UploadAssetOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UploadAssetOutput(success=False, error=f"Call failed: {exc}")

    return UploadAssetOutput(
        success=True,
        job=UploadJob(
            id=job_data.get("id"),
            status=job_data.get("status"),
            asset=job_data.get("asset"),
        ),
    )
