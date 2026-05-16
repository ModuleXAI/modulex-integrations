"""Airtable LangChain ``@tool`` functions.

Hits two endpoint families under ``api.airtable.com/v0``:

- ``/v0/meta/...`` for base + table discovery.
- ``/v0/{base_id}/{table}`` for record CRUD.

Airtable caps record-batch operations at 10 records per request.
``create_records`` / ``update_records`` / ``delete_records`` split
input lists into 10-row batches automatically (matching legacy).
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.airtable.outputs import (
    AirtableRecord,
    CreateRecordsOutput,
    DeleteRecordsOutput,
    GetRecordOutput,
    ListBasesOutput,
    ListRecordsOutput,
    ListTablesOutput,
    UpdateRecordsOutput,
)

__all__ = [
    "create_records",
    "delete_records",
    "get_record",
    "list_bases",
    "list_records",
    "list_tables",
    "update_records",
]

_BASE_URL = "https://api.airtable.com/v0"
_TIMEOUT = 30.0
_BATCH_SIZE = 10


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _empty_key_error(name: str) -> str:
    return (
        f"Airtable API key is empty for {name}. "
        "Please configure a valid Airtable credential."
    )


def _api_error(response: httpx.Response) -> str:
    return f"Airtable API error: {response.status_code} - {response.text}"


def _to_record(raw: dict[str, Any]) -> AirtableRecord:
    return AirtableRecord(
        id=raw.get("id"),
        fields=raw.get("fields") or {},
        createdTime=raw.get("createdTime"),
    )


class ListBasesInput(BaseModel):
    api_key: str = Field(description="Airtable PAT (provided by credential system)")


class ListTablesInput(BaseModel):
    api_key: str = Field(description="Airtable PAT (provided by credential system)")
    base_id: str = Field(description="The ID of the Airtable base (starts with 'app')")


class ListRecordsInput(BaseModel):
    api_key: str = Field(description="Airtable PAT (provided by credential system)")
    base_id: str = Field(description="The ID of the Airtable base")
    table_name: str = Field(description="Name or ID of the table")
    max_records: int = Field(default=100, description="Max records to return (1-100)")
    filter_formula: str | None = Field(default=None, description="Airtable filter formula")
    sort_field: str | None = Field(default=None, description="Field name to sort by")
    sort_direction: str | None = Field(default="asc", description="'asc' or 'desc'")
    view: str | None = Field(default=None, description="Name or ID of view")


class GetRecordInput(BaseModel):
    api_key: str = Field(description="Airtable PAT (provided by credential system)")
    base_id: str = Field(description="The ID of the Airtable base")
    table_name: str = Field(description="Name or ID of the table")
    record_id: str = Field(description="The ID of the record (starts with 'rec')")


class CreateRecordsInput(BaseModel):
    api_key: str = Field(description="Airtable PAT (provided by credential system)")
    base_id: str = Field(description="The ID of the Airtable base")
    table_name: str = Field(description="Name or ID of the table")
    records: list[dict[str, Any]] = Field(description="Records (field: value dicts)")
    typecast: bool = Field(default=False, description="Auto-convert string values")


class UpdateRecordsInput(BaseModel):
    api_key: str = Field(description="Airtable PAT (provided by credential system)")
    base_id: str = Field(description="The ID of the Airtable base")
    table_name: str = Field(description="Name or ID of the table")
    records: list[dict[str, Any]] = Field(
        description="Records with 'id' and 'fields' (or flat top-level fields)"
    )
    typecast: bool = Field(default=False, description="Auto-convert string values")


class DeleteRecordsInput(BaseModel):
    api_key: str = Field(description="Airtable PAT (provided by credential system)")
    base_id: str = Field(description="The ID of the Airtable base")
    table_name: str = Field(description="Name or ID of the table")
    record_ids: list[str] = Field(description="Record IDs to delete (each starts with 'rec')")


@tool(args_schema=ListBasesInput)
@serialize_pydantic_return
async def list_bases(api_key: str) -> ListBasesOutput:
    """List all Airtable bases accessible with the provided token."""
    if not api_key or not api_key.strip():
        return ListBasesOutput(success=False, error=_empty_key_error("list_bases"))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/meta/bases", headers=_headers(api_key)
            )
        if response.status_code != 200:
            return ListBasesOutput(success=False, error=_api_error(response))
        body = response.json() or {}
    except Exception as exc:
        return ListBasesOutput(success=False, error=f"list_bases failed: {exc}")

    bases = body.get("bases") or []
    return ListBasesOutput(success=True, bases=bases, count=len(bases))


@tool(args_schema=ListTablesInput)
@serialize_pydantic_return
async def list_tables(api_key: str, base_id: str) -> ListTablesOutput:
    """List tables in a base with their fields and views."""
    if not api_key or not api_key.strip():
        return ListTablesOutput(success=False, error=_empty_key_error("list_tables"))
    if not base_id or not base_id.strip():
        return ListTablesOutput(success=False, error="Base ID is required.")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/meta/bases/{base_id}/tables",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return ListTablesOutput(success=False, error=_api_error(response))
        body = response.json() or {}
    except Exception as exc:
        return ListTablesOutput(success=False, error=f"list_tables failed: {exc}")

    raw_tables = body.get("tables") or []
    summaries: list[dict[str, Any]] = []
    for table in raw_tables:
        summaries.append(
            {
                "id": table.get("id"),
                "name": table.get("name"),
                "description": table.get("description"),
                "primaryFieldId": table.get("primaryFieldId"),
                "fields": [
                    {"id": f.get("id"), "name": f.get("name"), "type": f.get("type")}
                    for f in table.get("fields", [])
                ],
                "views": [
                    {"id": v.get("id"), "name": v.get("name"), "type": v.get("type")}
                    for v in table.get("views", [])
                ],
            }
        )
    return ListTablesOutput(
        success=True, tables=summaries, count=len(summaries), base_id=base_id
    )


@tool(args_schema=ListRecordsInput)
@serialize_pydantic_return
async def list_records(
    api_key: str,
    base_id: str,
    table_name: str,
    max_records: int = 100,
    filter_formula: str | None = None,
    sort_field: str | None = None,
    sort_direction: str | None = "asc",
    view: str | None = None,
) -> ListRecordsOutput:
    """List records from an Airtable table with optional filter + sort."""
    if not api_key or not api_key.strip():
        return ListRecordsOutput(success=False, error=_empty_key_error("list_records"))
    if not base_id or not base_id.strip():
        return ListRecordsOutput(success=False, error="Base ID is required.")
    if not table_name or not table_name.strip():
        return ListRecordsOutput(success=False, error="Table name is required.")

    params: dict[str, Any] = {"maxRecords": min(max_records, 100)}
    if filter_formula:
        params["filterByFormula"] = filter_formula
    if sort_field:
        params["sort[0][field]"] = sort_field
        params["sort[0][direction]"] = sort_direction or "asc"
    if view:
        params["view"] = view

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/{base_id}/{table_name}",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListRecordsOutput(success=False, error=_api_error(response))
        body = response.json() or {}
    except Exception as exc:
        return ListRecordsOutput(success=False, error=f"list_records failed: {exc}")

    raw = body.get("records") or []
    records = [_to_record(r) for r in raw if isinstance(r, dict)]
    return ListRecordsOutput(
        success=True,
        records=records,
        count=len(records),
        table=table_name,
        base_id=base_id,
    )


@tool(args_schema=GetRecordInput)
@serialize_pydantic_return
async def get_record(
    api_key: str, base_id: str, table_name: str, record_id: str
) -> GetRecordOutput:
    """Get a single record by ID."""
    if not api_key or not api_key.strip():
        return GetRecordOutput(success=False, error=_empty_key_error("get_record"))
    if not (base_id and table_name and record_id):
        return GetRecordOutput(
            success=False,
            error="Base ID, table name, and record ID are all required.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/{base_id}/{table_name}/{record_id}",
                headers=_headers(api_key),
            )
        if response.status_code == 404:
            return GetRecordOutput(
                success=False,
                error=f"Record {record_id} not found in table {table_name}",
            )
        if response.status_code != 200:
            return GetRecordOutput(success=False, error=_api_error(response))
        body = response.json() or {}
    except Exception as exc:
        return GetRecordOutput(success=False, error=f"get_record failed: {exc}")

    return GetRecordOutput(success=True, record=_to_record(body))


@tool(args_schema=CreateRecordsInput)
@serialize_pydantic_return
async def create_records(
    api_key: str,
    base_id: str,
    table_name: str,
    records: list[dict[str, Any]],
    typecast: bool = False,
) -> CreateRecordsOutput:
    """Create records in an Airtable table (auto-batched at 10/req)."""
    if not api_key or not api_key.strip():
        return CreateRecordsOutput(
            success=False, error=_empty_key_error("create_records")
        )
    if not base_id or not table_name:
        return CreateRecordsOutput(
            success=False, error="Base ID and table name are required."
        )
    if not records:
        return CreateRecordsOutput(
            success=False, error="At least one record is required."
        )

    created: list[AirtableRecord] = []
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for i in range(0, len(records), _BATCH_SIZE):
                batch = records[i : i + _BATCH_SIZE]
                payload = {
                    "records": [{"fields": r} for r in batch],
                    "typecast": typecast,
                }
                response = await client.post(
                    f"{_BASE_URL}/{base_id}/{table_name}",
                    headers=_headers(api_key),
                    json=payload,
                )
                if response.status_code not in (200, 201):
                    return CreateRecordsOutput(
                        success=False,
                        error=_api_error(response),
                        records=created,
                        count=len(created),
                        table=table_name,
                        base_id=base_id,
                    )
                body = response.json() or {}
                for raw in body.get("records") or []:
                    if isinstance(raw, dict):
                        created.append(_to_record(raw))
    except Exception as exc:
        return CreateRecordsOutput(success=False, error=f"create_records failed: {exc}")

    return CreateRecordsOutput(
        success=True,
        records=created,
        count=len(created),
        table=table_name,
        base_id=base_id,
    )


def _normalize_update_record(record: dict[str, Any]) -> dict[str, Any]:
    """Accept both {'id', 'fields': {…}} and {'id', 'field_a': v, …}."""
    record_id = record.get("id")
    if "fields" in record:
        return {"id": record_id, "fields": record["fields"]}
    return {
        "id": record_id,
        "fields": {k: v for k, v in record.items() if k != "id"},
    }


@tool(args_schema=UpdateRecordsInput)
@serialize_pydantic_return
async def update_records(
    api_key: str,
    base_id: str,
    table_name: str,
    records: list[dict[str, Any]],
    typecast: bool = False,
) -> UpdateRecordsOutput:
    """Update records (PATCH semantics, auto-batched at 10/req)."""
    if not api_key or not api_key.strip():
        return UpdateRecordsOutput(
            success=False, error=_empty_key_error("update_records")
        )
    if not base_id or not table_name:
        return UpdateRecordsOutput(
            success=False, error="Base ID and table name are required."
        )
    if not records:
        return UpdateRecordsOutput(
            success=False, error="At least one record is required."
        )

    for idx, record in enumerate(records):
        if "id" not in record:
            return UpdateRecordsOutput(
                success=False,
                error=f"Record at index {idx} is missing required 'id' field.",
            )

    updated: list[AirtableRecord] = []
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for i in range(0, len(records), _BATCH_SIZE):
                batch = records[i : i + _BATCH_SIZE]
                payload = {
                    "records": [_normalize_update_record(r) for r in batch],
                    "typecast": typecast,
                }
                response = await client.patch(
                    f"{_BASE_URL}/{base_id}/{table_name}",
                    headers=_headers(api_key),
                    json=payload,
                )
                if response.status_code != 200:
                    return UpdateRecordsOutput(
                        success=False,
                        error=_api_error(response),
                        records=updated,
                        count=len(updated),
                        table=table_name,
                        base_id=base_id,
                        updated_count=len(updated),
                    )
                body = response.json() or {}
                for raw in body.get("records") or []:
                    if isinstance(raw, dict):
                        updated.append(_to_record(raw))
    except Exception as exc:
        return UpdateRecordsOutput(success=False, error=f"update_records failed: {exc}")

    return UpdateRecordsOutput(
        success=True,
        records=updated,
        count=len(updated),
        table=table_name,
        base_id=base_id,
    )


@tool(args_schema=DeleteRecordsInput)
@serialize_pydantic_return
async def delete_records(
    api_key: str,
    base_id: str,
    table_name: str,
    record_ids: list[str],
) -> DeleteRecordsOutput:
    """Delete records (auto-batched at 10/req, irreversible)."""
    if not api_key or not api_key.strip():
        return DeleteRecordsOutput(
            success=False, error=_empty_key_error("delete_records")
        )
    if not base_id or not table_name:
        return DeleteRecordsOutput(
            success=False, error="Base ID and table name are required."
        )
    if not record_ids:
        return DeleteRecordsOutput(
            success=False, error="At least one record ID is required."
        )

    deleted_ids: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for i in range(0, len(record_ids), _BATCH_SIZE):
                batch = record_ids[i : i + _BATCH_SIZE]
                # Airtable's batch-delete uses repeated `records[]=...` params.
                # httpx accepts list[tuple[str, str|int|...|None]]; widen str→Any
                # for the type to keep mypy happy without losing runtime fidelity.
                params: list[tuple[str, Any]] = [("records[]", rid) for rid in batch]
                response = await client.delete(
                    f"{_BASE_URL}/{base_id}/{table_name}",
                    headers=_headers(api_key),
                    params=params,
                )
                if response.status_code != 200:
                    return DeleteRecordsOutput(
                        success=False,
                        error=_api_error(response),
                        deleted_ids=deleted_ids,
                        count=len(deleted_ids),
                        table=table_name,
                        base_id=base_id,
                        deleted_count=len(deleted_ids),
                    )
                body = response.json() or {}
                for raw in body.get("records") or []:
                    if isinstance(raw, dict) and raw.get("deleted") and raw.get("id"):
                        deleted_ids.append(str(raw["id"]))
    except Exception as exc:
        return DeleteRecordsOutput(success=False, error=f"delete_records failed: {exc}")

    return DeleteRecordsOutput(
        success=True,
        deleted_ids=deleted_ids,
        count=len(deleted_ids),
        table=table_name,
        base_id=base_id,
    )
