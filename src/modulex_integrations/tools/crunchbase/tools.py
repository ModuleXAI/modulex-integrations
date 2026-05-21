"""Crunchbase LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.crunchbase.outputs import (
    GetOrganizationOutput,
    SearchOrganizationsOutput,
)

__all__ = [
    "get_organization",
    "search_organizations",
]

_BASE_URL = "https://api.crunchbase.com/v4/data"


def _headers(user_key: str) -> dict[str, str]:
    return {
        "X-cb-user-key": user_key,
        "Content-Type": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class GetOrganizationInput(BaseModel):
    entity_id: str = Field(description="UUID or permalink of the organization to retrieve")
    user_key: str = Field(description="Crunchbase API user key (provided by credential system)")


class SearchOrganizationsInput(BaseModel):
    field_ids: list[str] = Field(description="Fields to include on the resulting entity (e.g. identifier, short_description, name, website_url)")
    user_key: str = Field(description="Crunchbase API user key (provided by credential system)")
    query: list[dict[str, Any]] | None = Field(default=None, description="Array of query predicate objects for filtering organizations. Each object should have operator_id, type, values, and field_id keys.")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=GetOrganizationInput)
@serialize_pydantic_return
async def get_organization(
    entity_id: str,
    user_key: str,
) -> GetOrganizationOutput:
    """Retrieve details about an organization by UUID or permalink."""
    if not user_key or not user_key.strip():
        return GetOrganizationOutput(
            success=False,
            error="API key is empty. Please configure a valid Crunchbase credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/entities/organizations/{entity_id}",
                headers=_headers(user_key),
            )
        if response.status_code != 200:
            return GetOrganizationOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetOrganizationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetOrganizationOutput(success=False, error=f"Call failed: {exc}")

    return GetOrganizationOutput(success=True, data=data)


@tool(args_schema=SearchOrganizationsInput)
@serialize_pydantic_return
async def search_organizations(
    field_ids: list[str],
    user_key: str,
    query: list[dict[str, Any]] | None = None,
) -> SearchOrganizationsOutput:
    """Search for organizations based on specified criteria."""
    if not user_key or not user_key.strip():
        return SearchOrganizationsOutput(
            success=False,
            error="API key is empty. Please configure a valid Crunchbase credential.",
        )
    payload: dict[str, Any] = {"field_ids": field_ids}
    if query:
        payload["query"] = query
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/searches/organizations",
                headers=_headers(user_key),
                json=payload,
            )
        if response.status_code != 200:
            return SearchOrganizationsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchOrganizationsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchOrganizationsOutput(success=False, error=f"Call failed: {exc}")

    return SearchOrganizationsOutput(
        success=True,
        entities=data.get("entities", []),
        total_count=data.get("count"),
    )
