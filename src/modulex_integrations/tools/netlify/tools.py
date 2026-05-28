"""Netlify LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.netlify.outputs import (
    GetSiteOutput,
    ListFilesOutput,
    ListSiteDeploysOutput,
    RollbackDeployOutput,
)

__all__ = [
    "get_site",
    "list_files",
    "list_site_deploys",
    "rollback_deploy",
]

_BASE_URL = "https://api.netlify.com/api/v1"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Netlify API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas ------------------------------------------------------------


class GetSiteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    site_id: str = Field(description="The Netlify site ID to retrieve information for")


class ListFilesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    site_id: str = Field(description="The Netlify site ID to list files for")


class ListSiteDeploysInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    site_id: str = Field(description="The Netlify site ID to list deploys for")
    max_results: int | None = Field(
        default=None, description="Maximum number of deploys to return"
    )
    max_pages: int = Field(
        default=50,
        description="Maximum number of pages to fetch (1-500)",
        ge=1,
        le=500,
    )


class RollbackDeployInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    site_id: str = Field(description="The Netlify site ID to rollback a deploy for")
    deploy_id: str = Field(description="The deploy ID to restore")


# --- @tool functions ----------------------------------------------------------


@tool(args_schema=GetSiteInput)
@serialize_pydantic_return
async def get_site(
    auth_type: str,
    auth_data: dict[str, Any],
    site_id: str,
) -> GetSiteOutput:
    """Get a specified site by its ID."""
    if not auth_data.get("access_token"):
        return GetSiteOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/sites/{site_id}",
                headers=headers,
            )
        if response.status_code != 200:
            return GetSiteOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetSiteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSiteOutput(success=False, error=f"Call failed: {exc}")

    return GetSiteOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        url=data.get("url"),
        ssl_url=data.get("ssl_url"),
        admin_url=data.get("admin_url"),
        state=data.get("state"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        default_domain=data.get("default_domain"),
        custom_domain=data.get("custom_domain"),
    )


@tool(args_schema=ListFilesInput)
@serialize_pydantic_return
async def list_files(
    auth_type: str,
    auth_data: dict[str, Any],
    site_id: str,
) -> ListFilesOutput:
    """Returns a list of all the files in the current deploy for a site."""
    if not auth_data.get("access_token"):
        return ListFilesOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/sites/{site_id}/files",
                headers=headers,
            )
        if response.status_code != 200:
            return ListFilesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListFilesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFilesOutput(success=False, error=f"Call failed: {exc}")

    return ListFilesOutput(success=True, files=data if isinstance(data, list) else [])


@tool(args_schema=ListSiteDeploysInput)
@serialize_pydantic_return
async def list_site_deploys(
    auth_type: str,
    auth_data: dict[str, Any],
    site_id: str,
    max_results: int | None = None,
    max_pages: int = 50,
) -> ListSiteDeploysOutput:
    """Returns a list of all deploys for a specific site."""
    if not auth_data.get("access_token"):
        return ListSiteDeploysOutput(
            success=False, error="Missing or empty access_token in auth_data."
        )
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        all_deploys: list[dict[str, Any]] = []
        page = 1
        per_page = 100
        pages_seen = 0
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while pages_seen < max_pages:
                pages_seen += 1
                params: dict[str, Any] = {"page": page, "per_page": per_page}
                response = await client.get(
                    f"{_BASE_URL}/sites/{site_id}/deploys",
                    headers=headers,
                    params=params,
                )
                if response.status_code != 200:
                    return ListSiteDeploysOutput(
                        success=False,
                        error=f"API error ({response.status_code}): {response.text}",
                    )
                batch = response.json()
                if not isinstance(batch, list) or not batch:
                    break
                all_deploys.extend(batch)
                if max_results and len(all_deploys) >= max_results:
                    all_deploys = all_deploys[:max_results]
                    break
                if len(batch) < per_page:
                    break
                page += 1
    except httpx.TimeoutException:
        return ListSiteDeploysOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListSiteDeploysOutput(success=False, error=f"Call failed: {exc}")

    return ListSiteDeploysOutput(success=True, deploys=all_deploys)


@tool(args_schema=RollbackDeployInput)
@serialize_pydantic_return
async def rollback_deploy(
    auth_type: str,
    auth_data: dict[str, Any],
    site_id: str,
    deploy_id: str,
) -> RollbackDeployOutput:
    """Restores an old deploy and makes it the live version of the site."""
    if not auth_data.get("access_token"):
        return RollbackDeployOutput(
            success=False, error="Missing or empty access_token in auth_data."
        )
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/sites/{site_id}/deploys/{deploy_id}/restore",
                headers=headers,
            )
        if response.status_code not in (200, 201):
            return RollbackDeployOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return RollbackDeployOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RollbackDeployOutput(success=False, error=f"Call failed: {exc}")

    return RollbackDeployOutput(
        success=True,
        id=data.get("id"),
        state=data.get("state"),
        name=data.get("name"),
        url=data.get("url"),
        ssl_url=data.get("ssl_url"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )
