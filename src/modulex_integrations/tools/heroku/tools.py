"""Heroku LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.heroku.outputs import (
    AppSummary,
    ListAppsOutput,
)

__all__ = [
    "list_apps",
]

_BASE_URL = "https://api.heroku.com"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Heroku Platform API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/vnd.heroku+json; version=3"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class ListAppsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=ListAppsInput)
@serialize_pydantic_return
async def list_apps(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListAppsOutput:
    """List all apps accessible by the authenticated user."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/apps",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    return ListAppsOutput(
        success=True,
        apps=[
            AppSummary(
                id=app.get("id"),
                name=app.get("name"),
                web_url=app.get("web_url"),
                region=(app.get("region") or {}).get("name"),
                stack=(app.get("stack") or {}).get("name"),
                created_at=app.get("created_at"),
                updated_at=app.get("updated_at"),
            )
            for app in data
        ],
    )
