"""Microsoft Power BI LangChain @tool functions."""
from __future__ import annotations

import asyncio
import base64
import json
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.microsoft_power_bi.outputs import (
    AddRowsToPushDatasetOutput,
    ExecuteDaxQueryOutput,
    ExportReportOutput,
    GetRefreshHistoryOutput,
    GetReportsByIdOutput,
    ListDashboardsOutput,
    ListDatasetsOutput,
    ListReportsOutput,
    ListWorkspacesOutput,
    RefreshDatasetOutput,
)

__all__ = [
    "add_rows_to_push_dataset",
    "execute_dax_query",
    "export_report",
    "get_refresh_history",
    "get_reports_by_id",
    "list_dashboards",
    "list_datasets",
    "list_reports",
    "list_workspaces",
    "refresh_dataset",
]

_BASE_URL = "https://api.powerbi.com/v1.0/myorg"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Power BI REST API."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _workspace_prefix(workspace_id: str | None) -> str:
    """Return the URL prefix for workspace-scoped or My-workspace requests."""
    if workspace_id:
        return f"{_BASE_URL}/groups/{workspace_id}"
    return _BASE_URL


# --- Input schemas --------------------------------------------------------


class AddRowsToPushDatasetInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    dataset_id: str = Field(description="ID of the Push Dataset")
    table_name: str = Field(description="Exact case-sensitive name of the table")
    rows: str = Field(description="JSON array of row objects matching the table column schema")
    workspace_id: str | None = Field(default=None, description="ID of the workspace (omit for My workspace)")


class ExecuteDaxQueryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    dataset_id: str = Field(description="ID of the dataset to query")
    query: str = Field(description="DAX expression starting with EVALUATE")
    workspace_id: str | None = Field(default=None, description="ID of the workspace (omit for My workspace)")
    include_nulls: bool = Field(default=True, description="Whether to include null values in the response")
    impersonated_user_name: str | None = Field(default=None, description="UPN of an effective identity for Row-Level Security")


class ExportReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    report_id: str = Field(description="ID of the report to export")
    format: str = Field(default="PDF", description="Output format: PDF, PPTX, PNG, CSV, XLSX, DOCX, XML, MHTML")
    workspace_id: str | None = Field(default=None, description="ID of the workspace (omit for My workspace)")
    poll_interval_seconds: int = Field(default=5, description="Seconds between export status polls")
    poll_timeout_seconds: int = Field(default=300, description="Maximum seconds to wait for export completion")


class GetRefreshHistoryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    dataset_id: str = Field(description="ID of the dataset")
    workspace_id: str | None = Field(default=None, description="ID of the workspace (omit for My workspace)")
    top: int | None = Field(default=None, description="Number of most recent refresh entries to return (max 200)")


class GetReportsByIdInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    report_id: str = Field(description="Power BI report ID (GUID)")
    group_id: str | None = Field(default=None, description="Workspace group ID (omit for My workspace)")


class ListDashboardsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    workspace_id: str | None = Field(default=None, description="ID of the workspace (omit for My workspace)")


class ListDatasetsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    workspace_id: str | None = Field(default=None, description="ID of the workspace (omit for My workspace)")


class ListReportsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    workspace_id: str | None = Field(default=None, description="ID of the workspace (omit for My workspace)")


class ListWorkspacesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class RefreshDatasetInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    dataset_id: str = Field(description="ID of the dataset to refresh")
    workspace_id: str | None = Field(default=None, description="ID of the workspace (omit for My workspace)")
    notify_option: str = Field(default="NoNotification", description="Email notification behavior: NoNotification, MailOnCompletion, MailOnFailure")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AddRowsToPushDatasetInput)
@serialize_pydantic_return
async def add_rows_to_push_dataset(
    auth_type: str,
    auth_data: dict[str, Any],
    dataset_id: str,
    table_name: str,
    rows: str,
    workspace_id: str | None = None,
) -> AddRowsToPushDatasetOutput:
    """Append rows to a table in a Power BI Push Dataset."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return AddRowsToPushDatasetOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    prefix = _workspace_prefix(workspace_id)
    url = f"{prefix}/datasets/{dataset_id}/tables/{table_name}/rows"

    try:
        parsed_rows = json.loads(rows) if isinstance(rows, str) else rows
    except (json.JSONDecodeError, TypeError) as exc:
        return AddRowsToPushDatasetOutput(
            success=False,
            error=f"Invalid JSON for rows: {exc}",
        )

    payload = {"rows": parsed_rows}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code not in (200, 202):
            return AddRowsToPushDatasetOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return AddRowsToPushDatasetOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddRowsToPushDatasetOutput(success=False, error=f"Call failed: {exc}")

    return AddRowsToPushDatasetOutput(
        success=True,
        rows_added=len(parsed_rows) if isinstance(parsed_rows, list) else None,
    )


@tool(args_schema=ExecuteDaxQueryInput)
@serialize_pydantic_return
async def execute_dax_query(
    auth_type: str,
    auth_data: dict[str, Any],
    dataset_id: str,
    query: str,
    workspace_id: str | None = None,
    include_nulls: bool = True,
    impersonated_user_name: str | None = None,
) -> ExecuteDaxQueryOutput:
    """Execute a DAX query against a Power BI dataset."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return ExecuteDaxQueryOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    prefix = _workspace_prefix(workspace_id)
    url = f"{prefix}/datasets/{dataset_id}/executeQueries"

    payload: dict[str, Any] = {
        "queries": [{"query": query}],
        "serializerSettings": {"includeNulls": include_nulls},
    }
    if impersonated_user_name:
        payload["impersonatedUserName"] = impersonated_user_name

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return ExecuteDaxQueryOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ExecuteDaxQueryOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ExecuteDaxQueryOutput(success=False, error=f"Call failed: {exc}")

    results = data.get("results", [])
    rows: list[dict[str, Any]] = []
    for result in results:
        for table in result.get("tables", []):
            rows.extend(table.get("rows", []))

    return ExecuteDaxQueryOutput(success=True, results=rows)


@tool(args_schema=ExportReportInput)
@serialize_pydantic_return
async def export_report(
    auth_type: str,
    auth_data: dict[str, Any],
    report_id: str,
    format: str = "PDF",
    workspace_id: str | None = None,
    poll_interval_seconds: int = 5,
    poll_timeout_seconds: int = 300,
) -> ExportReportOutput:
    """Export a Power BI report to PDF, PPTX, PNG, or other file format (Premium only)."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return ExportReportOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    prefix = _workspace_prefix(workspace_id)

    start_url = f"{prefix}/reports/{report_id}/ExportTo"
    payload: dict[str, Any] = {"format": format}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            start_resp = await client.post(start_url, headers=headers, json=payload)
        if start_resp.status_code not in (200, 202):
            return ExportReportOutput(
                success=False,
                error=f"Export start failed ({start_resp.status_code}): {start_resp.text}",
            )
        export_data = start_resp.json()
    except httpx.TimeoutException:
        return ExportReportOutput(success=False, error="Export start request timed out.")
    except Exception as exc:
        return ExportReportOutput(success=False, error=f"Export start failed: {exc}")

    export_id = export_data.get("id", "")
    poll_url = f"{prefix}/reports/{report_id}/exports/{export_id}"
    elapsed = 0

    while elapsed < poll_timeout_seconds:
        await asyncio.sleep(poll_interval_seconds)
        elapsed += poll_interval_seconds
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                poll_resp = await client.get(poll_url, headers=headers)
            if poll_resp.status_code != 200:
                return ExportReportOutput(
                    success=False,
                    error=f"Poll failed ({poll_resp.status_code}): {poll_resp.text}",
                )
            poll_data = poll_resp.json()
        except Exception as exc:
            return ExportReportOutput(success=False, error=f"Poll failed: {exc}")

        status = poll_data.get("status", "")
        percent = poll_data.get("percentComplete")

        if status == "Succeeded":
            file_url = f"{poll_url}/file"
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    file_resp = await client.get(file_url, headers=headers)
                if file_resp.status_code != 200:
                    return ExportReportOutput(
                        success=False,
                        error=f"File download failed ({file_resp.status_code})",
                    )
                file_b64 = base64.b64encode(file_resp.content).decode("utf-8")
            except Exception as exc:
                return ExportReportOutput(success=False, error=f"File download failed: {exc}")

            return ExportReportOutput(
                success=True,
                export_id=export_id,
                status="Succeeded",
                report_id=report_id,
                format=format,
                resource_file_extension=poll_data.get("resourceFileExtension"),
                resource_location=poll_data.get("resourceLocation"),
                file_size_bytes=len(file_resp.content),
                file_base64=file_b64,
                percent_complete=100,
            )

        if status == "Failed":
            return ExportReportOutput(
                success=False,
                error=f"Export failed: {poll_data.get('error', 'unknown error')}",
                export_id=export_id,
                status="Failed",
                report_id=report_id,
                percent_complete=percent,
            )

    return ExportReportOutput(
        success=False,
        error=f"Export timed out after {poll_timeout_seconds}s",
        export_id=export_id,
        status="Running",
        report_id=report_id,
        percent_complete=poll_data.get("percentComplete") if "poll_data" in dir() else None,
    )


@tool(args_schema=GetRefreshHistoryInput)
@serialize_pydantic_return
async def get_refresh_history(
    auth_type: str,
    auth_data: dict[str, Any],
    dataset_id: str,
    workspace_id: str | None = None,
    top: int | None = None,
) -> GetRefreshHistoryOutput:
    """Get the refresh history for a Power BI dataset."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return GetRefreshHistoryOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    prefix = _workspace_prefix(workspace_id)
    url = f"{prefix}/datasets/{dataset_id}/refreshes"
    params: dict[str, Any] = {}
    if top is not None:
        params["$top"] = top

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return GetRefreshHistoryOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetRefreshHistoryOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetRefreshHistoryOutput(success=False, error=f"Call failed: {exc}")

    return GetRefreshHistoryOutput(success=True, refreshes=data.get("value", []))


@tool(args_schema=GetReportsByIdInput)
@serialize_pydantic_return
async def get_reports_by_id(
    auth_type: str,
    auth_data: dict[str, Any],
    report_id: str,
    group_id: str | None = None,
) -> GetReportsByIdOutput:
    """Retrieve metadata for a single Power BI report by ID."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return GetReportsByIdOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    if group_id:
        url = f"{_BASE_URL}/groups/{group_id}/reports/{report_id}"
    else:
        url = f"{_BASE_URL}/reports/{report_id}"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return GetReportsByIdOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetReportsByIdOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetReportsByIdOutput(success=False, error=f"Call failed: {exc}")

    return GetReportsByIdOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        web_url=data.get("webUrl"),
        embed_url=data.get("embedUrl"),
        dataset_id=data.get("datasetId"),
        report_type=data.get("reportType"),
    )


@tool(args_schema=ListDashboardsInput)
@serialize_pydantic_return
async def list_dashboards(
    auth_type: str,
    auth_data: dict[str, Any],
    workspace_id: str | None = None,
) -> ListDashboardsOutput:
    """List Power BI dashboards in a workspace."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return ListDashboardsOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    prefix = _workspace_prefix(workspace_id)
    url = f"{prefix}/dashboards"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return ListDashboardsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListDashboardsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDashboardsOutput(success=False, error=f"Call failed: {exc}")

    return ListDashboardsOutput(success=True, dashboards=data.get("value", []))


@tool(args_schema=ListDatasetsInput)
@serialize_pydantic_return
async def list_datasets(
    auth_type: str,
    auth_data: dict[str, Any],
    workspace_id: str | None = None,
) -> ListDatasetsOutput:
    """List Power BI datasets (semantic models) in a workspace."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return ListDatasetsOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    prefix = _workspace_prefix(workspace_id)
    url = f"{prefix}/datasets"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return ListDatasetsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListDatasetsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDatasetsOutput(success=False, error=f"Call failed: {exc}")

    return ListDatasetsOutput(success=True, datasets=data.get("value", []))


@tool(args_schema=ListReportsInput)
@serialize_pydantic_return
async def list_reports(
    auth_type: str,
    auth_data: dict[str, Any],
    workspace_id: str | None = None,
) -> ListReportsOutput:
    """List Power BI reports in a workspace."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return ListReportsOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    prefix = _workspace_prefix(workspace_id)
    url = f"{prefix}/reports"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return ListReportsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListReportsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListReportsOutput(success=False, error=f"Call failed: {exc}")

    return ListReportsOutput(success=True, reports=data.get("value", []))


@tool(args_schema=ListWorkspacesInput)
@serialize_pydantic_return
async def list_workspaces(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListWorkspacesOutput:
    """List Power BI workspaces accessible to the authenticated user."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return ListWorkspacesOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    url = f"{_BASE_URL}/groups"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return ListWorkspacesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListWorkspacesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListWorkspacesOutput(success=False, error=f"Call failed: {exc}")

    return ListWorkspacesOutput(success=True, workspaces=data.get("value", []))


@tool(args_schema=RefreshDatasetInput)
@serialize_pydantic_return
async def refresh_dataset(
    auth_type: str,
    auth_data: dict[str, Any],
    dataset_id: str,
    workspace_id: str | None = None,
    notify_option: str = "NoNotification",
) -> RefreshDatasetOutput:
    """Trigger a refresh of a Power BI dataset."""
    access_token = auth_data.get("access_token")
    if not access_token or not access_token.strip():
        return RefreshDatasetOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    prefix = _workspace_prefix(workspace_id)
    url = f"{prefix}/datasets/{dataset_id}/refreshes"
    payload = {"notifyOption": notify_option}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code not in (200, 202):
            return RefreshDatasetOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return RefreshDatasetOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RefreshDatasetOutput(success=False, error=f"Call failed: {exc}")

    return RefreshDatasetOutput(
        success=True,
        status_code=response.status_code,
        request_id=response.headers.get("x-ms-request-id"),
        dataset_id=dataset_id,
        location=response.headers.get("Location"),
    )
