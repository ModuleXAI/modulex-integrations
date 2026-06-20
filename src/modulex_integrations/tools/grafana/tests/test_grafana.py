"""Happy-path tests per action + failure-path and empty-credential tests.

Grafana tools follow the modulex api_key convention and additionally
receive the instance ``base_url`` (injected from the credential's
GRAFANA_BASE_URL env var). Every test passes both explicitly.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.grafana import (
    TOOLS,
    check_data_source_health,
    create_alert_rule,
    create_annotation,
    create_contact_point,
    create_dashboard,
    create_folder,
    delete_alert_rule,
    delete_annotation,
    delete_dashboard,
    delete_folder,
    get_alert_rule,
    get_dashboard,
    get_data_source,
    get_folder,
    get_health,
    list_alert_rules,
    list_annotations,
    list_contact_points,
    list_dashboards,
    list_data_sources,
    list_folders,
    manifest,
    update_alert_rule,
    update_annotation,
    update_dashboard,
    update_folder,
)
from modulex_integrations.tools.grafana.outputs import (
    CheckDataSourceHealthOutput,
    CreateAlertRuleOutput,
    CreateAnnotationOutput,
    CreateContactPointOutput,
    CreateDashboardOutput,
    CreateFolderOutput,
    DeleteAlertRuleOutput,
    DeleteAnnotationOutput,
    DeleteDashboardOutput,
    DeleteFolderOutput,
    GetAlertRuleOutput,
    GetDashboardOutput,
    GetDataSourceOutput,
    GetFolderOutput,
    GetHealthOutput,
    ListAlertRulesOutput,
    ListAnnotationsOutput,
    ListContactPointsOutput,
    ListDashboardsOutput,
    ListDataSourcesOutput,
    ListFoldersOutput,
    UpdateAlertRuleOutput,
    UpdateAnnotationOutput,
    UpdateDashboardOutput,
    UpdateFolderOutput,
)

BASE = "https://grafana.example.com"
_API_KEY = "glsa_fake_token"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, base_url=BASE, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_25_actions(self) -> None:
        assert len(manifest.actions) == 25

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_base_url_envvar_injected_into_auth_data(self) -> None:
        env = manifest.auth_schemas[0].setup_environment_variables
        base = next(e for e in env if e.name == "GRAFANA_BASE_URL")
        assert base.inject_into_auth_data is True
        assert base.required is True
        assert base.sensitive is False


# --- Happy-path: dashboards -------------------------------------------------


@pytest.mark.asyncio
async def test_list_dashboards(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/search?type=dash-db",
        json=[
            {"id": 1, "uid": "abc", "title": "Prod", "tags": ["prod"], "isStarred": True}
        ],
    )
    result = ListDashboardsOutput.model_validate(
        await list_dashboards.ainvoke(_args())
    )
    assert result.success is True
    assert result.dashboards[0].uid == "abc"
    assert result.dashboards[0].is_starred is True


@pytest.mark.asyncio
async def test_get_dashboard(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/dashboards/uid/abc",
        json={"dashboard": {"uid": "abc", "title": "Prod"}, "meta": {"version": 3}},
    )
    result = GetDashboardOutput.model_validate(
        await get_dashboard.ainvoke(_args(dashboard_uid="abc"))
    )
    assert result.success is True
    assert result.dashboard == {"uid": "abc", "title": "Prod"}
    assert result.meta == {"version": 3}


@pytest.mark.asyncio
async def test_create_dashboard(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/api/dashboards/db",
        json={
            "id": 2,
            "uid": "new",
            "url": "/d/new",
            "status": "success",
            "version": 1,
            "slug": "x",
        },
    )
    result = CreateDashboardOutput.model_validate(
        await create_dashboard.ainvoke(_args(title="X"))
    )
    assert result.success is True
    assert result.uid == "new"
    assert result.status == "success"


@pytest.mark.asyncio
async def test_update_dashboard(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/dashboards/uid/abc",
        json={"dashboard": {"uid": "abc", "title": "Old", "version": 2}, "meta": {}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/api/dashboards/db",
        json={
            "id": 1,
            "uid": "abc",
            "url": "/d/abc",
            "status": "success",
            "version": 3,
            "slug": "y",
        },
    )
    result = UpdateDashboardOutput.model_validate(
        await update_dashboard.ainvoke(_args(dashboard_uid="abc", title="New"))
    )
    assert result.success is True
    assert result.version == 3


@pytest.mark.asyncio
async def test_delete_dashboard(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{BASE}/api/dashboards/uid/abc",
        json={"title": "Prod", "message": "Dashboard Prod deleted", "id": 1},
    )
    result = DeleteDashboardOutput.model_validate(
        await delete_dashboard.ainvoke(_args(dashboard_uid="abc"))
    )
    assert result.success is True
    assert result.id == 1


# --- Happy-path: alert rules ------------------------------------------------


@pytest.mark.asyncio
async def test_list_alert_rules(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/v1/provisioning/alert-rules",
        json=[{"uid": "r1", "title": "High CPU", "for": "5m", "isPaused": False}],
    )
    result = ListAlertRulesOutput.model_validate(
        await list_alert_rules.ainvoke(_args())
    )
    assert result.success is True
    assert result.rules[0].uid == "r1"
    assert result.rules[0].for_ == "5m"


@pytest.mark.asyncio
async def test_get_alert_rule(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/v1/provisioning/alert-rules/r1",
        json={"uid": "r1", "title": "High CPU", "condition": "C"},
    )
    result = GetAlertRuleOutput.model_validate(
        await get_alert_rule.ainvoke(_args(alert_rule_uid="r1"))
    )
    assert result.success is True
    assert result.rule is not None
    assert result.rule.condition == "C"


@pytest.mark.asyncio
async def test_create_alert_rule(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/api/v1/provisioning/alert-rules",
        status_code=201,
        json={"uid": "r2", "title": "Mem", "folderUID": "f1", "ruleGroup": "g1"},
    )
    result = CreateAlertRuleOutput.model_validate(
        await create_alert_rule.ainvoke(
            _args(
                title="Mem",
                folder_uid="f1",
                rule_group="g1",
                data='[{"refId":"A"}]',
            )
        )
    )
    assert result.success is True
    assert result.rule is not None
    assert result.rule.uid == "r2"
    assert result.rule.folder_uid == "f1"


@pytest.mark.asyncio
async def test_update_alert_rule(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/v1/provisioning/alert-rules/r1",
        json={"uid": "r1", "title": "Old", "folderUID": "f1", "ruleGroup": "g1", "data": []},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE}/api/v1/provisioning/alert-rules/r1",
        json={"uid": "r1", "title": "New", "folderUID": "f1", "ruleGroup": "g1"},
    )
    result = UpdateAlertRuleOutput.model_validate(
        await update_alert_rule.ainvoke(_args(alert_rule_uid="r1", title="New"))
    )
    assert result.success is True
    assert result.rule is not None
    assert result.rule.title == "New"


@pytest.mark.asyncio
async def test_delete_alert_rule(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{BASE}/api/v1/provisioning/alert-rules/r1",
        status_code=204,
    )
    result = DeleteAlertRuleOutput.model_validate(
        await delete_alert_rule.ainvoke(_args(alert_rule_uid="r1"))
    )
    assert result.success is True
    assert result.message is not None


# --- Happy-path: contact points ---------------------------------------------


@pytest.mark.asyncio
async def test_list_contact_points(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/v1/provisioning/contact-points",
        json=[{"uid": "cp1", "name": "Slack", "type": "slack", "settings": {"url": "x"}}],
    )
    result = ListContactPointsOutput.model_validate(
        await list_contact_points.ainvoke(_args())
    )
    assert result.success is True
    assert result.contact_points[0].name == "Slack"


@pytest.mark.asyncio
async def test_create_contact_point(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/api/v1/provisioning/contact-points",
        status_code=202,
        json={"uid": "cp2", "name": "Email", "type": "email", "settings": {"addresses": "a@b.com"}},
    )
    result = CreateContactPointOutput.model_validate(
        await create_contact_point.ainvoke(
            _args(name="Email", type="email", settings='{"addresses":"a@b.com"}')
        )
    )
    assert result.success is True
    assert result.uid == "cp2"


# --- Happy-path: annotations ------------------------------------------------


@pytest.mark.asyncio
async def test_create_annotation(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/api/annotations",
        json={"id": 11, "message": "Annotation added"},
    )
    result = CreateAnnotationOutput.model_validate(
        await create_annotation.ainvoke(_args(text="Deploy v1", tags="deploy,prod"))
    )
    assert result.success is True
    assert result.id == 11


@pytest.mark.asyncio
async def test_list_annotations(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/annotations?limit=10",
        json=[{"id": 11, "text": "Deploy", "tags": ["deploy"], "time": 1700000000000}],
    )
    result = ListAnnotationsOutput.model_validate(
        await list_annotations.ainvoke(_args(limit=10))
    )
    assert result.success is True
    assert result.annotations[0].id == 11
    assert result.annotations[0].text == "Deploy"


@pytest.mark.asyncio
async def test_update_annotation(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{BASE}/api/annotations/11",
        json={"id": 11, "message": "Annotation patched"},
    )
    result = UpdateAnnotationOutput.model_validate(
        await update_annotation.ainvoke(_args(annotation_id=11, text="Deploy v2"))
    )
    assert result.success is True
    assert result.id == 11


@pytest.mark.asyncio
async def test_delete_annotation(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{BASE}/api/annotations/11",
        json={"message": "Annotation deleted"},
    )
    result = DeleteAnnotationOutput.model_validate(
        await delete_annotation.ainvoke(_args(annotation_id=11))
    )
    assert result.success is True
    assert result.message == "Annotation deleted"


# --- Happy-path: data sources -----------------------------------------------


@pytest.mark.asyncio
async def test_list_data_sources(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/datasources",
        json=[{"id": 1, "uid": "ds1", "name": "Prometheus", "type": "prometheus"}],
    )
    result = ListDataSourcesOutput.model_validate(
        await list_data_sources.ainvoke(_args())
    )
    assert result.success is True
    assert result.data_sources[0].name == "Prometheus"


@pytest.mark.asyncio
async def test_get_data_source_by_uid(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/datasources/uid/P123",
        json={"id": 1, "uid": "P123", "name": "Prom", "type": "prometheus"},
    )
    result = GetDataSourceOutput.model_validate(
        await get_data_source.ainvoke(_args(data_source_id="P123"))
    )
    assert result.success is True
    assert result.data_source is not None
    assert result.data_source.uid == "P123"


@pytest.mark.asyncio
async def test_get_data_source_by_numeric_id(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/datasources/5",
        json={"id": 5, "uid": "P5", "name": "Loki", "type": "loki"},
    )
    result = GetDataSourceOutput.model_validate(
        await get_data_source.ainvoke(_args(data_source_id="5"))
    )
    assert result.success is True
    assert result.data_source is not None
    assert result.data_source.id == 5


@pytest.mark.asyncio
async def test_check_data_source_health(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/datasources/uid/P123/health",
        json={"status": "OK", "message": "Data source is working"},
    )
    result = CheckDataSourceHealthOutput.model_validate(
        await check_data_source_health.ainvoke(_args(data_source_uid="P123"))
    )
    assert result.success is True
    assert result.status == "OK"


# --- Happy-path: folders ----------------------------------------------------


@pytest.mark.asyncio
async def test_list_folders(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/folders",
        json=[{"id": 1, "uid": "f1", "title": "Prod"}],
    )
    result = ListFoldersOutput.model_validate(
        await list_folders.ainvoke(_args())
    )
    assert result.success is True
    assert result.folders[0].uid == "f1"


@pytest.mark.asyncio
async def test_create_folder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/api/folders",
        status_code=200,
        json={"id": 2, "uid": "f2", "title": "Staging", "version": 1},
    )
    result = CreateFolderOutput.model_validate(
        await create_folder.ainvoke(_args(title="Staging"))
    )
    assert result.success is True
    assert result.folder is not None
    assert result.folder.uid == "f2"


@pytest.mark.asyncio
async def test_get_folder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/folders/f1",
        json={"id": 1, "uid": "f1", "title": "Prod", "version": 4},
    )
    result = GetFolderOutput.model_validate(
        await get_folder.ainvoke(_args(folder_uid="f1"))
    )
    assert result.success is True
    assert result.folder is not None
    assert result.folder.title == "Prod"


@pytest.mark.asyncio
async def test_update_folder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/folders/f1",
        json={"id": 1, "uid": "f1", "title": "Old", "version": 4},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE}/api/folders/f1",
        json={"id": 1, "uid": "f1", "title": "New", "version": 5},
    )
    result = UpdateFolderOutput.model_validate(
        await update_folder.ainvoke(_args(folder_uid="f1", title="New"))
    )
    assert result.success is True
    assert result.folder is not None
    assert result.folder.title == "New"


@pytest.mark.asyncio
async def test_delete_folder(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{BASE}/api/folders/f1",
        json={"message": "Folder deleted"},
    )
    result = DeleteFolderOutput.model_validate(
        await delete_folder.ainvoke(_args(folder_uid="f1"))
    )
    assert result.success is True
    assert result.uid == "f1"


# --- Happy-path: health -----------------------------------------------------


@pytest.mark.asyncio
async def test_get_health(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/health",
        json={"commit": "abc123", "database": "ok", "version": "11.0.0"},
    )
    result = GetHealthOutput.model_validate(await get_health.ainvoke(_args()))
    assert result.success is True
    assert result.database == "ok"
    assert result.version == "11.0.0"


@pytest.mark.asyncio
async def test_org_id_header_sent(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/health",
        json={"commit": "c", "database": "ok", "version": "11.0.0"},
    )
    await get_health.ainvoke(_args(organization_id="2"))
    sent = httpx_mock.get_requests()[0]
    assert sent.headers["X-Grafana-Org-Id"] == "2"
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


# --- Failure paths ----------------------------------------------------------


@pytest.mark.asyncio
async def test_get_health_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Non-2xx responses surface as success=False + error, not an exception."""
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/api/health",
        status_code=401,
        text="Unauthorized",
    )
    result = GetHealthOutput.model_validate(await get_health.ainvoke(_args()))
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_create_alert_rule_invalid_json() -> None:
    """Malformed JSON for the data parameter short-circuits before HTTP."""
    result = CreateAlertRuleOutput.model_validate(
        await create_alert_rule.ainvoke(
            _args(title="X", folder_uid="f1", rule_group="g1", data="not-json")
        )
    )
    assert result.success is False
    assert result.error is not None
    assert "data" in result.error


@pytest.mark.asyncio
async def test_list_dashboards_validates_empty_api_key() -> None:
    result = ListDashboardsOutput.model_validate(
        await list_dashboards.ainvoke({"api_key": "", "base_url": BASE})
    )
    assert result.success is False
    assert result.error is not None
    assert "token" in result.error


@pytest.mark.asyncio
async def test_get_health_validates_empty_base_url() -> None:
    result = GetHealthOutput.model_validate(
        await get_health.ainvoke({"api_key": _API_KEY, "base_url": ""})
    )
    assert result.success is False
    assert result.error is not None
    assert "URL" in result.error
