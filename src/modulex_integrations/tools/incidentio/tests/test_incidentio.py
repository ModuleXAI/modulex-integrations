"""Happy-path tests per action + a failure-path and empty-credential test.

incident.io doesn't raise on non-2xx — the tools catch and return
``success=False`` + ``error``. Tests assert dict at the @tool boundary and
roundtrip through the output model.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.incidentio import (
    TOOLS,
    actions_list,
    actions_show,
    custom_fields_create,
    custom_fields_delete,
    custom_fields_list,
    custom_fields_show,
    custom_fields_update,
    escalation_paths_create,
    escalation_paths_delete,
    escalation_paths_list,
    escalation_paths_show,
    escalation_paths_update,
    escalations_create,
    escalations_list,
    escalations_show,
    follow_ups_list,
    follow_ups_show,
    incident_roles_create,
    incident_roles_delete,
    incident_roles_list,
    incident_roles_show,
    incident_roles_update,
    incident_statuses_list,
    incident_timestamps_list,
    incident_timestamps_show,
    incident_types_list,
    incident_updates_list,
    incidents_create,
    incidents_list,
    incidents_show,
    incidents_update,
    manifest,
    schedule_entries_list,
    schedule_overrides_create,
    schedules_create,
    schedules_delete,
    schedules_list,
    schedules_show,
    schedules_update,
    severities_list,
    users_list,
    users_show,
    workflows_create,
    workflows_delete,
    workflows_list,
    workflows_show,
    workflows_update,
)
from modulex_integrations.tools.incidentio.outputs import (
    ActionsListOutput,
    ActionsShowOutput,
    CustomFieldsCreateOutput,
    CustomFieldsDeleteOutput,
    CustomFieldsListOutput,
    CustomFieldsShowOutput,
    CustomFieldsUpdateOutput,
    EscalationPathsCreateOutput,
    EscalationPathsDeleteOutput,
    EscalationPathsListOutput,
    EscalationPathsShowOutput,
    EscalationPathsUpdateOutput,
    EscalationsCreateOutput,
    EscalationsListOutput,
    EscalationsShowOutput,
    FollowUpsListOutput,
    FollowUpsShowOutput,
    IncidentRolesCreateOutput,
    IncidentRolesDeleteOutput,
    IncidentRolesListOutput,
    IncidentRolesShowOutput,
    IncidentRolesUpdateOutput,
    IncidentsCreateOutput,
    IncidentsListOutput,
    IncidentsShowOutput,
    IncidentStatusesListOutput,
    IncidentsUpdateOutput,
    IncidentTimestampsListOutput,
    IncidentTimestampsShowOutput,
    IncidentTypesListOutput,
    IncidentUpdatesListOutput,
    ScheduleEntriesListOutput,
    ScheduleOverridesCreateOutput,
    SchedulesCreateOutput,
    SchedulesDeleteOutput,
    SchedulesListOutput,
    SchedulesShowOutput,
    SchedulesUpdateOutput,
    SeveritiesListOutput,
    UsersListOutput,
    UsersShowOutput,
    WorkflowsCreateOutput,
    WorkflowsDeleteOutput,
    WorkflowsListOutput,
    WorkflowsShowOutput,
    WorkflowsUpdateOutput,
)

API = "https://api.incident.io"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_46_actions(self) -> None:
        assert len(manifest.actions) == 46

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo(self) -> None:
        assert manifest.logo == "modulex:incidentio-themed"


# --- Incidents -------------------------------------------------------------


@pytest.mark.asyncio
async def test_incidents_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/incidents?page_size=2",
        json={
            "incidents": [{"id": "01ABC", "name": "DB down"}],
            "pagination_meta": {"after": "cur1", "page_size": 2},
        },
    )
    result_dict = await incidents_list.ainvoke(_args(page_size=2))
    assert isinstance(result_dict, dict)
    result = IncidentsListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incidents[0]["name"] == "DB down"
    assert result.pagination_meta == {"after": "cur1", "page_size": 2}
    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_incidents_create(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/incidents",
        json={"incident": {"id": "01NEW", "name": "Outage"}},
    )
    result_dict = await incidents_create.ainvoke(
        _args(idempotency_key="k1", severity_id="sev1", visibility="public", name="Outage")
    )
    assert isinstance(result_dict, dict)
    result = IncidentsCreateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident == {"id": "01NEW", "name": "Outage"}


@pytest.mark.asyncio
async def test_incidents_show(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/incidents/01ABC",
        json={"incident": {"id": "01ABC", "permalink": "https://x"}},
    )
    result_dict = await incidents_show.ainvoke(_args(id="01ABC"))
    assert isinstance(result_dict, dict)
    result = IncidentsShowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident is not None
    assert result.incident["id"] == "01ABC"


@pytest.mark.asyncio
async def test_incidents_update(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/incidents/01ABC/actions/edit",
        json={"incident": {"id": "01ABC", "name": "Renamed"}},
    )
    result_dict = await incidents_update.ainvoke(
        _args(id="01ABC", notify_incident_channel=True, name="Renamed")
    )
    assert isinstance(result_dict, dict)
    result = IncidentsUpdateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident is not None
    assert result.incident["name"] == "Renamed"


# --- Actions ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_actions_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/actions",
        json={"actions": [{"id": "act1", "status": "outstanding"}]},
    )
    result_dict = await actions_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ActionsListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.actions[0]["id"] == "act1"


@pytest.mark.asyncio
async def test_actions_show(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/actions/act1",
        json={"action": {"id": "act1", "description": "Investigate"}},
    )
    result_dict = await actions_show.ainvoke(_args(id="act1"))
    assert isinstance(result_dict, dict)
    result = ActionsShowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.action is not None
    assert result.action["description"] == "Investigate"


# --- Follow-ups ------------------------------------------------------------


@pytest.mark.asyncio
async def test_follow_ups_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/follow_ups",
        json={"follow_ups": [{"id": "fu1", "title": "Write postmortem"}]},
    )
    result_dict = await follow_ups_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = FollowUpsListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.follow_ups[0]["title"] == "Write postmortem"


@pytest.mark.asyncio
async def test_follow_ups_show(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/follow_ups/fu1",
        json={"follow_up": {"id": "fu1", "title": "Write postmortem"}},
    )
    result_dict = await follow_ups_show.ainvoke(_args(id="fu1"))
    assert isinstance(result_dict, dict)
    result = FollowUpsShowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.follow_up is not None
    assert result.follow_up["id"] == "fu1"


# --- Users -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_users_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/users",
        json={
            "users": [{"id": "u1", "name": "Alice", "email": "a@x.io", "role": "admin"}],
            "pagination_meta": {"after": "c", "page_size": 25},
        },
    )
    result_dict = await users_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = UsersListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.users[0]["name"] == "Alice"


@pytest.mark.asyncio
async def test_users_show(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/users/u1",
        json={"user": {"id": "u1", "name": "Alice"}},
    )
    result_dict = await users_show.ainvoke(_args(id="u1"))
    assert isinstance(result_dict, dict)
    result = UsersShowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user is not None
    assert result.user["name"] == "Alice"


# --- Workflows -------------------------------------------------------------


@pytest.mark.asyncio
async def test_workflows_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/workflows",
        json={"workflows": [{"id": "wf1", "name": "Notify"}]},
    )
    result_dict = await workflows_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = WorkflowsListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.workflows[0]["name"] == "Notify"


@pytest.mark.asyncio
async def test_workflows_create(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/workflows",
        json={"workflow": {"id": "wf1", "name": "Notify"}, "management_meta": {"k": "v"}},
    )
    result_dict = await workflows_create.ainvoke(_args(name="Notify"))
    assert isinstance(result_dict, dict)
    result = WorkflowsCreateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.workflow is not None
    assert result.workflow["name"] == "Notify"
    assert result.management_meta == {"k": "v"}


@pytest.mark.asyncio
async def test_workflows_show(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/workflows/wf1",
        json={"workflow": {"id": "wf1", "name": "Notify"}},
    )
    result_dict = await workflows_show.ainvoke(_args(id="wf1"))
    assert isinstance(result_dict, dict)
    result = WorkflowsShowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.workflow is not None
    assert result.workflow["id"] == "wf1"


@pytest.mark.asyncio
async def test_workflows_update(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/v2/workflows/wf1",
        json={"workflow": {"id": "wf1", "name": "Renamed"}},
    )
    result_dict = await workflows_update.ainvoke(
        _args(
            id="wf1",
            name="Renamed",
            steps=[],
            condition_groups=[],
            runs_on_incidents="all",
            runs_on_incident_modes=["standard"],
            include_private_incidents=True,
            continue_on_step_error=False,
            once_for=[],
            expressions=[],
        )
    )
    assert isinstance(result_dict, dict)
    result = WorkflowsUpdateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.workflow is not None
    assert result.workflow["name"] == "Renamed"


@pytest.mark.asyncio
async def test_workflows_delete(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/v2/workflows/wf1", status_code=204)
    result_dict = await workflows_delete.ainvoke(_args(id="wf1"))
    assert isinstance(result_dict, dict)
    result = WorkflowsDeleteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message == "Workflow deleted successfully"


# --- Schedules -------------------------------------------------------------


@pytest.mark.asyncio
async def test_schedules_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/schedules",
        json={"schedules": [{"id": "s1", "name": "Primary"}]},
    )
    result_dict = await schedules_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = SchedulesListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.schedules[0]["name"] == "Primary"


@pytest.mark.asyncio
async def test_schedules_create(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/schedules",
        json={"schedule": {"id": "s1", "name": "Primary"}},
    )
    result_dict = await schedules_create.ainvoke(
        _args(name="Primary", timezone="UTC", rotations_config={"rotations": []})
    )
    assert isinstance(result_dict, dict)
    result = SchedulesCreateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.schedule is not None
    assert result.schedule["name"] == "Primary"


@pytest.mark.asyncio
async def test_schedules_show(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/schedules/s1",
        json={"schedule": {"id": "s1", "timezone": "UTC"}},
    )
    result_dict = await schedules_show.ainvoke(_args(id="s1"))
    assert isinstance(result_dict, dict)
    result = SchedulesShowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.schedule is not None
    assert result.schedule["timezone"] == "UTC"


@pytest.mark.asyncio
async def test_schedules_update(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/v2/schedules/s1",
        json={"schedule": {"id": "s1", "name": "Renamed"}},
    )
    result_dict = await schedules_update.ainvoke(_args(id="s1", name="Renamed"))
    assert isinstance(result_dict, dict)
    result = SchedulesUpdateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.schedule is not None
    assert result.schedule["name"] == "Renamed"


@pytest.mark.asyncio
async def test_schedules_delete(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/v2/schedules/s1", status_code=204)
    result_dict = await schedules_delete.ainvoke(_args(id="s1"))
    assert isinstance(result_dict, dict)
    result = SchedulesDeleteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message == "Schedule deleted successfully"


# --- Escalations -----------------------------------------------------------


@pytest.mark.asyncio
async def test_escalations_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/escalations",
        json={"escalations": [{"id": "e1", "name": "Crit"}]},
    )
    result_dict = await escalations_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = EscalationsListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.escalations[0]["id"] == "e1"


@pytest.mark.asyncio
async def test_escalations_create(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/escalations",
        json={"escalation": {"id": "e1", "title": "Crit"}},
    )
    result_dict = await escalations_create.ainvoke(
        _args(idempotency_key="k1", title="Crit", user_ids="u1,u2")
    )
    assert isinstance(result_dict, dict)
    result = EscalationsCreateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.escalation is not None
    assert result.escalation["id"] == "e1"


@pytest.mark.asyncio
async def test_escalations_show(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/escalations/e1",
        json={"escalation": {"id": "e1", "name": "Crit"}},
    )
    result_dict = await escalations_show.ainvoke(_args(id="e1"))
    assert isinstance(result_dict, dict)
    result = EscalationsShowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.escalation is not None
    assert result.escalation["id"] == "e1"


# --- Custom Fields ---------------------------------------------------------


@pytest.mark.asyncio
async def test_custom_fields_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/custom_fields",
        json={"custom_fields": [{"id": "cf1", "name": "Service"}]},
    )
    result_dict = await custom_fields_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = CustomFieldsListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.custom_fields[0]["name"] == "Service"


@pytest.mark.asyncio
async def test_custom_fields_create(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/custom_fields",
        json={"custom_field": {"id": "cf1", "name": "Service"}},
    )
    result_dict = await custom_fields_create.ainvoke(
        _args(name="Service", description="Affected service", field_type="text")
    )
    assert isinstance(result_dict, dict)
    result = CustomFieldsCreateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.custom_field is not None
    assert result.custom_field["name"] == "Service"


@pytest.mark.asyncio
async def test_custom_fields_show(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/custom_fields/cf1",
        json={"custom_field": {"id": "cf1", "field_type": "text"}},
    )
    result_dict = await custom_fields_show.ainvoke(_args(id="cf1"))
    assert isinstance(result_dict, dict)
    result = CustomFieldsShowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.custom_field is not None
    assert result.custom_field["field_type"] == "text"


@pytest.mark.asyncio
async def test_custom_fields_update(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/v2/custom_fields/cf1",
        json={"custom_field": {"id": "cf1", "name": "Renamed"}},
    )
    result_dict = await custom_fields_update.ainvoke(
        _args(id="cf1", name="Renamed", description="Updated")
    )
    assert isinstance(result_dict, dict)
    result = CustomFieldsUpdateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.custom_field is not None
    assert result.custom_field["name"] == "Renamed"


@pytest.mark.asyncio
async def test_custom_fields_delete(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/v2/custom_fields/cf1", status_code=204)
    result_dict = await custom_fields_delete.ainvoke(_args(id="cf1"))
    assert isinstance(result_dict, dict)
    result = CustomFieldsDeleteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message == "Custom field successfully deleted"


# --- Reference data --------------------------------------------------------


@pytest.mark.asyncio
async def test_severities_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/severities",
        json={"severities": [{"id": "sev1", "name": "Critical", "rank": 1}]},
    )
    result_dict = await severities_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = SeveritiesListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.severities[0]["name"] == "Critical"


@pytest.mark.asyncio
async def test_incident_statuses_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/incident_statuses",
        json={"incident_statuses": [{"id": "st1", "name": "Investigating"}]},
    )
    result_dict = await incident_statuses_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = IncidentStatusesListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident_statuses[0]["name"] == "Investigating"


@pytest.mark.asyncio
async def test_incident_types_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/incident_types",
        json={"incident_types": [{"id": "it1", "name": "Default", "is_default": True}]},
    )
    result_dict = await incident_types_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = IncidentTypesListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident_types[0]["is_default"] is True


# --- Incident Roles --------------------------------------------------------


@pytest.mark.asyncio
async def test_incident_roles_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/incident_roles",
        json={"incident_roles": [{"id": "r1", "name": "Commander"}]},
    )
    result_dict = await incident_roles_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = IncidentRolesListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident_roles[0]["name"] == "Commander"


@pytest.mark.asyncio
async def test_incident_roles_create(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/incident_roles",
        json={"incident_role": {"id": "r1", "name": "Commander"}},
    )
    result_dict = await incident_roles_create.ainvoke(
        _args(name="Commander", description="Leads", instructions="Do x", shortform="IC")
    )
    assert isinstance(result_dict, dict)
    result = IncidentRolesCreateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident_role is not None
    assert result.incident_role["name"] == "Commander"


@pytest.mark.asyncio
async def test_incident_roles_show(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/incident_roles/r1",
        json={"incident_role": {"id": "r1", "shortform": "IC"}},
    )
    result_dict = await incident_roles_show.ainvoke(_args(id="r1"))
    assert isinstance(result_dict, dict)
    result = IncidentRolesShowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident_role is not None
    assert result.incident_role["shortform"] == "IC"


@pytest.mark.asyncio
async def test_incident_roles_update(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/v2/incident_roles/r1",
        json={"incident_role": {"id": "r1", "name": "Lead"}},
    )
    result_dict = await incident_roles_update.ainvoke(
        _args(id="r1", name="Lead", description="d", instructions="i", shortform="LD")
    )
    assert isinstance(result_dict, dict)
    result = IncidentRolesUpdateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident_role is not None
    assert result.incident_role["name"] == "Lead"


@pytest.mark.asyncio
async def test_incident_roles_delete(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/v2/incident_roles/r1", status_code=204)
    result_dict = await incident_roles_delete.ainvoke(_args(id="r1"))
    assert isinstance(result_dict, dict)
    result = IncidentRolesDeleteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message == "Incident role deleted successfully"


# --- Incident Timestamps ---------------------------------------------------


@pytest.mark.asyncio
async def test_incident_timestamps_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/incident_timestamps",
        json={"incident_timestamps": [{"id": "ts1", "name": "Reported", "rank": 1}]},
    )
    result_dict = await incident_timestamps_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = IncidentTimestampsListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident_timestamps[0]["name"] == "Reported"


@pytest.mark.asyncio
async def test_incident_timestamps_show(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/incident_timestamps/ts1",
        json={"incident_timestamp": {"id": "ts1", "rank": 1}},
    )
    result_dict = await incident_timestamps_show.ainvoke(_args(id="ts1"))
    assert isinstance(result_dict, dict)
    result = IncidentTimestampsShowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident_timestamp is not None
    assert result.incident_timestamp["rank"] == 1


# --- Incident Updates ------------------------------------------------------


@pytest.mark.asyncio
async def test_incident_updates_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/incident_updates",
        json={"incident_updates": [{"id": "iu1", "message": "Investigating"}]},
    )
    result_dict = await incident_updates_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = IncidentUpdatesListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.incident_updates[0]["message"] == "Investigating"


# --- Schedule Entries ------------------------------------------------------


@pytest.mark.asyncio
async def test_schedule_entries_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/schedule_entries?schedule_id=s1",
        json={
            "schedule_entries": {
                "final": [{"entry_id": "ent1"}],
                "overrides": [],
                "scheduled": [],
            }
        },
    )
    result_dict = await schedule_entries_list.ainvoke(_args(schedule_id="s1"))
    assert isinstance(result_dict, dict)
    result = ScheduleEntriesListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.schedule_entries is not None
    assert result.schedule_entries["final"][0]["entry_id"] == "ent1"
    assert result.schedule_entries["overrides"] == []


# --- Schedule Overrides ----------------------------------------------------


@pytest.mark.asyncio
async def test_schedule_overrides_create(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/schedule_overrides",
        json={"override": {"id": "ov1", "schedule_id": "s1"}},
    )
    result_dict = await schedule_overrides_create.ainvoke(
        _args(
            rotation_id="rot1",
            layer_id="lay1",
            schedule_id="s1",
            start_at="2024-01-01T00:00:00Z",
            end_at="2024-01-02T00:00:00Z",
            user_id="u1",
        )
    )
    assert isinstance(result_dict, dict)
    result = ScheduleOverridesCreateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.override is not None
    assert result.override["id"] == "ov1"


# --- Escalation Paths ------------------------------------------------------


@pytest.mark.asyncio
async def test_escalation_paths_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/escalation_paths",
        json={"escalation_paths": [{"id": "ep1", "name": "Crit Path"}]},
    )
    result_dict = await escalation_paths_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = EscalationPathsListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.escalation_paths[0]["name"] == "Crit Path"


@pytest.mark.asyncio
async def test_escalation_paths_create(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v2/escalation_paths",
        json={"escalation_path": {"id": "ep1", "name": "Crit Path"}},
    )
    result_dict = await escalation_paths_create.ainvoke(
        _args(
            name="Crit Path",
            path=[{"targets": [{"id": "u1", "type": "user", "urgency": "high"}],
                   "time_to_ack_seconds": 300}],
        )
    )
    assert isinstance(result_dict, dict)
    result = EscalationPathsCreateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.escalation_path is not None
    assert result.escalation_path["name"] == "Crit Path"


@pytest.mark.asyncio
async def test_escalation_paths_show(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/escalation_paths/ep1",
        json={"escalation_path": {"id": "ep1", "name": "Crit Path"}},
    )
    result_dict = await escalation_paths_show.ainvoke(_args(id="ep1"))
    assert isinstance(result_dict, dict)
    result = EscalationPathsShowOutput.model_validate(result_dict)
    assert result.success is True
    assert result.escalation_path is not None
    assert result.escalation_path["id"] == "ep1"


@pytest.mark.asyncio
async def test_escalation_paths_update(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/v2/escalation_paths/ep1",
        json={"escalation_path": {"id": "ep1", "name": "Renamed"}},
    )
    result_dict = await escalation_paths_update.ainvoke(
        _args(id="ep1", name="Renamed", path=[])
    )
    assert isinstance(result_dict, dict)
    result = EscalationPathsUpdateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.escalation_path is not None
    assert result.escalation_path["name"] == "Renamed"


@pytest.mark.asyncio
async def test_escalation_paths_delete(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/v2/escalation_paths/ep1", status_code=204)
    result_dict = await escalation_paths_delete.ainvoke(_args(id="ep1"))
    assert isinstance(result_dict, dict)
    result = EscalationPathsDeleteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message == "Escalation path deleted successfully"


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_incidents_list_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Non-2xx is caught and returned as success=False + error, not raised."""
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v2/incidents",
        status_code=401,
        text="Unauthorized",
    )
    result_dict = await incidents_list.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = IncidentsListOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_incidents_list_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await incidents_list.ainvoke({"api_key": ""})
    assert isinstance(result_dict, dict)
    result = IncidentsListOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
