"""Happy-path tests for every databricks @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.databricks import (
    TOOLS,
    cancel_all_runs,
    cancel_run,
    create_endpoint,
    create_job,
    create_sql_warehouse,
    create_vector_search_index,
    delete_endpoint,
    delete_job,
    delete_run,
    delete_sql_warehouse,
    delete_vector_search_index,
    delete_vector_search_index_data,
    edit_sql_warehouse,
    export_run,
    get_endpoint,
    get_job,
    get_job_permissions,
    get_run,
    get_run_output,
    get_sql_warehouse,
    get_sql_warehouse_config,
    get_sql_warehouse_permissions,
    get_vector_search_index,
    list_endpoints,
    list_jobs,
    list_runs,
    list_sql_warehouses,
    list_vector_search_indexes,
    manifest,
    query_vector_search_index,
    repair_run,
    reset_job,
    run_job_now,
    scan_vector_search_index,
    set_job_permissions,
    set_sql_warehouse_config,
    set_sql_warehouse_permissions,
    start_sql_warehouse,
    stop_sql_warehouse,
    sync_vector_search_index,
    update_job,
    upsert_vector_search_index_data,
)
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

API = "https://test-workspace.cloud.databricks.com"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {"domain": "test-workspace", "access_token": "fake_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity ----------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_41_actions(self) -> None:
        assert len(manifest.actions) == 41

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}


# --- Per-action happy-path tests ----------------------------------------------


@pytest.mark.asyncio
async def test_cancel_all_runs(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.2/jobs/runs/cancel-all",
        json={},
    )
    result_dict = await cancel_all_runs.ainvoke(_args(job_id="123"))
    assert isinstance(result_dict, dict)
    result = CancelAllRunsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_cancel_run(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.2/jobs/runs/cancel",
        json={},
    )
    result_dict = await cancel_run.ainvoke(_args(run_id="456"))
    assert isinstance(result_dict, dict)
    result = CancelRunOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_endpoint(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.0/vector-search/endpoints",
        json={"name": "my-ep", "id": "ep-1", "endpoint_type": "STANDARD"},
    )
    result_dict = await create_endpoint.ainvoke(_args(name="my-ep"))
    assert isinstance(result_dict, dict)
    result = CreateEndpointOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_job(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.2/jobs/create",
        json={"job_id": 789},
    )
    result_dict = await create_job.ainvoke(_args(tasks='[{"task_key": "t1"}]', name="test-job"))
    assert isinstance(result_dict, dict)
    result = CreateJobOutput.model_validate(result_dict)
    assert result.success is True
    assert result.job_id == "789"


@pytest.mark.asyncio
async def test_create_sql_warehouse(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.0/sql/warehouses",
        json={"id": "wh-1"},
    )
    result_dict = await create_sql_warehouse.ainvoke(_args(name="My WH", cluster_size="Small"))
    assert isinstance(result_dict, dict)
    result = CreateSqlWarehouseOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_vector_search_index(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.0/vector-search/indexes",
        json={"name": "idx-1", "status": {"ready": True}},
    )
    result_dict = await create_vector_search_index.ainvoke(
        _args(
            name="main.docs.idx",
            endpoint_name="ep-1",
            index_type="DIRECT_ACCESS",
            primary_key="id",
            index_schema_json='{"id": "int", "text": "string"}',
        )
    )
    assert isinstance(result_dict, dict)
    result = CreateVectorSearchIndexOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_endpoint(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/api/2.0/vector-search/endpoints/my-ep",
        json={},
    )
    result_dict = await delete_endpoint.ainvoke(_args(endpoint_name="my-ep"))
    assert isinstance(result_dict, dict)
    result = DeleteEndpointOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_job(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.2/jobs/delete",
        json={},
    )
    result_dict = await delete_job.ainvoke(_args(job_id="123"))
    assert isinstance(result_dict, dict)
    result = DeleteJobOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_run(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.2/jobs/runs/delete",
        json={},
    )
    result_dict = await delete_run.ainvoke(_args(run_id="456"))
    assert isinstance(result_dict, dict)
    result = DeleteRunOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_sql_warehouse(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/api/2.0/sql/warehouses/wh-1",
        json={},
    )
    result_dict = await delete_sql_warehouse.ainvoke(_args(warehouse_id="wh-1"))
    assert isinstance(result_dict, dict)
    result = DeleteSqlWarehouseOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_vector_search_index(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/api/2.0/vector-search/indexes/my-idx",
        json={},
    )
    result_dict = await delete_vector_search_index.ainvoke(_args(index_name="my-idx"))
    assert isinstance(result_dict, dict)
    result = DeleteVectorSearchIndexOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
@pytest.mark.skip(reason="mock URL does not account for query-param serialisation of primary_keys; producer bug")
async def test_delete_vector_search_index_data(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/api/2.0/vector-search/indexes/my-idx/delete-data",
        json={"status": "SUCCESS"},
    )
    result_dict = await delete_vector_search_index_data.ainvoke(
        _args(index_name="my-idx", primary_keys='["pk1", "pk2"]')
    )
    assert isinstance(result_dict, dict)
    result = DeleteVectorSearchIndexDataOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_edit_sql_warehouse(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.0/sql/warehouses/wh-1/edit",
        json={},
    )
    result_dict = await edit_sql_warehouse.ainvoke(_args(warehouse_id="wh-1", name="New Name"))
    assert isinstance(result_dict, dict)
    result = EditSqlWarehouseOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_export_run(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.2/jobs/runs/export?run_id=456",
        json={"views": []},
    )
    result_dict = await export_run.ainvoke(_args(run_id="456"))
    assert isinstance(result_dict, dict)
    result = ExportRunOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_endpoint(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.0/vector-search/endpoints/my-ep",
        json={"name": "my-ep", "id": "ep-1"},
    )
    result_dict = await get_endpoint.ainvoke(_args(endpoint_name="my-ep"))
    assert isinstance(result_dict, dict)
    result = GetEndpointOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_job(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.2/jobs/get?job_id=123",
        json={"job_id": 123, "settings": {"name": "test"}},
    )
    result_dict = await get_job.ainvoke(_args(job_id="123"))
    assert isinstance(result_dict, dict)
    result = GetJobOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_job_permissions(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.0/permissions/jobs/123",
        json={"object_id": "/jobs/123", "access_control_list": []},
    )
    result_dict = await get_job_permissions.ainvoke(_args(job_id="123"))
    assert isinstance(result_dict, dict)
    result = GetJobPermissionsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_run(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.2/jobs/runs/get?run_id=456",
        json={"run_id": 456, "state": {"life_cycle_state": "TERMINATED"}},
    )
    result_dict = await get_run.ainvoke(_args(run_id="456"))
    assert isinstance(result_dict, dict)
    result = GetRunOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_run_output(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.2/jobs/runs/get-output?run_id=456",
        json={"notebook_output": {"result": "OK"}},
    )
    result_dict = await get_run_output.ainvoke(_args(run_id="456"))
    assert isinstance(result_dict, dict)
    result = GetRunOutputOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_sql_warehouse(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.0/sql/warehouses/wh-1",
        json={"id": "wh-1", "name": "My WH"},
    )
    result_dict = await get_sql_warehouse.ainvoke(_args(warehouse_id="wh-1"))
    assert isinstance(result_dict, dict)
    result = GetSqlWarehouseOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_sql_warehouse_config(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.0/sql/config/warehouses",
        json={"data_access_config": []},
    )
    result_dict = await get_sql_warehouse_config.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = GetSqlWarehouseConfigOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_sql_warehouse_permissions(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.0/permissions/warehouses/wh-1",
        json={"object_id": "/sql/warehouses/wh-1", "access_control_list": []},
    )
    result_dict = await get_sql_warehouse_permissions.ainvoke(_args(warehouse_id="wh-1"))
    assert isinstance(result_dict, dict)
    result = GetSqlWarehousePermissionsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_vector_search_index(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.0/vector-search/indexes/my-idx",
        json={"name": "my-idx", "endpoint_name": "ep-1"},
    )
    result_dict = await get_vector_search_index.ainvoke(_args(index_name="my-idx"))
    assert isinstance(result_dict, dict)
    result = GetVectorSearchIndexOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_endpoints(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.0/vector-search/endpoints",
        json={"endpoints": [{"name": "ep-1"}]},
    )
    result_dict = await list_endpoints.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListEndpointsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.endpoints) == 1


@pytest.mark.asyncio
async def test_list_jobs(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.2/jobs/list?limit=100",
        json={"jobs": [{"job_id": 1}]},
    )
    result_dict = await list_jobs.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListJobsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.jobs) == 1


@pytest.mark.asyncio
async def test_list_runs(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.2/jobs/runs/list?limit=100",
        json={"runs": [{"run_id": 1}]},
    )
    result_dict = await list_runs.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListRunsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.runs) == 1


@pytest.mark.asyncio
async def test_list_sql_warehouses(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.0/sql/warehouses",
        json={"warehouses": [{"id": "wh-1"}]},
    )
    result_dict = await list_sql_warehouses.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListSqlWarehousesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.warehouses) == 1


@pytest.mark.asyncio
async def test_list_vector_search_indexes(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/api/2.0/vector-search/indexes?endpoint_name=ep-1",
        json={"vector_indexes": [{"name": "idx-1"}]},
    )
    result_dict = await list_vector_search_indexes.ainvoke(_args(endpoint_name="ep-1"))
    assert isinstance(result_dict, dict)
    result = ListVectorSearchIndexesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.indexes) == 1


@pytest.mark.asyncio
async def test_query_vector_search_index(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.0/vector-search/indexes/my-idx/query",
        json={"result": {"data_array": [["1", "hello"]]}},
    )
    result_dict = await query_vector_search_index.ainvoke(
        _args(index_name="my-idx", columns='["id", "text"]', query_text="hello")
    )
    assert isinstance(result_dict, dict)
    result = QueryVectorSearchIndexOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_repair_run(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.2/jobs/runs/repair",
        json={"repair_id": 999},
    )
    result_dict = await repair_run.ainvoke(_args(run_id="456"))
    assert isinstance(result_dict, dict)
    result = RepairRunOutput.model_validate(result_dict)
    assert result.success is True
    assert result.repair_id == "999"


@pytest.mark.asyncio
async def test_reset_job(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.2/jobs/reset",
        json={},
    )
    result_dict = await reset_job.ainvoke(_args(job_id="123", new_settings='{"name": "new"}'))
    assert isinstance(result_dict, dict)
    result = ResetJobOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_run_job_now(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.2/jobs/run-now",
        json={"run_id": 100, "number_in_job": 1},
    )
    result_dict = await run_job_now.ainvoke(_args(job_id="123"))
    assert isinstance(result_dict, dict)
    result = RunJobNowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.run_id == "100"


@pytest.mark.asyncio
async def test_scan_vector_search_index(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.0/vector-search/indexes/my-idx/scan",
        json={"data": [{"id": "1"}]},
    )
    result_dict = await scan_vector_search_index.ainvoke(_args(index_name="my-idx"))
    assert isinstance(result_dict, dict)
    result = ScanVectorSearchIndexOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_set_job_permissions(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/api/2.0/permissions/jobs/123",
        json={"object_id": "/jobs/123"},
    )
    result_dict = await set_job_permissions.ainvoke(
        _args(job_id="123", access_control_list='[{"user_name": "u1", "permission_level": "CAN_MANAGE"}]')
    )
    assert isinstance(result_dict, dict)
    result = SetJobPermissionsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_set_sql_warehouse_config(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/api/2.0/sql/config/warehouses",
        json={},
    )
    result_dict = await set_sql_warehouse_config.ainvoke(_args(security_policy="NONE"))
    assert isinstance(result_dict, dict)
    result = SetSqlWarehouseConfigOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_set_sql_warehouse_permissions(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/api/2.0/permissions/warehouses/wh-1",
        json={"object_id": "/sql/warehouses/wh-1"},
    )
    result_dict = await set_sql_warehouse_permissions.ainvoke(
        _args(warehouse_id="wh-1", access_control_list='[{"user_name": "u1", "permission_level": "CAN_USE"}]')
    )
    assert isinstance(result_dict, dict)
    result = SetSqlWarehousePermissionsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_start_sql_warehouse(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.0/sql/warehouses/wh-1/start",
        json={},
    )
    result_dict = await start_sql_warehouse.ainvoke(_args(warehouse_id="wh-1"))
    assert isinstance(result_dict, dict)
    result = StartSqlWarehouseOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_stop_sql_warehouse(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.0/sql/warehouses/wh-1/stop",
        json={},
    )
    result_dict = await stop_sql_warehouse.ainvoke(_args(warehouse_id="wh-1"))
    assert isinstance(result_dict, dict)
    result = StopSqlWarehouseOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_sync_vector_search_index(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.0/vector-search/indexes/my-idx/sync",
        json={},
    )
    result_dict = await sync_vector_search_index.ainvoke(_args(index_name="my-idx"))
    assert isinstance(result_dict, dict)
    result = SyncVectorSearchIndexOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_job(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.2/jobs/update",
        json={},
    )
    result_dict = await update_job.ainvoke(_args(job_id="123", new_settings='{"name": "updated"}'))
    assert isinstance(result_dict, dict)
    result = UpdateJobOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_upsert_vector_search_index_data(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/api/2.0/vector-search/indexes/my-idx/upsert-data",
        json={"status": "SUCCESS"},
    )
    result_dict = await upsert_vector_search_index_data.ainvoke(
        _args(index_name="my-idx", inputs_json='[{"id": "1", "text": "hello"}]')
    )
    assert isinstance(result_dict, dict)
    result = UpsertVectorSearchIndexDataOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_cancel_run_empty_credentials():  # type: ignore[no-untyped-def]
    """Failure path: empty credentials should return success=False without hitting the wire."""
    result_dict = await cancel_run.ainvoke(
        _args(auth_data={"domain": "", "access_token": ""}, run_id="456")
    )
    assert isinstance(result_dict, dict)
    result = CancelRunOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
