"""Google AppSheet LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_appsheet.outputs import (
    AddRowOutput,
    DeleteRowOutput,
    GetRowsOutput,
    UpdateRowOutput,
)

__all__ = [
    "add_row",
    "delete_row",
    "get_rows",
    "update_row",
]

_BASE_URL = "https://api.appsheet.com/api/v2/apps"


def _headers(api_key: str) -> dict[str, str]:
    return {
        "ApplicationAccessKey": api_key,
        "Content-Type": "application/json",
    }


def _action_url(app_id: str, table_name: str) -> str:
    return f"{_BASE_URL}/{app_id}/tables/{table_name}/Action"


# --- Input schemas --------------------------------------------------------


class AddRowInput(BaseModel):
    table_name: str = Field(description="Name of the table to add a row to")
    row: dict[str, Any] = Field(description="JSON object representing the row data to add, with keys matching table column names")
    app_id: str = Field(description="AppSheet application ID")
    api_key: str = Field(description="AppSheet Application Access Key")


class DeleteRowInput(BaseModel):
    table_name: str = Field(description="Name of the table to delete a row from")
    row: dict[str, Any] | None = Field(default=None, description="JSON object containing the key field values of the record to delete")
    app_id: str = Field(description="AppSheet application ID")
    api_key: str = Field(description="AppSheet Application Access Key")


class GetRowsInput(BaseModel):
    table_name: str = Field(description="Name of the table to read rows from")
    selector: str | None = Field(default=None, description="An expression to filter and format the rows returned")
    row: dict[str, Any] | None = Field(default=None, description="Filter results using key field values")
    app_id: str = Field(description="AppSheet application ID")
    api_key: str = Field(description="AppSheet Application Access Key")


class UpdateRowInput(BaseModel):
    table_name: str = Field(description="Name of the table containing the row to update")
    row: dict[str, Any] = Field(description="JSON object with the key field values of the record to update and any fields to change")
    app_id: str = Field(description="AppSheet application ID")
    api_key: str = Field(description="AppSheet Application Access Key")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AddRowInput)
@serialize_pydantic_return
async def add_row(
    table_name: str,
    row: dict[str, Any],
    app_id: str,
    api_key: str,
) -> AddRowOutput:
    """Add a new row to a specific table in the AppSheet app."""
    if not api_key or not api_key.strip():
        return AddRowOutput(success=False, error="API key is empty. Please configure a valid credential.")
    if not app_id or not app_id.strip():
        return AddRowOutput(success=False, error="App ID is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                _action_url(app_id, table_name),
                headers=_headers(api_key),
                json={
                    "Action": "Add",
                    "Properties": {"Locale": "en-US"},
                    "Rows": [row],
                },
            )
        if response.status_code != 200:
            return AddRowOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return AddRowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddRowOutput(success=False, error=f"Call failed: {exc}")
    return AddRowOutput(success=True, rows=data.get("Rows", []))


@tool(args_schema=DeleteRowInput)
@serialize_pydantic_return
async def delete_row(
    table_name: str,
    app_id: str,
    api_key: str,
    row: dict[str, Any] | None = None,
) -> DeleteRowOutput:
    """Delete a specific row from a table in the AppSheet app."""
    if not api_key or not api_key.strip():
        return DeleteRowOutput(success=False, error="API key is empty. Please configure a valid credential.")
    if not app_id or not app_id.strip():
        return DeleteRowOutput(success=False, error="App ID is empty. Please configure a valid credential.")
    try:
        body: dict[str, Any] = {
            "Action": "Delete",
            "Properties": {"Locale": "en-US"},
        }
        if row is not None:
            body["Rows"] = [row]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                _action_url(app_id, table_name),
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return DeleteRowOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return DeleteRowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteRowOutput(success=False, error=f"Call failed: {exc}")
    return DeleteRowOutput(success=True, rows=data.get("Rows", []))


@tool(args_schema=GetRowsInput)
@serialize_pydantic_return
async def get_rows(
    table_name: str,
    app_id: str,
    api_key: str,
    selector: str | None = None,
    row: dict[str, Any] | None = None,
) -> GetRowsOutput:
    """Read existing records from a table in the AppSheet app."""
    if not api_key or not api_key.strip():
        return GetRowsOutput(success=False, error="API key is empty. Please configure a valid credential.")
    if not app_id or not app_id.strip():
        return GetRowsOutput(success=False, error="App ID is empty. Please configure a valid credential.")
    try:
        body: dict[str, Any] = {
            "Action": "Find",
            "Properties": {"Locale": "en-US"},
        }
        if selector:
            body["Properties"]["Selector"] = selector
        if row is not None:
            body["Rows"] = [row]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                _action_url(app_id, table_name),
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return GetRowsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetRowsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetRowsOutput(success=False, error=f"Call failed: {exc}")
    rows = data if isinstance(data, list) else data.get("Rows", [])
    return GetRowsOutput(success=True, rows=rows)


@tool(args_schema=UpdateRowInput)
@serialize_pydantic_return
async def update_row(
    table_name: str,
    row: dict[str, Any],
    app_id: str,
    api_key: str,
) -> UpdateRowOutput:
    """Update an existing row in a specific table in the AppSheet app."""
    if not api_key or not api_key.strip():
        return UpdateRowOutput(success=False, error="API key is empty. Please configure a valid credential.")
    if not app_id or not app_id.strip():
        return UpdateRowOutput(success=False, error="App ID is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                _action_url(app_id, table_name),
                headers=_headers(api_key),
                json={
                    "Action": "Edit",
                    "Properties": {"Locale": "en-US"},
                    "Rows": [row],
                },
            )
        if response.status_code != 200:
            return UpdateRowOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return UpdateRowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateRowOutput(success=False, error=f"Call failed: {exc}")
    return UpdateRowOutput(success=True, rows=data.get("Rows", []))
