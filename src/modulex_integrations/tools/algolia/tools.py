"""Algolia LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.algolia.outputs import (
    BrowseRecordsOutput,
    DeleteRecordsOutput,
    ListIndexNameOptionsOutput,
    SaveRecordsOutput,
)

__all__ = [
    "browse_records",
    "delete_records",
    "list_index_name_options",
    "save_records",
]

_TIMEOUT = 30.0


def _read_url(application_id: str) -> str:
    return f"https://{application_id}-dsn.algolia.net"


def _write_url(application_id: str) -> str:
    return f"https://{application_id}.algolia.net"


def _headers(application_id: str, api_key: str) -> dict[str, str]:
    return {
        "X-Algolia-API-Key": api_key,
        "X-Algolia-Application-Id": application_id,
        "Content-Type": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class BrowseRecordsInput(BaseModel):
    index_name: str = Field(description="The name of the Algolia index to browse")
    application_id: str = Field(description="Algolia Application ID")
    api_key: str = Field(description="Algolia API key")


class DeleteRecordsInput(BaseModel):
    index_name: str = Field(description="The name of the Algolia index")
    record_ids: list[str] = Field(description="List of object IDs to delete from the index")
    application_id: str = Field(description="Algolia Application ID")
    api_key: str = Field(description="Algolia API key")


class ListIndexNameOptionsInput(BaseModel):
    application_id: str = Field(description="Algolia Application ID")
    api_key: str = Field(description="Algolia API key")


class SaveRecordsInput(BaseModel):
    index_name: str = Field(description="The name of the Algolia index")
    records: list[dict[str, Any]] = Field(
        description="List of JSON objects to save. Each must have an 'objectID' field."
    )
    application_id: str = Field(description="Algolia Application ID")
    api_key: str = Field(description="Algolia API key")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=BrowseRecordsInput)
@serialize_pydantic_return
async def browse_records(
    index_name: str,
    application_id: str,
    api_key: str,
) -> BrowseRecordsOutput:
    """Browse for records in the given index."""
    if not application_id or not application_id.strip() or not api_key or not api_key.strip():
        return BrowseRecordsOutput(
            success=False,
            error="Algolia credentials are empty. Please configure Application ID and API Key.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_read_url(application_id)}/1/indexes/{index_name}/browse",
                headers=_headers(application_id, api_key),
                json={},
            )
        if response.status_code != 200:
            return BrowseRecordsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return BrowseRecordsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return BrowseRecordsOutput(success=False, error=f"Call failed: {exc}")

    return BrowseRecordsOutput(
        success=True,
        hits=data.get("hits", []),
        cursor=data.get("cursor"),
    )


@tool(args_schema=DeleteRecordsInput)
@serialize_pydantic_return
async def delete_records(
    index_name: str,
    record_ids: list[str],
    application_id: str,
    api_key: str,
) -> DeleteRecordsOutput:
    """Delete records from the given index by object IDs."""
    if not application_id or not application_id.strip() or not api_key or not api_key.strip():
        return DeleteRecordsOutput(
            success=False,
            error="Algolia credentials are empty. Please configure Application ID and API Key.",
        )
    try:
        requests_body = [
            {"action": "deleteObject", "body": {"objectID": obj_id}}
            for obj_id in record_ids
        ]
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_write_url(application_id)}/1/indexes/{index_name}/batch",
                headers=_headers(application_id, api_key),
                json={"requests": requests_body},
            )
        if response.status_code != 200:
            return DeleteRecordsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return DeleteRecordsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteRecordsOutput(success=False, error=f"Call failed: {exc}")

    return DeleteRecordsOutput(
        success=True,
        task_id=data.get("taskID"),
        object_ids=data.get("objectIDs", []),
    )


@tool(args_schema=ListIndexNameOptionsInput)
@serialize_pydantic_return
async def list_index_name_options(
    application_id: str,
    api_key: str,
) -> ListIndexNameOptionsOutput:
    """Retrieves available index names for the application."""
    if not application_id or not application_id.strip() or not api_key or not api_key.strip():
        return ListIndexNameOptionsOutput(
            success=False,
            error="Algolia credentials are empty. Please configure Application ID and API Key.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_read_url(application_id)}/1/indexes",
                headers=_headers(application_id, api_key),
            )
        if response.status_code != 200:
            return ListIndexNameOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListIndexNameOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListIndexNameOptionsOutput(success=False, error=f"Call failed: {exc}")

    items = data.get("items", [])
    index_names = [item.get("name", "") for item in items if item.get("name")]
    return ListIndexNameOptionsOutput(
        success=True,
        index_names=index_names,
    )


@tool(args_schema=SaveRecordsInput)
@serialize_pydantic_return
async def save_records(
    index_name: str,
    records: list[dict[str, Any]],
    application_id: str,
    api_key: str,
) -> SaveRecordsOutput:
    """Adds or updates records in the given index."""
    if not application_id or not application_id.strip() or not api_key or not api_key.strip():
        return SaveRecordsOutput(
            success=False,
            error="Algolia credentials are empty. Please configure Application ID and API Key.",
        )
    try:
        requests_body = [
            {"action": "addObject", "body": record}
            for record in records
        ]
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_write_url(application_id)}/1/indexes/{index_name}/batch",
                headers=_headers(application_id, api_key),
                json={"requests": requests_body},
            )
        if response.status_code != 200:
            return SaveRecordsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SaveRecordsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SaveRecordsOutput(success=False, error=f"Call failed: {exc}")

    return SaveRecordsOutput(
        success=True,
        task_id=data.get("taskID"),
        object_ids=data.get("objectIDs", []),
    )
