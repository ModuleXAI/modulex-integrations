"""ServiceNow LangChain ``@tool`` functions.

Token-based runtime convention: every tool's signature starts with
``auth_type: str, auth_data: dict[str, Any]``. ``auth_data`` carries
``instance_name`` (for URL construction) plus either ``access_token``
(oauth2) or ``token`` (bearer_token). The local ``_headers`` helper
accepts either key to support both auth schemas with one code path.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.servicenow.outputs import (
    CreateCaseOutput,
    CreateIncidentOutput,
    CreateTableRecordOutput,
    DeleteTableRecordOutput,
    GetTableRecordOutput,
    GetTableRecordsOutput,
    UpdateTableRecordOutput,
)

__all__ = [
    "create_case",
    "create_incident",
    "create_table_record",
    "delete_table_record",
    "get_table_record",
    "get_table_records",
    "update_table_record",
]

_TIMEOUT = 30.0
_TROUBLE_TICKET_PATH = "/api/sn_ind_tsm_sdwan/ticket/troubleTicket"


def _headers(auth_data: dict[str, Any]) -> dict[str, str]:
    token = auth_data.get("access_token") or auth_data.get("token") or ""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _base_url(auth_data: dict[str, Any]) -> str:
    instance = str(auth_data.get("instance_name", "")).strip()
    if instance.startswith("https://"):
        return instance.rstrip("/")
    if instance.endswith(".service-now.com"):
        return f"https://{instance}".rstrip("/")
    return f"https://{instance}.service-now.com"


def _credential_error(name: str) -> str | None:
    """Return an error string if auth_data is missing required fields."""
    return None  # validation happens via _validate below


def _validate(auth_data: dict[str, Any], name: str) -> str | None:
    token = auth_data.get("access_token") or auth_data.get("token")
    if not token:
        return (
            f"ServiceNow access token missing for {name}. "
            "Configure a valid credential."
        )
    if not auth_data.get("instance_name"):
        return (
            f"ServiceNow instance_name missing for {name}. "
            "Configure SERVICENOW_INSTANCE_NAME."
        )
    return None


def _api_path(api_version: str | None) -> str:
    """Build the optional `v1/` or `v2/` path prefix."""
    return f"{api_version}/" if api_version in ("v1", "v2") else ""


def _sysparms(
    *,
    display_value: str | None = None,
    exclude_reference_link: bool | None = None,
    fields: str | None = None,
    input_display_value: bool | None = None,
    view: str | None = None,
    query: str | None = None,
    suppress_pagination_header: bool | None = None,
    limit: int | None = None,
    query_category: str | None = None,
    query_no_domain: bool | None = None,
    no_count: bool | None = None,
) -> dict[str, Any]:
    """Translate snake_case tool args into the `sysparm_*` query string keys."""
    params: dict[str, Any] = {}
    if display_value:
        params["sysparm_display_value"] = display_value
    if exclude_reference_link:
        params["sysparm_exclude_reference_link"] = "true"
    if fields:
        params["sysparm_fields"] = fields
    if input_display_value:
        params["sysparm_input_display_value"] = "true"
    if view:
        params["sysparm_view"] = view
    if query:
        params["sysparm_query"] = query
    if suppress_pagination_header:
        params["sysparm_suppress_pagination_header"] = "true"
    if limit is not None:
        params["sysparm_limit"] = limit
    if query_category:
        params["sysparm_query_category"] = query_category
    if query_no_domain:
        params["sysparm_query_no_domain"] = "true"
    if no_count:
        params["sysparm_no_count"] = "true"
    return params


def _build_notes(
    work_note: str | None, comment: str | None
) -> list[dict[str, str]] | None:
    notes: list[dict[str, str]] = []
    if work_note:
        notes.append({"text": work_note, "@type": "work_notes"})
    if comment:
        notes.append({"text": comment, "@type": "comments"})
    return notes or None


def _build_related_parties(
    pairs: dict[str, str | None],
) -> list[dict[str, str]] | None:
    entries = [(k, v) for k, v in pairs.items() if v]
    if not entries:
        return None
    return [{"id": v, "@referredType": k} for k, v in entries]


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2 or bearer_token)")
    auth_data: dict[str, Any] = Field(
        description="Auth data carrying instance_name + access_token/token"
    )


class CreateCaseInput(_AuthFields):
    description: str = Field(description="Detailed description of the issue")
    severity: str = Field(description="'1' Critical | '2' High | '3' Moderate | '4' Low")
    name: str | None = Field(default=None, description="Short description")
    status: str | None = Field(default="New", description="Current status")
    channel_name: str | None = Field(default=None, description="Contact channel name")
    account_id: str | None = Field(default=None, description="Account sys_id")
    contact_id: str | None = Field(default=None, description="Contact sys_id")
    work_note: str | None = Field(default=None, description="Internal work note")
    comment: str | None = Field(default=None, description="Additional comment")


class CreateIncidentInput(_AuthFields):
    description: str = Field(description="Detailed description of the incident")
    severity: str = Field(
        description="'1' Critical | '2' High | '3' Moderate | '4' Low | '5' Planning"
    )
    name: str | None = Field(default=None, description="Short description")
    status: str | None = Field(default="New", description="Current status")
    contact_method: str | None = Field(default=None, description="Contact method name")
    company_id: str | None = Field(default=None, description="Company sys_id")
    user_id: str | None = Field(default=None, description="User sys_id")
    work_note: str | None = Field(default=None, description="Internal work note")
    comment: str | None = Field(default=None, description="Additional comment")


class CreateTableRecordInput(_AuthFields):
    table_name: str = Field(description="Table to insert into")
    table_record: dict[str, Any] = Field(description="Record field name/value pairs")
    api_version: str | None = Field(default=None, description="'v1', 'v2', or 'latest'")
    display_value: str | None = Field(default="false", description="Display vs actual")
    exclude_reference_link: bool | None = Field(default=False, description="Skip ref links")
    fields: str | None = Field(default=None, description="Comma-separated return fields")
    input_display_value: bool | None = Field(default=False, description="Inputs are display values")
    view: str | None = Field(default=None, description="UI view")


class GetTableRecordInput(_AuthFields):
    table_name: str = Field(description="Table containing the record")
    sys_id: str = Field(description="Sys_id of the record to retrieve")
    api_version: str | None = Field(default=None, description="'v1', 'v2', or 'latest'")
    display_value: str | None = Field(default="false", description="Display vs actual")
    exclude_reference_link: bool | None = Field(default=False, description="Skip ref links")
    fields: str | None = Field(default=None, description="Comma-separated return fields")
    view: str | None = Field(default=None, description="UI view")
    query_no_domain: bool | None = Field(default=False, description="Cross-domain access")


class GetTableRecordsInput(_AuthFields):
    table_name: str = Field(description="Table containing the records")
    api_version: str | None = Field(default=None, description="'v1', 'v2', or 'latest'")
    query: str | None = Field(default=None, description="Encoded query string filter")
    display_value: str | None = Field(default="false", description="Display vs actual")
    exclude_reference_link: bool | None = Field(default=False, description="Skip ref links")
    suppress_pagination_header: bool | None = Field(default=False, description="No paging hdr")
    fields: str | None = Field(default=None, description="Comma-separated return fields")
    limit: int | None = Field(default=None, description="Max results per page")
    view: str | None = Field(default=None, description="UI view")
    query_category: str | None = Field(default=None, description="Read-replica category")
    query_no_domain: bool | None = Field(default=False, description="Cross-domain access")
    no_count: bool | None = Field(default=False, description="Skip count(*)")


class UpdateTableRecordInput(_AuthFields):
    table_name: str = Field(description="Table containing the record")
    sys_id: str = Field(description="Sys_id of the record to update")
    update_fields: dict[str, Any] = Field(description="Fields to update (name/value)")
    api_version: str | None = Field(default=None, description="'v1', 'v2', or 'latest'")
    display_value: str | None = Field(default="false", description="Display vs actual")
    fields: str | None = Field(default=None, description="Comma-separated return fields")
    input_display_value: bool | None = Field(default=False, description="Inputs are display values")
    view: str | None = Field(default=None, description="UI view")
    query_no_domain: bool | None = Field(default=False, description="Cross-domain access")


class DeleteTableRecordInput(_AuthFields):
    table_name: str = Field(description="Table containing the record")
    sys_id: str = Field(description="Sys_id of the record to delete")
    api_version: str | None = Field(default=None, description="'v1', 'v2', or 'latest'")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=CreateCaseInput)
@serialize_pydantic_return
async def create_case(
    auth_type: str,
    auth_data: dict[str, Any],
    description: str,
    severity: str,
    name: str | None = None,
    status: str | None = "New",
    channel_name: str | None = None,
    account_id: str | None = None,
    contact_id: str | None = None,
    work_note: str | None = None,
    comment: str | None = None,
) -> CreateCaseOutput:
    """Create a new Case record (customer service management)."""
    err = _validate(auth_data, "create_case")
    if err:
        return CreateCaseOutput(success=False, error=err)

    body: dict[str, Any] = {
        "ticketType": "Case",
        "description": description,
        "severity": severity,
    }
    if name:
        body["name"] = name
    if status:
        body["status"] = status
    if channel_name:
        body["channel"] = {"name": channel_name}
    notes = _build_notes(work_note, comment)
    if notes:
        body["notes"] = notes
    parties = _build_related_parties(
        {"customer": account_id, "customer_contact": contact_id}
    )
    if parties:
        body["relatedParties"] = parties

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}{_TROUBLE_TICKET_PATH}",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateCaseOutput(
                success=False,
                error=f"API error {response.status_code}: {response.text}",
            )
        result = response.json()
    except Exception as exc:
        return CreateCaseOutput(success=False, error=f"create_case failed: {exc}")

    return CreateCaseOutput(success=True, result=result)


@tool(args_schema=CreateIncidentInput)
@serialize_pydantic_return
async def create_incident(
    auth_type: str,
    auth_data: dict[str, Any],
    description: str,
    severity: str,
    name: str | None = None,
    status: str | None = "New",
    contact_method: str | None = None,
    company_id: str | None = None,
    user_id: str | None = None,
    work_note: str | None = None,
    comment: str | None = None,
) -> CreateIncidentOutput:
    """Create a new Incident record (IT service management)."""
    err = _validate(auth_data, "create_incident")
    if err:
        return CreateIncidentOutput(success=False, error=err)

    body: dict[str, Any] = {
        "ticketType": "Incident",
        "description": description,
        "severity": severity,
    }
    if name:
        body["name"] = name
    if status:
        body["status"] = status
    if contact_method:
        body["channel"] = {"name": contact_method}
    notes = _build_notes(work_note, comment)
    if notes:
        body["notes"] = notes
    parties = _build_related_parties(
        {"customer": company_id, "customer_contact": user_id}
    )
    if parties:
        body["relatedParties"] = parties

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}{_TROUBLE_TICKET_PATH}",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateIncidentOutput(
                success=False,
                error=f"API error {response.status_code}: {response.text}",
            )
        result = response.json()
    except Exception as exc:
        return CreateIncidentOutput(
            success=False, error=f"create_incident failed: {exc}"
        )

    return CreateIncidentOutput(success=True, result=result)


@tool(args_schema=CreateTableRecordInput)
@serialize_pydantic_return
async def create_table_record(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    table_record: dict[str, Any],
    api_version: str | None = None,
    display_value: str | None = "false",
    exclude_reference_link: bool | None = False,
    fields: str | None = None,
    input_display_value: bool | None = False,
    view: str | None = None,
) -> CreateTableRecordOutput:
    """Create a new record in any ServiceNow table."""
    err = _validate(auth_data, "create_table_record")
    if err:
        return CreateTableRecordOutput(success=False, error=err)

    params = _sysparms(
        display_value=display_value,
        exclude_reference_link=exclude_reference_link,
        fields=fields,
        input_display_value=input_display_value,
        view=view,
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/now/{_api_path(api_version)}table/{table_name}",
                headers=_headers(auth_data),
                params=params or None,
                json=table_record,
            )
        if response.status_code not in (200, 201):
            return CreateTableRecordOutput(
                success=False,
                error=f"API error {response.status_code}: {response.text}",
            )
        body = response.json() or {}
    except Exception as exc:
        return CreateTableRecordOutput(
            success=False, error=f"create_table_record failed: {exc}"
        )

    return CreateTableRecordOutput(
        success=True,
        table=table_name,
        record=body.get("result") if isinstance(body.get("result"), dict) else body,
    )


@tool(args_schema=GetTableRecordInput)
@serialize_pydantic_return
async def get_table_record(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    sys_id: str,
    api_version: str | None = None,
    display_value: str | None = "false",
    exclude_reference_link: bool | None = False,
    fields: str | None = None,
    view: str | None = None,
    query_no_domain: bool | None = False,
) -> GetTableRecordOutput:
    """Get a specific record from a ServiceNow table by sys_id."""
    err = _validate(auth_data, "get_table_record")
    if err:
        return GetTableRecordOutput(success=False, error=err)

    params = _sysparms(
        display_value=display_value,
        exclude_reference_link=exclude_reference_link,
        fields=fields,
        view=view,
        query_no_domain=query_no_domain,
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/now/{_api_path(api_version)}table/{table_name}/{sys_id}",
                headers=_headers(auth_data),
                params=params or None,
            )
        if response.status_code == 404:
            return GetTableRecordOutput(
                success=False, error=f"Record not found: {table_name}/{sys_id}"
            )
        if response.status_code != 200:
            return GetTableRecordOutput(
                success=False,
                error=f"API error {response.status_code}: {response.text}",
            )
        body = response.json() or {}
    except Exception as exc:
        return GetTableRecordOutput(
            success=False, error=f"get_table_record failed: {exc}"
        )

    return GetTableRecordOutput(
        success=True,
        table=table_name,
        sys_id=sys_id,
        record=body.get("result") if isinstance(body.get("result"), dict) else body,
    )


@tool(args_schema=GetTableRecordsInput)
@serialize_pydantic_return
async def get_table_records(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    api_version: str | None = None,
    query: str | None = None,
    display_value: str | None = "false",
    exclude_reference_link: bool | None = False,
    suppress_pagination_header: bool | None = False,
    fields: str | None = None,
    limit: int | None = None,
    view: str | None = None,
    query_category: str | None = None,
    query_no_domain: bool | None = False,
    no_count: bool | None = False,
) -> GetTableRecordsOutput:
    """List records from a ServiceNow table with optional filters."""
    err = _validate(auth_data, "get_table_records")
    if err:
        return GetTableRecordsOutput(success=False, error=err)

    params = _sysparms(
        display_value=display_value,
        exclude_reference_link=exclude_reference_link,
        fields=fields,
        view=view,
        query=query,
        suppress_pagination_header=suppress_pagination_header,
        limit=limit,
        query_category=query_category,
        query_no_domain=query_no_domain,
        no_count=no_count,
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/now/{_api_path(api_version)}table/{table_name}",
                headers=_headers(auth_data),
                params=params or None,
            )
        if response.status_code != 200:
            return GetTableRecordsOutput(
                success=False,
                error=f"API error {response.status_code}: {response.text}",
            )
        body = response.json() or {}
    except Exception as exc:
        return GetTableRecordsOutput(
            success=False, error=f"get_table_records failed: {exc}"
        )

    raw = body.get("result")
    records = raw if isinstance(raw, list) else []
    return GetTableRecordsOutput(
        success=True, table=table_name, records=records, count=len(records)
    )


@tool(args_schema=UpdateTableRecordInput)
@serialize_pydantic_return
async def update_table_record(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    sys_id: str,
    update_fields: dict[str, Any],
    api_version: str | None = None,
    display_value: str | None = "false",
    fields: str | None = None,
    input_display_value: bool | None = False,
    view: str | None = None,
    query_no_domain: bool | None = False,
) -> UpdateTableRecordOutput:
    """Update a ServiceNow table record (PATCH semantics)."""
    err = _validate(auth_data, "update_table_record")
    if err:
        return UpdateTableRecordOutput(success=False, error=err)

    params = _sysparms(
        display_value=display_value,
        fields=fields,
        input_display_value=input_display_value,
        view=view,
        query_no_domain=query_no_domain,
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_base_url(auth_data)}/api/now/{_api_path(api_version)}table/{table_name}/{sys_id}",
                headers=_headers(auth_data),
                params=params or None,
                json=update_fields,
            )
        if response.status_code != 200:
            return UpdateTableRecordOutput(
                success=False,
                error=f"API error {response.status_code}: {response.text}",
            )
        body = response.json() or {}
    except Exception as exc:
        return UpdateTableRecordOutput(
            success=False, error=f"update_table_record failed: {exc}"
        )

    return UpdateTableRecordOutput(
        success=True,
        table=table_name,
        sys_id=sys_id,
        record=body.get("result") if isinstance(body.get("result"), dict) else body,
    )


@tool(args_schema=DeleteTableRecordInput)
@serialize_pydantic_return
async def delete_table_record(
    auth_type: str,
    auth_data: dict[str, Any],
    table_name: str,
    sys_id: str,
    api_version: str | None = None,
) -> DeleteTableRecordOutput:
    """Delete a ServiceNow table record (irreversible)."""
    err = _validate(auth_data, "delete_table_record")
    if err:
        return DeleteTableRecordOutput(success=False, error=err)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_base_url(auth_data)}/api/now/{_api_path(api_version)}table/{table_name}/{sys_id}",
                headers=_headers(auth_data),
            )
        # Successful delete is 204 (or 200 from older versions).
        if response.status_code not in (200, 204):
            return DeleteTableRecordOutput(
                success=False,
                error=f"API error {response.status_code}: {response.text}",
            )
    except Exception as exc:
        return DeleteTableRecordOutput(
            success=False, error=f"delete_table_record failed: {exc}"
        )

    return DeleteTableRecordOutput(success=True, table=table_name, sys_id=sys_id)
