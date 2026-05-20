"""Databricks LangChain @tool functions."""
from __future__ import annotations

import json
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.databricks.outputs import (
    CancelAllRunsOutput,
    CancelRunOutput,
    CreateEndpointOutput,
    CreateJobOutput,
    CreateSqlWarehouseOutput,
    CreateVectorSearchIndexOutput,
    DeleteEndpointOutput,
    DeleteJobOutput,
    DeleteRunOutput,
    DeleteSqlWarehouseOutput,
    DeleteVectorSearchIndexDataOutput,
    DeleteVectorSearchIndexOutput,
    EditSqlWarehouseOutput,
    ExportRunOutput,
    GetEndpointOutput,
    GetJobOutput,
    GetJobPermissionsOutput,
    GetRunOutput,
    GetRunOutputOutput,
    GetSqlWarehouseConfigOutput,
    GetSqlWarehouseOutput,
    GetSqlWarehousePermissionsOutput,
    GetVectorSearchIndexOutput,
    ListEndpointsOutput,
    ListJobsOutput,
    ListRunsOutput,
    ListSqlWarehousesOutput,
    ListVectorSearchIndexesOutput,
    QueryVectorSearchIndexOutput,
    RepairRunOutput,
    ResetJobOutput,
    RunJobNowOutput,
    ScanVectorSearchIndexOutput,
    SetJobPermissionsOutput,
    SetSqlWarehouseConfigOutput,
    SetSqlWarehousePermissionsOutput,
    StartSqlWarehouseOutput,
    StopSqlWarehouseOutput,
    SyncVectorSearchIndexOutput,
    UpdateJobOutput,
    UpsertVectorSearchIndexDataOutput,
)

__all__ = [
    "cancel_all_runs",
    "cancel_run",
    "create_endpoint",
    "create_job",
    "create_sql_warehouse",
    "create_vector_search_index",
    "delete_endpoint",
    "delete_job",
    "delete_run",
    "delete_sql_warehouse",
    "delete_vector_search_index",
    "delete_vector_search_index_data",
    "edit_sql_warehouse",
    "export_run",
    "get_endpoint",
    "get_job",
    "get_job_permissions",
    "get_run",
    "get_run_output",
    "get_sql_warehouse",
    "get_sql_warehouse_config",
    "get_sql_warehouse_permissions",
    "get_vector_search_index",
    "list_endpoints",
    "list_jobs",
    "list_runs",
    "list_sql_warehouses",
    "list_vector_search_indexes",
    "query_vector_search_index",
    "repair_run",
    "reset_job",
    "run_job_now",
    "scan_vector_search_index",
    "set_job_permissions",
    "set_sql_warehouse_config",
    "set_sql_warehouse_permissions",
    "start_sql_warehouse",
    "stop_sql_warehouse",
    "sync_vector_search_index",
    "update_job",
    "upsert_vector_search_index_data",
]

_TIMEOUT = 30.0


def _base_url(auth_data: dict[str, Any]) -> str:
    domain = auth_data.get("domain", "")
    return f"https://{domain}.cloud.databricks.com"


def _headers(auth_data: dict[str, Any]) -> dict[str, str]:
    token = auth_data.get("access_token", "")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _parse_json(value: str | None) -> Any:
    if not value:
        return None
    return json.loads(value)


# --- Input schemas ------------------------------------------------------------


class CancelAllRunsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    job_id: str | None = Field(default=None, description="Identifier of a job.")
    all_queued_runs: bool | None = Field(default=None, description="Cancel all queued runs.")


class CancelRunInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    run_id: str = Field(description="Identifier of the run to cancel.")


class CreateEndpointInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="The name of the vector search endpoint to create.")


class CreateJobInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    tasks: str = Field(description="JSON string of task specifications for this job.")
    name: str | None = Field(default=None, description="An optional name for the job.")
    tags: str | None = Field(default=None, description="JSON string of tags.")
    job_clusters: str | None = Field(default=None, description="JSON string of job cluster specifications.")
    email_notifications: str | None = Field(default=None, description="JSON string of email notification settings.")
    webhook_notifications: str | None = Field(default=None, description="JSON string of webhook notification settings.")
    timeout_seconds: int | None = Field(default=None, description="Timeout in seconds.")
    schedule: str | None = Field(default=None, description="JSON string of schedule definition.")
    max_concurrent_runs: int | None = Field(default=None, description="Maximum number of concurrent runs.")
    git_source: str | None = Field(default=None, description="JSON string specifying a remote Git repository.")
    access_control_list: str | None = Field(default=None, description="JSON string of permissions.")


class CreateSqlWarehouseInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="A human-readable name for the warehouse.")
    cluster_size: str = Field(description="Size of the cluster.")
    auto_stop_minutes: int = Field(default=10, description="Minutes of inactivity before auto-stop.")
    min_num_clusters: int = Field(default=1, description="Minimum number of clusters.")
    max_num_clusters: int = Field(default=1, description="Maximum number of clusters.")
    enable_photon: bool | None = Field(default=None, description="Use Photon optimized clusters.")
    enable_serverless_compute: bool | None = Field(default=None, description="Use serverless compute.")
    warehouse_type: str | None = Field(default=None, description="Warehouse type.")
    spot_instance_policy: str | None = Field(default=None, description="Spot instance policy.")
    channel: str | None = Field(default=None, description="JSON string of channel details.")
    tags: str | None = Field(default=None, description="JSON string of custom key-value tags.")


class CreateVectorSearchIndexInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="A unique name for the index.")
    endpoint_name: str = Field(description="The name of the vector search endpoint.")
    index_type: str = Field(description="Type of index: DELTA_SYNC or DIRECT_ACCESS.")
    primary_key: str = Field(description="The primary key column.")
    source_table: str | None = Field(default=None, description="The Delta table backing the index.")
    columns_to_sync: str | None = Field(default=None, description="JSON array of column names to sync.")
    embedding_source_columns: str | None = Field(default=None, description="JSON array of embedding source configs.")
    schema_json: str | None = Field(default=None, description="Schema in JSON format for DIRECT_ACCESS.")  # type: ignore[assignment]
    pipeline_type: str = Field(default="TRIGGERED", description="Pipeline type: TRIGGERED or CONTINUOUS.")


class DeleteEndpointInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    endpoint_name: str = Field(description="The name of the endpoint to delete.")


class DeleteJobInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    job_id: str = Field(description="Identifier of the job to delete.")


class DeleteRunInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    run_id: str = Field(description="Identifier of the run to delete.")


class DeleteSqlWarehouseInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    warehouse_id: str = Field(description="The ID of the SQL Warehouse to delete.")


class DeleteVectorSearchIndexInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    index_name: str = Field(description="The name of the vector search index to delete.")


class DeleteVectorSearchIndexDataInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    index_name: str = Field(description="The name of the vector search index.")
    primary_keys: str = Field(description="JSON array of primary key values to delete.")


class EditSqlWarehouseInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    warehouse_id: str = Field(description="The ID of the SQL Warehouse to edit.")
    name: str | None = Field(default=None, description="New logical name.")
    cluster_size: str | None = Field(default=None, description="Size of clusters.")
    auto_stop_mins: int | None = Field(default=None, description="Minutes of inactivity before auto-stop.")
    min_num_clusters: int | None = Field(default=None, description="Minimum number of clusters.")
    max_num_clusters: int | None = Field(default=None, description="Maximum number of clusters.")
    enable_photon: bool | None = Field(default=None, description="Use Photon optimized clusters.")
    enable_serverless_compute: bool | None = Field(default=None, description="Use serverless compute.")
    warehouse_type: str | None = Field(default=None, description="Warehouse type.")
    spot_instance_policy: str | None = Field(default=None, description="Spot instance policy.")
    tags: str | None = Field(default=None, description="JSON string of custom key-value tags.")
    channel: str | None = Field(default=None, description="JSON string of channel details.")


class ExportRunInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    run_id: str = Field(description="Identifier of the run to export.")
    views_to_export: str | None = Field(default=None, description="Views to export: CODE, DASHBOARDS, or ALL.")


class GetEndpointInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    endpoint_name: str = Field(description="The name of the vector search endpoint.")


class GetJobInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    job_id: str = Field(description="Identifier of the job.")


class GetJobPermissionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    job_id: str = Field(description="Identifier of the job.")


class GetRunInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    run_id: str = Field(description="Identifier of the run.")
    include_history: bool | None = Field(default=None, description="Include repair history.")
    include_resolved_values: bool | None = Field(default=None, description="Include resolved parameter values.")


class GetRunOutputInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    run_id: str = Field(description="Identifier of the run.")


class GetSqlWarehouseInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    warehouse_id: str = Field(description="The ID of the SQL Warehouse.")


class GetSqlWarehouseConfigInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class GetSqlWarehousePermissionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    warehouse_id: str = Field(description="The ID of the SQL Warehouse.")


class GetVectorSearchIndexInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    index_name: str = Field(description="The name of the vector search index.")


class ListEndpointsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    max_results: int = Field(default=100, description="Maximum number of endpoints to return.")


class ListJobsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    expand_tasks: bool | None = Field(default=None, description="Include task and cluster details.")
    name: str | None = Field(default=None, description="Optional name to filter on.")
    max_requests: int | None = Field(default=None, description="Max API page requests (1-10).")


class ListRunsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    job_id: str | None = Field(default=None, description="Identifier of a job to filter runs.")
    active_only: bool | None = Field(default=None, description="Return only active runs.")
    max_results: int = Field(default=100, description="Maximum number of runs to return.")


class ListSqlWarehousesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class ListVectorSearchIndexesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    endpoint_name: str = Field(description="The name of the vector search endpoint.")


class QueryVectorSearchIndexInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    index_name: str = Field(description="The name of the vector search index.")
    columns: str = Field(description="JSON array of column names to include in the response.")
    query_text: str | None = Field(default=None, description="Free-text query for semantic search.")
    query_vector: str | None = Field(default=None, description="JSON array of floats for embedding vector.")
    filters_json: str | None = Field(default=None, description="JSON string of query filters.")
    num_results: int = Field(default=10, description="Number of results to return.")
    include_embeddings: bool | None = Field(default=None, description="Include embedding vectors.")


class RepairRunInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    run_id: str = Field(description="Identifier of the run to repair.")
    rerun_tasks: str | None = Field(default=None, description="JSON array of task keys to repair.")
    rerun_all_failed_tasks: bool | None = Field(default=None, description="Repair all failed tasks.")
    pipeline_params_full_refresh: bool | None = Field(default=None, description="Perform a full refresh.")


class ResetJobInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    job_id: str = Field(description="Identifier of the job.")
    new_settings: str = Field(description="JSON string of new job settings.")


class RunJobNowInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    job_id: str = Field(description="Identifier of the job to run.")
    jar_params: str | None = Field(default=None, description="JSON array of JAR task parameters.")
    notebook_params: str | None = Field(default=None, description="JSON object for notebook tasks.")
    python_params: str | None = Field(default=None, description="JSON array for Python tasks.")
    spark_submit_params: str | None = Field(default=None, description="JSON array for spark submit tasks.")


class ScanVectorSearchIndexInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    index_name: str = Field(description="The name of the vector search index.")
    last_primary_key: str | None = Field(default=None, description="Primary key of the last entry from previous scan.")
    num_results: int = Field(default=10, description="Number of results to return.")


class SetJobPermissionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    job_id: str = Field(description="Identifier of the job.")
    access_control_list: str = Field(description="JSON string of permission objects.")


class SetSqlWarehouseConfigInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    instance_profile_arn: str | None = Field(default=None, description="Instance profile ARN (AWS).")
    google_service_account: str | None = Field(default=None, description="Service account email (GCP).")
    security_policy: str | None = Field(default=None, description="Security policy: NONE or DATA_ACCESS_CONTROL.")
    channel: str | None = Field(default=None, description="JSON string of channel details.")
    enabled_warehouse_types: str | None = Field(default=None, description="JSON array of enabled warehouse types.")
    config_param: str | None = Field(default=None, description="JSON array of config key/value pairs.")
    global_param: str | None = Field(default=None, description="JSON array of global parameter pairs.")


class SetSqlWarehousePermissionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    warehouse_id: str = Field(description="The ID of the SQL Warehouse.")
    access_control_list: str = Field(description="JSON string of access control entries.")


class StartSqlWarehouseInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    warehouse_id: str = Field(description="The ID of the SQL Warehouse to start.")


class StopSqlWarehouseInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    warehouse_id: str = Field(description="The ID of the SQL Warehouse to stop.")


class SyncVectorSearchIndexInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    index_name: str = Field(description="The name of the vector search index to synchronize.")


class UpdateJobInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    job_id: str = Field(description="Identifier of the job to update.")
    new_settings: str = Field(description="JSON string of updated job settings.")
    fields_to_remove: str | None = Field(default=None, description="JSON array of field paths to remove.")


class UpsertVectorSearchIndexDataInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    index_name: str = Field(description="The name of the vector search index.")
    inputs_json: str = Field(description="JSON array of row objects to upsert.")


# --- @tool functions ----------------------------------------------------------


@tool(args_schema=CancelAllRunsInput)
@serialize_pydantic_return
async def cancel_all_runs(
    auth_type: str,
    auth_data: dict[str, Any],
    job_id: str | None = None,
    all_queued_runs: bool | None = None,
) -> CancelAllRunsOutput:
    """Cancel all active runs for a job."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return CancelAllRunsOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {}
        if job_id:
            body["job_id"] = job_id
        if all_queued_runs is not None:
            body["all_queued_runs"] = all_queued_runs
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.2/jobs/runs/cancel-all",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return CancelAllRunsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return CancelAllRunsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CancelAllRunsOutput(success=False, error=f"Call failed: {exc}")
    return CancelAllRunsOutput(success=True)


@tool(args_schema=CancelRunInput)
@serialize_pydantic_return
async def cancel_run(
    auth_type: str,
    auth_data: dict[str, Any],
    run_id: str,
) -> CancelRunOutput:
    """Cancel a job run. The run is canceled asynchronously."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return CancelRunOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.2/jobs/runs/cancel",
                headers=_headers(auth_data),
                json={"run_id": run_id},
            )
        if response.status_code != 200:
            return CancelRunOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return CancelRunOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CancelRunOutput(success=False, error=f"Call failed: {exc}")
    return CancelRunOutput(success=True)


@tool(args_schema=CreateEndpointInput)
@serialize_pydantic_return
async def create_endpoint(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
) -> CreateEndpointOutput:
    """Create a new vector search endpoint."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return CreateEndpointOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.0/vector-search/endpoints",
                headers=_headers(auth_data),
                json={"name": name, "endpoint_type": "STANDARD"},
            )
        if response.status_code != 200:
            return CreateEndpointOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateEndpointOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateEndpointOutput(success=False, error=f"Call failed: {exc}")
    return CreateEndpointOutput(success=True, data=data)


@tool(args_schema=CreateJobInput)
@serialize_pydantic_return
async def create_job(
    auth_type: str,
    auth_data: dict[str, Any],
    tasks: str,
    name: str | None = None,
    tags: str | None = None,
    job_clusters: str | None = None,
    email_notifications: str | None = None,
    webhook_notifications: str | None = None,
    timeout_seconds: int | None = None,
    schedule: str | None = None,
    max_concurrent_runs: int | None = None,
    git_source: str | None = None,
    access_control_list: str | None = None,
) -> CreateJobOutput:
    """Create a new Databricks job."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return CreateJobOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {"tasks": _parse_json(tasks)}
        if name:
            body["name"] = name
        if tags:
            body["tags"] = _parse_json(tags)
        if job_clusters:
            body["job_clusters"] = _parse_json(job_clusters)
        if email_notifications:
            body["email_notifications"] = _parse_json(email_notifications)
        if webhook_notifications:
            body["webhook_notifications"] = _parse_json(webhook_notifications)
        if timeout_seconds is not None:
            body["timeout_seconds"] = timeout_seconds
        if schedule:
            body["schedule"] = _parse_json(schedule)
        if max_concurrent_runs is not None:
            body["max_concurrent_runs"] = max_concurrent_runs
        if git_source:
            body["git_source"] = _parse_json(git_source)
        if access_control_list:
            body["access_control_list"] = _parse_json(access_control_list)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.2/jobs/create",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return CreateJobOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateJobOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateJobOutput(success=False, error=f"Call failed: {exc}")
    return CreateJobOutput(success=True, job_id=str(data.get("job_id", "")))


@tool(args_schema=CreateSqlWarehouseInput)
@serialize_pydantic_return
async def create_sql_warehouse(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    cluster_size: str,
    auto_stop_minutes: int = 10,
    min_num_clusters: int = 1,
    max_num_clusters: int = 1,
    enable_photon: bool | None = None,
    enable_serverless_compute: bool | None = None,
    warehouse_type: str | None = None,
    spot_instance_policy: str | None = None,
    channel: str | None = None,
    tags: str | None = None,
) -> CreateSqlWarehouseOutput:
    """Create a new SQL Warehouse in Databricks."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return CreateSqlWarehouseOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {
            "name": name,
            "cluster_size": cluster_size,
            "auto_stop_mins": auto_stop_minutes,
            "min_num_clusters": min_num_clusters,
            "max_num_clusters": max_num_clusters,
        }
        if enable_photon is not None:
            body["enable_photon"] = enable_photon
        if enable_serverless_compute is not None:
            body["enable_serverless_compute"] = enable_serverless_compute
        if warehouse_type:
            body["warehouse_type"] = warehouse_type
        if spot_instance_policy:
            body["spot_instance_policy"] = spot_instance_policy
        if channel:
            body["channel"] = _parse_json(channel)
        if tags:
            body["tags"] = {"custom_tags": [{"key": k, "value": v} for k, v in _parse_json(tags).items()]}
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.0/sql/warehouses",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return CreateSqlWarehouseOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateSqlWarehouseOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateSqlWarehouseOutput(success=False, error=f"Call failed: {exc}")
    return CreateSqlWarehouseOutput(success=True, data=data)


@tool(args_schema=CreateVectorSearchIndexInput)
@serialize_pydantic_return
async def create_vector_search_index(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    endpoint_name: str,
    index_type: str,
    primary_key: str,
    source_table: str | None = None,
    columns_to_sync: str | None = None,
    embedding_source_columns: str | None = None,
    schema_json: str | None = None,
    pipeline_type: str = "TRIGGERED",
) -> CreateVectorSearchIndexOutput:
    """Create a new vector search index in Databricks."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return CreateVectorSearchIndexOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {
            "name": name,
            "endpoint_name": endpoint_name,
            "index_type": index_type,
            "primary_key": primary_key,
        }
        if index_type == "DELTA_SYNC":
            delta_sync: dict[str, Any] = {"pipeline_type": pipeline_type}
            if source_table:
                delta_sync["source_table"] = source_table
            if columns_to_sync:
                delta_sync["columns_to_sync"] = _parse_json(columns_to_sync)
            if embedding_source_columns:
                delta_sync["embedding_source_columns"] = _parse_json(embedding_source_columns)
            body["delta_sync_index_spec"] = delta_sync
        elif index_type == "DIRECT_ACCESS":
            direct: dict[str, Any] = {}
            if schema_json:
                direct["schema_json"] = schema_json
            if embedding_source_columns:
                direct["embedding_source_columns"] = _parse_json(embedding_source_columns)
            body["direct_access_index_spec"] = direct
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.0/vector-search/indexes",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return CreateVectorSearchIndexOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateVectorSearchIndexOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateVectorSearchIndexOutput(success=False, error=f"Call failed: {exc}")
    return CreateVectorSearchIndexOutput(success=True, data=data)


@tool(args_schema=DeleteEndpointInput)
@serialize_pydantic_return
async def delete_endpoint(
    auth_type: str,
    auth_data: dict[str, Any],
    endpoint_name: str,
) -> DeleteEndpointOutput:
    """Delete a vector search endpoint."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return DeleteEndpointOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_base_url(auth_data)}/api/2.0/vector-search/endpoints/{endpoint_name}",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return DeleteEndpointOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return DeleteEndpointOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteEndpointOutput(success=False, error=f"Call failed: {exc}")
    return DeleteEndpointOutput(success=True)


@tool(args_schema=DeleteJobInput)
@serialize_pydantic_return
async def delete_job(
    auth_type: str,
    auth_data: dict[str, Any],
    job_id: str,
) -> DeleteJobOutput:
    """Delete a job. Deleted jobs cannot be recovered."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return DeleteJobOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.2/jobs/delete",
                headers=_headers(auth_data),
                json={"job_id": job_id},
            )
        if response.status_code != 200:
            return DeleteJobOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return DeleteJobOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteJobOutput(success=False, error=f"Call failed: {exc}")
    return DeleteJobOutput(success=True)


@tool(args_schema=DeleteRunInput)
@serialize_pydantic_return
async def delete_run(
    auth_type: str,
    auth_data: dict[str, Any],
    run_id: str,
) -> DeleteRunOutput:
    """Delete a non-active run. Returns an error if the run is active."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return DeleteRunOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.2/jobs/runs/delete",
                headers=_headers(auth_data),
                json={"run_id": run_id},
            )
        if response.status_code != 200:
            return DeleteRunOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return DeleteRunOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteRunOutput(success=False, error=f"Call failed: {exc}")
    return DeleteRunOutput(success=True)


@tool(args_schema=DeleteSqlWarehouseInput)
@serialize_pydantic_return
async def delete_sql_warehouse(
    auth_type: str,
    auth_data: dict[str, Any],
    warehouse_id: str,
) -> DeleteSqlWarehouseOutput:
    """Delete a SQL Warehouse by ID."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return DeleteSqlWarehouseOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_base_url(auth_data)}/api/2.0/sql/warehouses/{warehouse_id}",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return DeleteSqlWarehouseOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return DeleteSqlWarehouseOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteSqlWarehouseOutput(success=False, error=f"Call failed: {exc}")
    return DeleteSqlWarehouseOutput(success=True)


@tool(args_schema=DeleteVectorSearchIndexInput)
@serialize_pydantic_return
async def delete_vector_search_index(
    auth_type: str,
    auth_data: dict[str, Any],
    index_name: str,
) -> DeleteVectorSearchIndexOutput:
    """Delete a vector search index."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return DeleteVectorSearchIndexOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_base_url(auth_data)}/api/2.0/vector-search/indexes/{index_name}",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return DeleteVectorSearchIndexOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return DeleteVectorSearchIndexOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteVectorSearchIndexOutput(success=False, error=f"Call failed: {exc}")
    return DeleteVectorSearchIndexOutput(success=True)


@tool(args_schema=DeleteVectorSearchIndexDataInput)
@serialize_pydantic_return
async def delete_vector_search_index_data(
    auth_type: str,
    auth_data: dict[str, Any],
    index_name: str,
    primary_keys: str,
) -> DeleteVectorSearchIndexDataOutput:
    """Delete rows from a Direct Access vector index by primary-key values."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return DeleteVectorSearchIndexDataOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        keys = _parse_json(primary_keys)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                "DELETE",
                f"{_base_url(auth_data)}/api/2.0/vector-search/indexes/{index_name}/delete-data",
                headers=_headers(auth_data),
                params={"primary_keys": keys} if isinstance(keys, list) else {},
            )
        if response.status_code != 200:
            return DeleteVectorSearchIndexDataOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return DeleteVectorSearchIndexDataOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteVectorSearchIndexDataOutput(success=False, error=f"Call failed: {exc}")
    return DeleteVectorSearchIndexDataOutput(success=True, data=data)


@tool(args_schema=EditSqlWarehouseInput)
@serialize_pydantic_return
async def edit_sql_warehouse(
    auth_type: str,
    auth_data: dict[str, Any],
    warehouse_id: str,
    name: str | None = None,
    cluster_size: str | None = None,
    auto_stop_mins: int | None = None,
    min_num_clusters: int | None = None,
    max_num_clusters: int | None = None,
    enable_photon: bool | None = None,
    enable_serverless_compute: bool | None = None,
    warehouse_type: str | None = None,
    spot_instance_policy: str | None = None,
    tags: str | None = None,
    channel: str | None = None,
) -> EditSqlWarehouseOutput:
    """Edit the configuration of an existing SQL Warehouse."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return EditSqlWarehouseOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {}
        if name:
            body["name"] = name
        if cluster_size:
            body["cluster_size"] = cluster_size
        if auto_stop_mins is not None:
            body["auto_stop_mins"] = auto_stop_mins
        if min_num_clusters is not None:
            body["min_num_clusters"] = min_num_clusters
        if max_num_clusters is not None:
            body["max_num_clusters"] = max_num_clusters
        if enable_photon is not None:
            body["enable_photon"] = enable_photon
        if enable_serverless_compute is not None:
            body["enable_serverless_compute"] = enable_serverless_compute
        if warehouse_type:
            body["warehouse_type"] = warehouse_type
        if spot_instance_policy:
            body["spot_instance_policy"] = spot_instance_policy
        if tags:
            body["tags"] = {"custom_tags": [{"key": k, "value": v} for k, v in _parse_json(tags).items()]}
        if channel:
            body["channel"] = _parse_json(channel)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.0/sql/warehouses/{warehouse_id}/edit",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return EditSqlWarehouseOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json() if response.text else {}
    except httpx.TimeoutException:
        return EditSqlWarehouseOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return EditSqlWarehouseOutput(success=False, error=f"Call failed: {exc}")
    return EditSqlWarehouseOutput(success=True, data=data)


@tool(args_schema=ExportRunInput)
@serialize_pydantic_return
async def export_run(
    auth_type: str,
    auth_data: dict[str, Any],
    run_id: str,
    views_to_export: str | None = None,
) -> ExportRunOutput:
    """Export and retrieve the job run task."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return ExportRunOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        params: dict[str, Any] = {"run_id": run_id}
        if views_to_export:
            params["views_to_export"] = views_to_export
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/2.2/jobs/runs/export",
                headers=_headers(auth_data),
                params=params,
            )
        if response.status_code != 200:
            return ExportRunOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ExportRunOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ExportRunOutput(success=False, error=f"Call failed: {exc}")
    return ExportRunOutput(success=True, data=data)


@tool(args_schema=GetEndpointInput)
@serialize_pydantic_return
async def get_endpoint(
    auth_type: str,
    auth_data: dict[str, Any],
    endpoint_name: str,
) -> GetEndpointOutput:
    """Get details of a specific vector search endpoint."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return GetEndpointOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/2.0/vector-search/endpoints/{endpoint_name}",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return GetEndpointOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetEndpointOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetEndpointOutput(success=False, error=f"Call failed: {exc}")
    return GetEndpointOutput(success=True, data=data)


@tool(args_schema=GetJobInput)
@serialize_pydantic_return
async def get_job(
    auth_type: str,
    auth_data: dict[str, Any],
    job_id: str,
) -> GetJobOutput:
    """Retrieve the details for a single job."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return GetJobOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/2.2/jobs/get",
                headers=_headers(auth_data),
                params={"job_id": job_id},
            )
        if response.status_code != 200:
            return GetJobOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetJobOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetJobOutput(success=False, error=f"Call failed: {exc}")
    return GetJobOutput(success=True, data=data)


@tool(args_schema=GetJobPermissionsInput)
@serialize_pydantic_return
async def get_job_permissions(
    auth_type: str,
    auth_data: dict[str, Any],
    job_id: str,
) -> GetJobPermissionsOutput:
    """Get permissions of a job."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return GetJobPermissionsOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/2.0/permissions/jobs/{job_id}",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return GetJobPermissionsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetJobPermissionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetJobPermissionsOutput(success=False, error=f"Call failed: {exc}")
    return GetJobPermissionsOutput(success=True, data=data)


@tool(args_schema=GetRunInput)
@serialize_pydantic_return
async def get_run(
    auth_type: str,
    auth_data: dict[str, Any],
    run_id: str,
    include_history: bool | None = None,
    include_resolved_values: bool | None = None,
) -> GetRunOutput:
    """Retrieve the metadata of a run."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return GetRunOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        params: dict[str, Any] = {"run_id": run_id}
        if include_history is not None:
            params["include_history"] = include_history
        if include_resolved_values is not None:
            params["include_resolved_values"] = include_resolved_values
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/2.2/jobs/runs/get",
                headers=_headers(auth_data),
                params=params,
            )
        if response.status_code != 200:
            return GetRunOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetRunOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetRunOutput(success=False, error=f"Call failed: {exc}")
    return GetRunOutput(success=True, data=data)


@tool(args_schema=GetRunOutputInput)
@serialize_pydantic_return
async def get_run_output(
    auth_type: str,
    auth_data: dict[str, Any],
    run_id: str,
) -> GetRunOutputOutput:
    """Retrieve the output and metadata of a single task run."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return GetRunOutputOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/2.2/jobs/runs/get-output",
                headers=_headers(auth_data),
                params={"run_id": run_id},
            )
        if response.status_code != 200:
            return GetRunOutputOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetRunOutputOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetRunOutputOutput(success=False, error=f"Call failed: {exc}")
    return GetRunOutputOutput(success=True, data=data)


@tool(args_schema=GetSqlWarehouseInput)
@serialize_pydantic_return
async def get_sql_warehouse(
    auth_type: str,
    auth_data: dict[str, Any],
    warehouse_id: str,
) -> GetSqlWarehouseOutput:
    """Retrieve details for a specific SQL Warehouse."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return GetSqlWarehouseOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/2.0/sql/warehouses/{warehouse_id}",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return GetSqlWarehouseOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetSqlWarehouseOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSqlWarehouseOutput(success=False, error=f"Call failed: {exc}")
    return GetSqlWarehouseOutput(success=True, data=data)


@tool(args_schema=GetSqlWarehouseConfigInput)
@serialize_pydantic_return
async def get_sql_warehouse_config(
    auth_type: str,
    auth_data: dict[str, Any],
) -> GetSqlWarehouseConfigOutput:
    """Retrieve the global configuration for SQL Warehouses."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return GetSqlWarehouseConfigOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/2.0/sql/config/warehouses",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return GetSqlWarehouseConfigOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetSqlWarehouseConfigOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSqlWarehouseConfigOutput(success=False, error=f"Call failed: {exc}")
    return GetSqlWarehouseConfigOutput(success=True, data=data)


@tool(args_schema=GetSqlWarehousePermissionsInput)
@serialize_pydantic_return
async def get_sql_warehouse_permissions(
    auth_type: str,
    auth_data: dict[str, Any],
    warehouse_id: str,
) -> GetSqlWarehousePermissionsOutput:
    """Retrieve the permissions for a specific SQL Warehouse."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return GetSqlWarehousePermissionsOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/2.0/permissions/warehouses/{warehouse_id}",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return GetSqlWarehousePermissionsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetSqlWarehousePermissionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSqlWarehousePermissionsOutput(success=False, error=f"Call failed: {exc}")
    return GetSqlWarehousePermissionsOutput(success=True, data=data)


@tool(args_schema=GetVectorSearchIndexInput)
@serialize_pydantic_return
async def get_vector_search_index(
    auth_type: str,
    auth_data: dict[str, Any],
    index_name: str,
) -> GetVectorSearchIndexOutput:
    """Retrieve details about a specific vector search index."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return GetVectorSearchIndexOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/2.0/vector-search/indexes/{index_name}",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return GetVectorSearchIndexOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetVectorSearchIndexOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetVectorSearchIndexOutput(success=False, error=f"Call failed: {exc}")
    return GetVectorSearchIndexOutput(success=True, data=data)


@tool(args_schema=ListEndpointsInput)
@serialize_pydantic_return
async def list_endpoints(
    auth_type: str,
    auth_data: dict[str, Any],
    max_results: int = 100,
) -> ListEndpointsOutput:
    """List all vector search endpoints."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return ListEndpointsOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        all_endpoints: list[dict[str, Any]] = []
        page_token: str | None = None
        pages_seen = 0
        max_pages = 50
        while pages_seen < max_pages:
            pages_seen += 1
            params: dict[str, Any] = {}
            if page_token:
                params["page_token"] = page_token
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                response = await client.get(
                    f"{_base_url(auth_data)}/api/2.0/vector-search/endpoints",
                    headers=_headers(auth_data),
                    params=params,
                )
            if response.status_code != 200:
                return ListEndpointsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
            data = response.json()
            all_endpoints.extend(data.get("endpoints", []))
            page_token = data.get("next_page_token")
            if not page_token or len(all_endpoints) >= max_results:
                break
    except httpx.TimeoutException:
        return ListEndpointsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListEndpointsOutput(success=False, error=f"Call failed: {exc}")
    return ListEndpointsOutput(success=True, endpoints=all_endpoints[:max_results])


@tool(args_schema=ListJobsInput)
@serialize_pydantic_return
async def list_jobs(
    auth_type: str,
    auth_data: dict[str, Any],
    expand_tasks: bool | None = None,
    name: str | None = None,
    max_requests: int | None = None,
) -> ListJobsOutput:
    """List all jobs using automatic pagination."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return ListJobsOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        all_jobs: list[dict[str, Any]] = []
        page_token: str | None = None
        requests_made = 0
        limit = max_requests or 5
        while requests_made < limit:
            params: dict[str, Any] = {"limit": 100}
            if expand_tasks is not None:
                params["expand_tasks"] = expand_tasks
            if name:
                params["name"] = name
            if page_token:
                params["page_token"] = page_token
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                response = await client.get(
                    f"{_base_url(auth_data)}/api/2.2/jobs/list",
                    headers=_headers(auth_data),
                    params=params,
                )
            if response.status_code != 200:
                return ListJobsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
            data = response.json()
            all_jobs.extend(data.get("jobs", []))
            page_token = data.get("next_page_token")
            requests_made += 1
            if not page_token:
                break
    except httpx.TimeoutException:
        return ListJobsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListJobsOutput(success=False, error=f"Call failed: {exc}")
    return ListJobsOutput(success=True, jobs=all_jobs)


@tool(args_schema=ListRunsInput)
@serialize_pydantic_return
async def list_runs(
    auth_type: str,
    auth_data: dict[str, Any],
    job_id: str | None = None,
    active_only: bool | None = None,
    max_results: int = 100,
) -> ListRunsOutput:
    """List all runs available to the user."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return ListRunsOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        params: dict[str, Any] = {"limit": min(max_results, 100)}
        if job_id:
            params["job_id"] = job_id
        if active_only is not None:
            params["active_only"] = active_only
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/2.2/jobs/runs/list",
                headers=_headers(auth_data),
                params=params,
            )
        if response.status_code != 200:
            return ListRunsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListRunsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListRunsOutput(success=False, error=f"Call failed: {exc}")
    return ListRunsOutput(success=True, runs=data.get("runs", []))


@tool(args_schema=ListSqlWarehousesInput)
@serialize_pydantic_return
async def list_sql_warehouses(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListSqlWarehousesOutput:
    """List all SQL Warehouses available in the workspace."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return ListSqlWarehousesOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/2.0/sql/warehouses",
                headers=_headers(auth_data),
            )
        if response.status_code != 200:
            return ListSqlWarehousesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListSqlWarehousesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListSqlWarehousesOutput(success=False, error=f"Call failed: {exc}")
    return ListSqlWarehousesOutput(success=True, warehouses=data.get("warehouses", []))


@tool(args_schema=ListVectorSearchIndexesInput)
@serialize_pydantic_return
async def list_vector_search_indexes(
    auth_type: str,
    auth_data: dict[str, Any],
    endpoint_name: str,
) -> ListVectorSearchIndexesOutput:
    """List all vector search indexes for a given endpoint."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return ListVectorSearchIndexesOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_base_url(auth_data)}/api/2.0/vector-search/indexes",
                headers=_headers(auth_data),
                params={"endpoint_name": endpoint_name},
            )
        if response.status_code != 200:
            return ListVectorSearchIndexesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListVectorSearchIndexesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListVectorSearchIndexesOutput(success=False, error=f"Call failed: {exc}")
    return ListVectorSearchIndexesOutput(success=True, indexes=data.get("vector_indexes", []))


@tool(args_schema=QueryVectorSearchIndexInput)
@serialize_pydantic_return
async def query_vector_search_index(
    auth_type: str,
    auth_data: dict[str, Any],
    index_name: str,
    columns: str,
    query_text: str | None = None,
    query_vector: str | None = None,
    filters_json: str | None = None,
    num_results: int = 10,
    include_embeddings: bool | None = None,
) -> QueryVectorSearchIndexOutput:
    """Query a specific vector search index."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return QueryVectorSearchIndexOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {
            "columns": _parse_json(columns),
            "num_results": num_results,
        }
        if query_text:
            body["query_text"] = query_text
        if query_vector:
            body["query_vector"] = _parse_json(query_vector)
        if filters_json:
            body["filters_json"] = filters_json
        if include_embeddings is not None:
            body["score_threshold"] = None
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.0/vector-search/indexes/{index_name}/query",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return QueryVectorSearchIndexOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return QueryVectorSearchIndexOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return QueryVectorSearchIndexOutput(success=False, error=f"Call failed: {exc}")
    return QueryVectorSearchIndexOutput(success=True, data=data)


@tool(args_schema=RepairRunInput)
@serialize_pydantic_return
async def repair_run(
    auth_type: str,
    auth_data: dict[str, Any],
    run_id: str,
    rerun_tasks: str | None = None,
    rerun_all_failed_tasks: bool | None = None,
    pipeline_params_full_refresh: bool | None = None,
) -> RepairRunOutput:
    """Re-run one or more tasks."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return RepairRunOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {"run_id": run_id}
        if rerun_tasks:
            body["rerun_tasks"] = _parse_json(rerun_tasks)
        if rerun_all_failed_tasks is not None:
            body["rerun_all_failed_tasks"] = rerun_all_failed_tasks
        if pipeline_params_full_refresh is not None:
            body["pipeline_params"] = {"full_refresh": pipeline_params_full_refresh}
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.2/jobs/runs/repair",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return RepairRunOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return RepairRunOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RepairRunOutput(success=False, error=f"Call failed: {exc}")
    return RepairRunOutput(success=True, repair_id=str(data.get("repair_id", "")))


@tool(args_schema=ResetJobInput)
@serialize_pydantic_return
async def reset_job(
    auth_type: str,
    auth_data: dict[str, Any],
    job_id: str,
    new_settings: str,
) -> ResetJobOutput:
    """Overwrite all settings for a job."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return ResetJobOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {
            "job_id": job_id,
            "new_settings": _parse_json(new_settings),
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.2/jobs/reset",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return ResetJobOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return ResetJobOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ResetJobOutput(success=False, error=f"Call failed: {exc}")
    return ResetJobOutput(success=True)


@tool(args_schema=RunJobNowInput)
@serialize_pydantic_return
async def run_job_now(
    auth_type: str,
    auth_data: dict[str, Any],
    job_id: str,
    jar_params: str | None = None,
    notebook_params: str | None = None,
    python_params: str | None = None,
    spark_submit_params: str | None = None,
) -> RunJobNowOutput:
    """Run a job now and return the ID of the triggered run."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return RunJobNowOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {"job_id": job_id}
        if jar_params:
            body["jar_params"] = _parse_json(jar_params)
        if notebook_params:
            body["notebook_params"] = _parse_json(notebook_params)
        if python_params:
            body["python_params"] = _parse_json(python_params)
        if spark_submit_params:
            body["spark_submit_params"] = _parse_json(spark_submit_params)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.2/jobs/run-now",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return RunJobNowOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return RunJobNowOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RunJobNowOutput(success=False, error=f"Call failed: {exc}")
    return RunJobNowOutput(
        success=True,
        run_id=str(data.get("run_id", "")),
        number_in_job=data.get("number_in_job"),
    )


@tool(args_schema=ScanVectorSearchIndexInput)
@serialize_pydantic_return
async def scan_vector_search_index(
    auth_type: str,
    auth_data: dict[str, Any],
    index_name: str,
    last_primary_key: str | None = None,
    num_results: int = 10,
) -> ScanVectorSearchIndexOutput:
    """Scan a vector search index and return entries after a given primary key."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return ScanVectorSearchIndexOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {"num_results": num_results}
        if last_primary_key:
            body["last_primary_key"] = last_primary_key
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.0/vector-search/indexes/{index_name}/scan",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return ScanVectorSearchIndexOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ScanVectorSearchIndexOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ScanVectorSearchIndexOutput(success=False, error=f"Call failed: {exc}")
    return ScanVectorSearchIndexOutput(success=True, data=data)


@tool(args_schema=SetJobPermissionsInput)
@serialize_pydantic_return
async def set_job_permissions(
    auth_type: str,
    auth_data: dict[str, Any],
    job_id: str,
    access_control_list: str,
) -> SetJobPermissionsOutput:
    """Set permissions on a job."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return SetJobPermissionsOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {
            "access_control_list": _parse_json(access_control_list),
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_base_url(auth_data)}/api/2.0/permissions/jobs/{job_id}",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return SetJobPermissionsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return SetJobPermissionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SetJobPermissionsOutput(success=False, error=f"Call failed: {exc}")
    return SetJobPermissionsOutput(success=True, data=data)


@tool(args_schema=SetSqlWarehouseConfigInput)
@serialize_pydantic_return
async def set_sql_warehouse_config(
    auth_type: str,
    auth_data: dict[str, Any],
    instance_profile_arn: str | None = None,
    google_service_account: str | None = None,
    security_policy: str | None = None,
    channel: str | None = None,
    enabled_warehouse_types: str | None = None,
    config_param: str | None = None,
    global_param: str | None = None,
) -> SetSqlWarehouseConfigOutput:
    """Update the global configuration for SQL Warehouses."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return SetSqlWarehouseConfigOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {}
        if instance_profile_arn:
            body["instance_profile_arn"] = instance_profile_arn
        if google_service_account:
            body["google_service_account"] = google_service_account
        if security_policy:
            body["security_policy"] = security_policy
        if channel:
            body["channel"] = _parse_json(channel)
        if enabled_warehouse_types:
            body["enabled_warehouse_types"] = _parse_json(enabled_warehouse_types)
        if config_param:
            body["data_access_config"] = _parse_json(config_param)
        if global_param:
            body["sql_configuration_parameters"] = {"configuration_pairs": _parse_json(global_param)}
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_base_url(auth_data)}/api/2.0/sql/config/warehouses",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return SetSqlWarehouseConfigOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json() if response.text else {}
    except httpx.TimeoutException:
        return SetSqlWarehouseConfigOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SetSqlWarehouseConfigOutput(success=False, error=f"Call failed: {exc}")
    return SetSqlWarehouseConfigOutput(success=True, data=data)


@tool(args_schema=SetSqlWarehousePermissionsInput)
@serialize_pydantic_return
async def set_sql_warehouse_permissions(
    auth_type: str,
    auth_data: dict[str, Any],
    warehouse_id: str,
    access_control_list: str,
) -> SetSqlWarehousePermissionsOutput:
    """Update the permissions for a specific SQL Warehouse."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return SetSqlWarehousePermissionsOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {
            "access_control_list": _parse_json(access_control_list),
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_base_url(auth_data)}/api/2.0/permissions/warehouses/{warehouse_id}",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return SetSqlWarehousePermissionsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return SetSqlWarehousePermissionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SetSqlWarehousePermissionsOutput(success=False, error=f"Call failed: {exc}")
    return SetSqlWarehousePermissionsOutput(success=True, data=data)


@tool(args_schema=StartSqlWarehouseInput)
@serialize_pydantic_return
async def start_sql_warehouse(
    auth_type: str,
    auth_data: dict[str, Any],
    warehouse_id: str,
) -> StartSqlWarehouseOutput:
    """Start a SQL Warehouse by ID."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return StartSqlWarehouseOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.0/sql/warehouses/{warehouse_id}/start",
                headers=_headers(auth_data),
                json={},
            )
        if response.status_code != 200:
            return StartSqlWarehouseOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return StartSqlWarehouseOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return StartSqlWarehouseOutput(success=False, error=f"Call failed: {exc}")
    return StartSqlWarehouseOutput(success=True)


@tool(args_schema=StopSqlWarehouseInput)
@serialize_pydantic_return
async def stop_sql_warehouse(
    auth_type: str,
    auth_data: dict[str, Any],
    warehouse_id: str,
) -> StopSqlWarehouseOutput:
    """Stop a SQL Warehouse by ID."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return StopSqlWarehouseOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.0/sql/warehouses/{warehouse_id}/stop",
                headers=_headers(auth_data),
                json={},
            )
        if response.status_code != 200:
            return StopSqlWarehouseOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return StopSqlWarehouseOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return StopSqlWarehouseOutput(success=False, error=f"Call failed: {exc}")
    return StopSqlWarehouseOutput(success=True)


@tool(args_schema=SyncVectorSearchIndexInput)
@serialize_pydantic_return
async def sync_vector_search_index(
    auth_type: str,
    auth_data: dict[str, Any],
    index_name: str,
) -> SyncVectorSearchIndexOutput:
    """Synchronize a Delta Sync vector search index."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return SyncVectorSearchIndexOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.0/vector-search/indexes/{index_name}/sync",
                headers=_headers(auth_data),
                json={},
            )
        if response.status_code != 200:
            return SyncVectorSearchIndexOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json() if response.text else {}
    except httpx.TimeoutException:
        return SyncVectorSearchIndexOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SyncVectorSearchIndexOutput(success=False, error=f"Call failed: {exc}")
    return SyncVectorSearchIndexOutput(success=True, data=data)


@tool(args_schema=UpdateJobInput)
@serialize_pydantic_return
async def update_job(
    auth_type: str,
    auth_data: dict[str, Any],
    job_id: str,
    new_settings: str,
    fields_to_remove: str | None = None,
) -> UpdateJobOutput:
    """Update an existing job. Only the fields provided will be updated."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return UpdateJobOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {
            "job_id": job_id,
            "new_settings": _parse_json(new_settings),
        }
        if fields_to_remove:
            body["fields_to_remove"] = _parse_json(fields_to_remove)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.2/jobs/update",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return UpdateJobOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return UpdateJobOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateJobOutput(success=False, error=f"Call failed: {exc}")
    return UpdateJobOutput(success=True)


@tool(args_schema=UpsertVectorSearchIndexDataInput)
@serialize_pydantic_return
async def upsert_vector_search_index_data(
    auth_type: str,
    auth_data: dict[str, Any],
    index_name: str,
    inputs_json: str,
) -> UpsertVectorSearchIndexDataOutput:
    """Upsert data into an existing vector search index."""
    if not auth_data.get("access_token") or not auth_data.get("domain"):
        return UpsertVectorSearchIndexDataOutput(
            success=False, error="Missing or empty Databricks credentials."
        )
    try:
        body: dict[str, Any] = {
            "inputs_json": inputs_json,
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_base_url(auth_data)}/api/2.0/vector-search/indexes/{index_name}/upsert-data",
                headers=_headers(auth_data),
                json=body,
            )
        if response.status_code != 200:
            return UpsertVectorSearchIndexDataOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json() if response.text else {}
    except httpx.TimeoutException:
        return UpsertVectorSearchIndexDataOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpsertVectorSearchIndexDataOutput(success=False, error=f"Call failed: {exc}")
    return UpsertVectorSearchIndexDataOutput(success=True, data=data)
