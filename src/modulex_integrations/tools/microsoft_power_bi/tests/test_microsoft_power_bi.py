"""Happy-path tests for every microsoft_power_bi @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.microsoft_power_bi import (
    TOOLS,
    add_rows_to_push_dataset,
    execute_dax_query,
    export_report,
    get_refresh_history,
    get_reports_by_id,
    list_dashboards,
    list_datasets,
    list_reports,
    list_workspaces,
    manifest,
    refresh_dataset,
)
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

API = "https://api.powerbi.com/v1.0/myorg"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a .ainvoke() input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_10_actions(self) -> None:
        assert len(manifest.actions) == 10

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_add_rows_to_push_dataset(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/datasets/ds-123/tables/MyTable/rows",
        status_code=200,
        json={},
    )

    result_dict = await add_rows_to_push_dataset.ainvoke(
        _args(
            dataset_id="ds-123",
            table_name="MyTable",
            rows='[{"id": 1, "name": "test"}]',
        )
    )

    assert isinstance(result_dict, dict)
    result = AddRowsToPushDatasetOutput.model_validate(result_dict)
    assert result.success is True
    assert result.rows_added == 1


@pytest.mark.asyncio
async def test_execute_dax_query(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/datasets/ds-456/executeQueries",
        json={
            "results": [
                {
                    "tables": [
                        {
                            "rows": [
                                {"[Name]": "Widget A", "[Sales]": 100},
                                {"[Name]": "Widget B", "[Sales]": 200},
                            ]
                        }
                    ]
                }
            ]
        },
    )

    result_dict = await execute_dax_query.ainvoke(
        _args(
            dataset_id="ds-456",
            query="EVALUATE FILTER('Products', 'Products'[Category] = \"Widgets\")",
        )
    )

    assert isinstance(result_dict, dict)
    result = ExecuteDaxQueryOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.results) == 2


@pytest.mark.asyncio
async def test_export_report(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/reports/rpt-789/ExportTo",
        status_code=202,
        json={"id": "export-001", "status": "Running", "percentComplete": 0},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/reports/rpt-789/exports/export-001",
        json={"id": "export-001", "status": "Succeeded", "percentComplete": 100},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/reports/rpt-789/exports/export-001/file",
        content=b"%PDF-1.4 fake content",
    )

    result_dict = await export_report.ainvoke(
        _args(
            report_id="rpt-789",
            format="PDF",
            poll_interval_seconds=0,
            poll_timeout_seconds=10,
        )
    )

    assert isinstance(result_dict, dict)
    result = ExportReportOutput.model_validate(result_dict)
    assert result.success is True
    assert result.export_id == "export-001"
    assert result.file_base64 is not None


@pytest.mark.asyncio
async def test_get_refresh_history(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/datasets/ds-111/refreshes",
        json={
            "value": [
                {
                    "requestId": "req-1",
                    "refreshType": "Scheduled",
                    "startTime": "2026-05-20T10:00:00Z",
                    "endTime": "2026-05-20T10:05:00Z",
                    "status": "Completed",
                }
            ]
        },
    )

    result_dict = await get_refresh_history.ainvoke(
        _args(dataset_id="ds-111")
    )

    assert isinstance(result_dict, dict)
    result = GetRefreshHistoryOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.refreshes) == 1


@pytest.mark.asyncio
async def test_get_reports_by_id(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/reports/rpt-abc",
        json={
            "id": "rpt-abc",
            "name": "Sales Report",
            "webUrl": "https://app.powerbi.com/reports/rpt-abc",
            "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=rpt-abc",
            "datasetId": "ds-xyz",
            "reportType": "PowerBIReport",
        },
    )

    result_dict = await get_reports_by_id.ainvoke(
        _args(report_id="rpt-abc")
    )

    assert isinstance(result_dict, dict)
    result = GetReportsByIdOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "Sales Report"


@pytest.mark.asyncio
async def test_list_dashboards(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/dashboards",
        json={
            "value": [
                {"id": "dash-1", "displayName": "Executive Dashboard", "isReadOnly": False}
            ]
        },
    )

    result_dict = await list_dashboards.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListDashboardsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.dashboards) == 1


@pytest.mark.asyncio
async def test_list_datasets(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/datasets",
        json={
            "value": [
                {"id": "ds-1", "name": "Sales Data", "addRowsAPIEnabled": True}
            ]
        },
    )

    result_dict = await list_datasets.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListDatasetsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.datasets) == 1


@pytest.mark.asyncio
async def test_list_reports(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/reports",
        json={
            "value": [
                {"id": "rpt-1", "name": "Monthly Report", "reportType": "PowerBIReport"}
            ]
        },
    )

    result_dict = await list_reports.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListReportsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.reports) == 1


@pytest.mark.asyncio
async def test_list_workspaces(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/groups",
        json={
            "value": [
                {"id": "ws-1", "name": "Finance", "isReadOnly": False, "type": "Workspace"}
            ]
        },
    )

    result_dict = await list_workspaces.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListWorkspacesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.workspaces) == 1


@pytest.mark.asyncio
async def test_refresh_dataset(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/datasets/ds-222/refreshes",
        status_code=202,
        headers={"x-ms-request-id": "req-id-1", "Location": "/refreshes/req-id-1"},
    )

    result_dict = await refresh_dataset.ainvoke(
        _args(dataset_id="ds-222")
    )

    assert isinstance(result_dict, dict)
    result = RefreshDatasetOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status_code == 202


@pytest.mark.asyncio
async def test_list_workspaces_empty_token() -> None:
    """Failure-path: empty access_token returns success=False without hitting the wire."""
    result_dict = await list_workspaces.ainvoke(
        _args(auth_data={"access_token": ""})
    )

    assert isinstance(result_dict, dict)
    result = ListWorkspacesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access_token" in result.error
