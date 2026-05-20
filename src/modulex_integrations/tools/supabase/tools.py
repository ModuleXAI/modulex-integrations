"""Supabase LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.supabase.outputs import (
    BatchInsertRowsOutput,
    CountRowsOutput,
    DeleteRowOutput,
    InsertRowOutput,
    RemoteProcedureCallOutput,
    SelectRowOutput,
    UpdateRowOutput,
    UpsertRowOutput,
)

__all__ = [
    "batch_insert_rows",
    "count_rows",
    "delete_row",
    "insert_row",
    "remote_procedure_call",
    "select_row",
    "update_row",
    "upsert_row",
]

_FILTER_MAP: dict[str, str] = {
    "eq": "eq",
    "neq": "neq",
    "gt": "gt",
    "gte": "gte",
    "lt": "lt",
    "lte": "lte",
    "like": "like",
    "ilike": "ilike",
    "equalTo": "eq",
    "notEqualTo": "neq",
    "greaterThan": "gt",
    "greaterThanOrEqualTo": "gte",
    "lessThan": "lt",
    "lessThanOrEqualTo": "lte",
    "patternMatch": "like",
    "patternMatchCaseInsensitive": "ilike",
}


def _base_url(subdomain: str) -> str:
    return f"https://{subdomain}.supabase.co/rest/v1"


def _headers(service_key: str) -> dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


# --- Input schemas ------------------------------------------------------------


class SelectRowInput(BaseModel):
    table: str = Field(description="Name of the table to query")
    subdomain: str = Field(description="Supabase project subdomain")
    service_key: str = Field(description="Supabase service role key")
    column: str | None = Field(default=None, description="Column name to filter by")
    filter: str | None = Field(default=None, description="Filter operator: eq, neq, gt, gte, lt, lte, like, ilike")
    value: str | None = Field(default=None, description="Value to filter the column by")
    order_by: str = Field(description="Column name to order results by")
    sort_order: str = Field(default="ascending", description="Sort direction: ascending or descending")
    max: int = Field(default=20, description="Maximum number of rows to return")


class InsertRowInput(BaseModel):
    table: str = Field(description="Name of the table to insert into")
    data: dict[str, Any] = Field(description="Column names and values as key/value pairs for the new row")
    subdomain: str = Field(description="Supabase project subdomain")
    service_key: str = Field(description="Supabase service role key")


class UpdateRowInput(BaseModel):
    table: str = Field(description="Name of the table to update")
    column: str = Field(description="Column name to match rows for update")
    value: str = Field(description="Value to match in the specified column")
    data: dict[str, Any] = Field(description="Column names and new values as key/value pairs")
    subdomain: str = Field(description="Supabase project subdomain")
    service_key: str = Field(description="Supabase service role key")


class UpsertRowInput(BaseModel):
    table: str = Field(description="Name of the table to upsert into")
    data: dict[str, Any] = Field(description="Column names and values as key/value pairs")
    subdomain: str = Field(description="Supabase project subdomain")
    service_key: str = Field(description="Supabase service role key")


class DeleteRowInput(BaseModel):
    table: str = Field(description="Name of the table to delete from")
    column: str = Field(description="Column name to match rows for deletion")
    value: str = Field(description="Value to match in the specified column")
    subdomain: str = Field(description="Supabase project subdomain")
    service_key: str = Field(description="Supabase service role key")


class BatchInsertRowsInput(BaseModel):
    table: str = Field(description="Name of the table to insert rows into")
    data: list[dict[str, Any]] = Field(description="Array of objects, each representing a row")
    subdomain: str = Field(description="Supabase project subdomain")
    service_key: str = Field(description="Supabase service role key")


class RemoteProcedureCallInput(BaseModel):
    function_name: str = Field(description="Name of the Postgres function to call")
    subdomain: str = Field(description="Supabase project subdomain")
    service_key: str = Field(description="Supabase service role key")
    args: dict[str, Any] | None = Field(default=None, description="Arguments to pass to the function")


class CountRowsInput(BaseModel):
    table: str = Field(description="Name of the table to count rows from")
    subdomain: str = Field(description="Supabase project subdomain")
    service_key: str = Field(description="Supabase service role key")
    column: str | None = Field(default=None, description="Column name to filter by")
    filter: str | None = Field(default=None, description="Filter operator: eq, neq, gt, gte, lt, lte, like, ilike")
    value: str | None = Field(default=None, description="Value to filter the column by")


# --- @tool functions ----------------------------------------------------------


@tool(args_schema=SelectRowInput)
@serialize_pydantic_return
async def select_row(
    table: str,
    subdomain: str,
    service_key: str,
    order_by: str,
    column: str | None = None,
    filter: str | None = None,
    value: str | None = None,
    sort_order: str = "ascending",
    max: int = 20,
) -> SelectRowOutput:
    """Select row(s) from a Supabase database table with optional filtering and ordering."""
    if not subdomain or not subdomain.strip():
        return SelectRowOutput(success=False, error="Supabase subdomain is empty. Please configure a valid credential.")
    if not service_key or not service_key.strip():
        return SelectRowOutput(success=False, error="Service key is empty. Please configure a valid credential.")

    url = f"{_base_url(subdomain)}/{table}"
    params: dict[str, str] = {
        "select": "*",
        "order": f"{order_by}.{'asc' if sort_order == 'ascending' else 'desc'}",
        "limit": str(max),
    }

    if column and filter and value:
        op = _FILTER_MAP.get(filter, filter)
        params[column] = f"{op}.{value}"

    hdrs = _headers(service_key)
    hdrs.pop("Prefer", None)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=hdrs, params=params)
        if response.status_code != 200:
            return SelectRowOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
                status=response.status_code,
                status_text=response.reason_phrase,
            )
        data = response.json()
    except httpx.TimeoutException:
        return SelectRowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SelectRowOutput(success=False, error=f"Call failed: {exc}")

    return SelectRowOutput(
        success=True,
        data=data if isinstance(data, list) else [],
        count=len(data) if isinstance(data, list) else None,
        status=response.status_code,
        status_text=response.reason_phrase,
    )


@tool(args_schema=InsertRowInput)
@serialize_pydantic_return
async def insert_row(
    table: str,
    data: dict[str, Any],
    subdomain: str,
    service_key: str,
) -> InsertRowOutput:
    """Insert a new row into a Supabase database table."""
    if not subdomain or not subdomain.strip():
        return InsertRowOutput(success=False, error="Supabase subdomain is empty. Please configure a valid credential.")
    if not service_key or not service_key.strip():
        return InsertRowOutput(success=False, error="Service key is empty. Please configure a valid credential.")

    url = f"{_base_url(subdomain)}/{table}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=_headers(service_key), json=data)
        if response.status_code not in (200, 201):
            return InsertRowOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
                status=response.status_code,
                status_text=response.reason_phrase,
            )
        result = response.json()
    except httpx.TimeoutException:
        return InsertRowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return InsertRowOutput(success=False, error=f"Call failed: {exc}")

    return InsertRowOutput(
        success=True,
        data=result if isinstance(result, list) else [result] if isinstance(result, dict) else [],
        status=response.status_code,
        status_text=response.reason_phrase,
    )


@tool(args_schema=UpdateRowInput)
@serialize_pydantic_return
async def update_row(
    table: str,
    column: str,
    value: str,
    data: dict[str, Any],
    subdomain: str,
    service_key: str,
) -> UpdateRowOutput:
    """Update row(s) in a Supabase database table matching a column value."""
    if not subdomain or not subdomain.strip():
        return UpdateRowOutput(success=False, error="Supabase subdomain is empty. Please configure a valid credential.")
    if not service_key or not service_key.strip():
        return UpdateRowOutput(success=False, error="Service key is empty. Please configure a valid credential.")

    url = f"{_base_url(subdomain)}/{table}"
    params: dict[str, str] = {column: f"eq.{value}"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(url, headers=_headers(service_key), json=data, params=params)
        if response.status_code not in (200, 204):
            return UpdateRowOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
                status=response.status_code,
                status_text=response.reason_phrase,
            )
        result = response.json() if response.status_code == 200 else []
    except httpx.TimeoutException:
        return UpdateRowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateRowOutput(success=False, error=f"Call failed: {exc}")

    return UpdateRowOutput(
        success=True,
        data=result if isinstance(result, list) else [result] if isinstance(result, dict) else [],
        status=response.status_code,
        status_text=response.reason_phrase,
    )


@tool(args_schema=UpsertRowInput)
@serialize_pydantic_return
async def upsert_row(
    table: str,
    data: dict[str, Any],
    subdomain: str,
    service_key: str,
) -> UpsertRowOutput:
    """Insert a row or update it if it already exists in a Supabase database table."""
    if not subdomain or not subdomain.strip():
        return UpsertRowOutput(success=False, error="Supabase subdomain is empty. Please configure a valid credential.")
    if not service_key or not service_key.strip():
        return UpsertRowOutput(success=False, error="Service key is empty. Please configure a valid credential.")

    url = f"{_base_url(subdomain)}/{table}"
    hdrs = _headers(service_key)
    hdrs["Prefer"] = "resolution=merge-duplicates,return=representation"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=hdrs, json=data)
        if response.status_code not in (200, 201):
            return UpsertRowOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
                status=response.status_code,
                status_text=response.reason_phrase,
            )
        result = response.json()
    except httpx.TimeoutException:
        return UpsertRowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpsertRowOutput(success=False, error=f"Call failed: {exc}")

    return UpsertRowOutput(
        success=True,
        data=result if isinstance(result, list) else [result] if isinstance(result, dict) else [],
        status=response.status_code,
        status_text=response.reason_phrase,
    )


@tool(args_schema=DeleteRowInput)
@serialize_pydantic_return
async def delete_row(
    table: str,
    column: str,
    value: str,
    subdomain: str,
    service_key: str,
) -> DeleteRowOutput:
    """Delete row(s) from a Supabase database table matching a column value."""
    if not subdomain or not subdomain.strip():
        return DeleteRowOutput(success=False, error="Supabase subdomain is empty. Please configure a valid credential.")
    if not service_key or not service_key.strip():
        return DeleteRowOutput(success=False, error="Service key is empty. Please configure a valid credential.")

    url = f"{_base_url(subdomain)}/{table}"
    params: dict[str, str] = {column: f"eq.{value}"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(url, headers=_headers(service_key), params=params)
        if response.status_code not in (200, 204):
            return DeleteRowOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
                status=response.status_code,
                status_text=response.reason_phrase,
            )
        result = response.json() if response.status_code == 200 else []
    except httpx.TimeoutException:
        return DeleteRowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteRowOutput(success=False, error=f"Call failed: {exc}")

    return DeleteRowOutput(
        success=True,
        data=result if isinstance(result, list) else [result] if isinstance(result, dict) else [],
        status=response.status_code,
        status_text=response.reason_phrase,
    )


@tool(args_schema=BatchInsertRowsInput)
@serialize_pydantic_return
async def batch_insert_rows(
    table: str,
    data: list[dict[str, Any]],
    subdomain: str,
    service_key: str,
) -> BatchInsertRowsOutput:
    """Insert multiple rows into a Supabase database table at once."""
    if not subdomain or not subdomain.strip():
        return BatchInsertRowsOutput(success=False, error="Supabase subdomain is empty. Please configure a valid credential.")
    if not service_key or not service_key.strip():
        return BatchInsertRowsOutput(success=False, error="Service key is empty. Please configure a valid credential.")

    url = f"{_base_url(subdomain)}/{table}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=_headers(service_key), json=data)
        if response.status_code not in (200, 201):
            return BatchInsertRowsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
                status=response.status_code,
                status_text=response.reason_phrase,
            )
        result = response.json()
    except httpx.TimeoutException:
        return BatchInsertRowsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return BatchInsertRowsOutput(success=False, error=f"Call failed: {exc}")

    return BatchInsertRowsOutput(
        success=True,
        data=result if isinstance(result, list) else [result] if isinstance(result, dict) else [],
        status=response.status_code,
        status_text=response.reason_phrase,
    )


@tool(args_schema=RemoteProcedureCallInput)
@serialize_pydantic_return
async def remote_procedure_call(
    function_name: str,
    subdomain: str,
    service_key: str,
    args: dict[str, Any] | None = None,
) -> RemoteProcedureCallOutput:
    """Call a Postgres function (RPC) in a Supabase database."""
    if not subdomain or not subdomain.strip():
        return RemoteProcedureCallOutput(success=False, error="Supabase subdomain is empty. Please configure a valid credential.")
    if not service_key or not service_key.strip():
        return RemoteProcedureCallOutput(success=False, error="Service key is empty. Please configure a valid credential.")

    url = f"{_base_url(subdomain)}/rpc/{function_name}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=_headers(service_key), json=args or {})
        if response.status_code != 200:
            return RemoteProcedureCallOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
                status=response.status_code,
                status_text=response.reason_phrase,
            )
        result = response.json()
    except httpx.TimeoutException:
        return RemoteProcedureCallOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RemoteProcedureCallOutput(success=False, error=f"Call failed: {exc}")

    return RemoteProcedureCallOutput(
        success=True,
        data=result,
        status=response.status_code,
        status_text=response.reason_phrase,
    )


@tool(args_schema=CountRowsInput)
@serialize_pydantic_return
async def count_rows(
    table: str,
    subdomain: str,
    service_key: str,
    column: str | None = None,
    filter: str | None = None,
    value: str | None = None,
) -> CountRowsOutput:
    """Count rows in a Supabase database table with optional filtering."""
    if not subdomain or not subdomain.strip():
        return CountRowsOutput(success=False, error="Supabase subdomain is empty. Please configure a valid credential.")
    if not service_key or not service_key.strip():
        return CountRowsOutput(success=False, error="Service key is empty. Please configure a valid credential.")

    url = f"{_base_url(subdomain)}/{table}"
    params: dict[str, str] = {"select": "count"}
    hdrs = _headers(service_key)
    hdrs["Prefer"] = "count=exact"
    hdrs.pop("Content-Type", None)

    if column and filter and value:
        op = _FILTER_MAP.get(filter, filter)
        params[column] = f"{op}.{value}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.head(url, headers=hdrs, params=params)
        if response.status_code != 200:
            return CountRowsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        content_range = response.headers.get("content-range", "")
        count_str = content_range.split("/")[-1] if "/" in content_range else None
        count = int(count_str) if count_str and count_str != "*" else None
    except httpx.TimeoutException:
        return CountRowsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CountRowsOutput(success=False, error=f"Call failed: {exc}")

    return CountRowsOutput(success=True, count=count)
