"""incident.io LangChain ``@tool`` functions.

46 async tools wrapping the incident.io REST API
(``https://api.incident.io``). These use the modulex *api_key* runtime
convention: the ``ToolExecutor`` injects an ``api_key: str`` directly
(resolved from the user's credential) rather than an
``auth_type``/``auth_data`` pair. The key is sent as
``Authorization: Bearer {api_key}``.

Error model: every call is wrapped in try/except. Non-2xx HTTP responses
do *not* raise — they return the typed output with ``success=False`` +
``error``. Timeouts and unexpected exceptions are handled the same way.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
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

__all__ = [
    "actions_list",
    "actions_show",
    "custom_fields_create",
    "custom_fields_delete",
    "custom_fields_list",
    "custom_fields_show",
    "custom_fields_update",
    "escalation_paths_create",
    "escalation_paths_delete",
    "escalation_paths_list",
    "escalation_paths_show",
    "escalation_paths_update",
    "escalations_create",
    "escalations_list",
    "escalations_show",
    "follow_ups_list",
    "follow_ups_show",
    "incident_roles_create",
    "incident_roles_delete",
    "incident_roles_list",
    "incident_roles_show",
    "incident_roles_update",
    "incident_statuses_list",
    "incident_timestamps_list",
    "incident_timestamps_show",
    "incident_types_list",
    "incident_updates_list",
    "incidents_create",
    "incidents_list",
    "incidents_show",
    "incidents_update",
    "schedule_entries_list",
    "schedule_overrides_create",
    "schedules_create",
    "schedules_delete",
    "schedules_list",
    "schedules_show",
    "schedules_update",
    "severities_list",
    "users_list",
    "users_show",
    "workflows_create",
    "workflows_delete",
    "workflows_list",
    "workflows_show",
    "workflows_update",
]

_BASE_URL = "https://api.incident.io"
_TIMEOUT = 30.0
_EMPTY_KEY_ERROR = (
    "incident.io API key is empty. Please configure a valid incident.io credential."
)


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }


async def _request(
    method: str,
    path: str,
    api_key: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Perform a single incident.io API call.

    Returns ``(data, None)`` on success or ``(None, error_message)`` on
    failure. Successful DELETE/204 responses with no JSON body return
    ``({}, None)``.
    """
    url = f"{_BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                method,
                url,
                headers=_headers(api_key),
                params=params,
                json=json_body,
            )
        if response.status_code < 200 or response.status_code >= 300:
            return None, f"incident.io API error ({response.status_code}): {response.text}"
        if not response.content:
            return {}, None
        try:
            data: dict[str, Any] = response.json()
        except ValueError:
            return {}, None
        return data, None
    except httpx.TimeoutException:
        return None, "Request timed out."
    except Exception as exc:
        return None, f"Request failed: {exc}"


# --- Input schemas ---------------------------------------------------------


class IncidentsListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    page_size: int | None = Field(
        default=None, description="Number of incidents to return per page (e.g., 10, 25, 50)"
    )
    after: str | None = Field(
        default=None, description="Pagination cursor to fetch the next page of results"
    )
    sort_by: str | None = Field(
        default=None,
        description="Sort order: 'created_at_newest_first' or 'created_at_oldest_first'",
    )
    filter_mode: str | None = Field(
        default=None, description="How to combine filters: 'all' or 'any'"
    )


class IncidentsCreateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    idempotency_key: str = Field(
        description="Unique identifier to prevent duplicate incident creation (e.g., a UUID)"
    )
    severity_id: str = Field(description="ID of the severity level")
    visibility: str = Field(description="Visibility of the incident: 'public' or 'private'")
    name: str | None = Field(default=None, description="Name of the incident")
    summary: str | None = Field(default=None, description="Brief summary of the incident")
    incident_type_id: str | None = Field(default=None, description="ID of the incident type")
    incident_status_id: str | None = Field(
        default=None, description="ID of the initial incident status"
    )


class IncidentsShowInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="ID of the incident to retrieve")


class IncidentsUpdateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="ID of the incident to update")
    notify_incident_channel: bool = Field(
        description="Whether to notify the incident channel about this update"
    )
    name: str | None = Field(default=None, description="Updated name of the incident")
    summary: str | None = Field(default=None, description="Updated summary of the incident")
    severity_id: str | None = Field(default=None, description="Updated severity ID")
    incident_status_id: str | None = Field(default=None, description="Updated status ID")
    incident_type_id: str | None = Field(default=None, description="Updated incident type ID")


class ActionsListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    incident_id: str | None = Field(default=None, description="Filter actions by incident ID")
    incident_mode: str | None = Field(
        default=None,
        description="Filter by incident mode: standard, retrospective, test, tutorial, or stream",
    )


class ActionsShowInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="Action ID")


class FollowUpsListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    incident_id: str | None = Field(default=None, description="Filter follow-ups by incident ID")
    incident_mode: str | None = Field(
        default=None,
        description="Filter by incident mode: standard, retrospective, test, tutorial, or stream",
    )


class FollowUpsShowInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="Follow-up ID")


class UsersListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    page_size: int | None = Field(
        default=None, description="Number of results to return per page (e.g., 10, 25, 50)"
    )
    after: str | None = Field(
        default=None, description="Pagination cursor to fetch the next page of results"
    )
    email: str | None = Field(default=None, description="Filter users by email address")
    slack_user_id: str | None = Field(default=None, description="Filter users by Slack user ID")


class UsersShowInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The unique identifier of the user to retrieve")


class WorkflowsListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")


class WorkflowsCreateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    name: str = Field(description="Name of the workflow")
    folder: str | None = Field(default=None, description="Folder to organize the workflow in")
    state: str = Field(
        default="draft", description="State of the workflow: active, draft, or disabled"
    )
    trigger: str = Field(
        default="incident.updated", description="Trigger type for the workflow"
    )
    steps: list[Any] | None = Field(
        default=None, description="Array of workflow steps (defaults to [])"
    )
    condition_groups: list[Any] | None = Field(
        default=None, description="Array of condition groups controlling when the workflow runs"
    )
    runs_on_incidents: str = Field(
        default="newly_created",
        description="When to run: newly_created, newly_created_and_active, active, or all",
    )
    runs_on_incident_modes: list[Any] | None = Field(
        default=None, description="Array of incident modes to run on (defaults to ['standard'])"
    )
    include_private_incidents: bool = Field(
        default=True, description="Whether to include private incidents"
    )
    continue_on_step_error: bool = Field(
        default=False, description="Whether to continue executing subsequent steps if one fails"
    )
    once_for: list[Any] | None = Field(
        default=None, description="Array of fields making the workflow run once per combination"
    )
    expressions: list[Any] | None = Field(
        default=None, description="Array of workflow expressions for advanced logic"
    )
    delay: dict[str, Any] | None = Field(
        default=None, description="Delay configuration object"
    )


class WorkflowsShowInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the workflow to retrieve")
    skip_step_upgrades: bool | None = Field(
        default=None,
        description="Skip workflow step upgrades when existing step parameters changed",
    )


class WorkflowsUpdateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the workflow to update")
    name: str = Field(description="New name for the workflow")
    steps: list[Any] = Field(description="Complete array of workflow steps")
    condition_groups: list[Any] = Field(description="Complete array of workflow condition groups")
    runs_on_incidents: str = Field(
        description="When to run: newly_created, newly_created_and_active, active, or all"
    )
    runs_on_incident_modes: list[Any] = Field(
        description="Complete array of incident modes to run on"
    )
    include_private_incidents: bool = Field(description="Whether to include private incidents")
    continue_on_step_error: bool = Field(
        description="Whether to continue executing subsequent steps if one fails"
    )
    once_for: list[Any] = Field(
        description="Complete array of fields that make the workflow run once"
    )
    expressions: list[Any] = Field(description="Complete array of workflow expressions")
    state: str | None = Field(default=None, description="New state: active, draft, or disabled")
    folder: str | None = Field(default=None, description="New folder for the workflow")
    delay: dict[str, Any] | None = Field(default=None, description="Delay configuration object")


class WorkflowsDeleteInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the workflow to delete")


class SchedulesListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    page_size: int | None = Field(default=None, description="Number of results per page")
    after: str | None = Field(default=None, description="Pagination cursor for the next page")


class SchedulesCreateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    name: str = Field(description="Name of the schedule")
    timezone: str = Field(description="Timezone for the schedule (e.g., America/New_York)")
    rotations_config: dict[str, Any] = Field(
        description="Schedule configuration object with rotations"
    )


class SchedulesShowInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the schedule")


class SchedulesUpdateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the schedule to update")
    name: str | None = Field(default=None, description="New name for the schedule")
    timezone: str | None = Field(default=None, description="New timezone for the schedule")
    rotations_config: dict[str, Any] | None = Field(
        default=None, description="Schedule configuration object with rotations"
    )


class SchedulesDeleteInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the schedule to delete")


class EscalationsListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    page_size: int | None = Field(default=None, description="Number of escalations per page")
    after: str | None = Field(default=None, description="Pagination cursor for the next page")


class EscalationsCreateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    idempotency_key: str = Field(
        description="Unique identifier to prevent duplicate escalation creation"
    )
    title: str = Field(description="Title of the escalation")
    escalation_path_id: str | None = Field(
        default=None, description="ID of the escalation path (required if user_ids not provided)"
    )
    user_ids: str | None = Field(
        default=None,
        description="Comma-separated user IDs to notify (required if no escalation_path_id)",
    )


class EscalationsShowInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the escalation policy")


class CustomFieldsListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")


class CustomFieldsCreateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    name: str = Field(description="Name of the custom field")
    description: str = Field(description="Description of the custom field")
    field_type: str = Field(
        description="Field type: text, single_select, multi_select, numeric, link, etc."
    )


class CustomFieldsShowInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="Custom field ID")


class CustomFieldsUpdateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="Custom field ID")
    name: str = Field(description="New name for the custom field")
    description: str = Field(description="New description for the custom field")


class CustomFieldsDeleteInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="Custom field ID")


class SeveritiesListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")


class IncidentStatusesListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")


class IncidentTypesListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")


class IncidentRolesListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")


class IncidentRolesCreateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    name: str = Field(description="Name of the incident role")
    description: str = Field(description="Description of the incident role")
    instructions: str = Field(description="Instructions for the incident role")
    shortform: str = Field(description="Short form abbreviation for the role")


class IncidentRolesShowInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the incident role")


class IncidentRolesUpdateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the incident role to update")
    name: str = Field(description="Name of the incident role")
    description: str = Field(description="Description of the incident role")
    instructions: str = Field(description="Instructions for the incident role")
    shortform: str = Field(description="Short form abbreviation for the role")


class IncidentRolesDeleteInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the incident role to delete")


class IncidentTimestampsListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")


class IncidentTimestampsShowInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the incident timestamp")


class IncidentUpdatesListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    incident_id: str | None = Field(
        default=None, description="The ID of the incident to get updates for"
    )
    page_size: int | None = Field(default=None, description="Number of results to return per page")
    after: str | None = Field(default=None, description="Cursor for pagination")


class ScheduleEntriesListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    schedule_id: str = Field(description="The ID of the schedule to get entries for")
    entry_window_start: str | None = Field(
        default=None, description="Start of the filter window in ISO 8601 format"
    )
    entry_window_end: str | None = Field(
        default=None, description="End of the filter window in ISO 8601 format"
    )


class ScheduleOverridesCreateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    rotation_id: str = Field(description="The ID of the rotation to override")
    layer_id: str = Field(description="The ID of the layer this override applies to")
    schedule_id: str = Field(description="The ID of the schedule")
    start_at: str = Field(description="When the override starts in ISO 8601 format")
    end_at: str = Field(description="When the override ends in ISO 8601 format")
    user_id: str | None = Field(
        default=None, description="The ID of the user to assign"
    )
    user_email: str | None = Field(
        default=None, description="The email of the user to assign"
    )
    user_slack_id: str | None = Field(
        default=None, description="The Slack ID of the user to assign"
    )


class EscalationPathsListInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    page_size: int | None = Field(default=None, description="Number of escalation paths per page")
    after: str | None = Field(default=None, description="Pagination cursor for the next page")


class EscalationPathsCreateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    name: str = Field(description="Name of the escalation path")
    path: list[Any] = Field(
        description=(
            "Array of escalation levels. Each level has targets "
            "(array of {id, type, schedule_id?, user_id?, urgency}) and time_to_ack_seconds"
        )
    )
    working_hours: list[Any] | None = Field(
        default=None,
        description="Optional working hours config: array of {weekday, start_time, end_time}",
    )


class EscalationPathsShowInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the escalation path")


class EscalationPathsUpdateInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the escalation path to update")
    name: str = Field(description="New name for the escalation path")
    path: list[Any] = Field(
        description="New escalation path: array of levels with targets and time_to_ack_seconds"
    )
    working_hours: list[Any] | None = Field(
        default=None,
        description="New working hours config: array of {weekday, start_time, end_time}",
    )


class EscalationPathsDeleteInput(BaseModel):
    api_key: str = Field(description="incident.io API key (provided by credential system)")
    id: str = Field(description="The ID of the escalation path to delete")


# --- @tool functions: Incidents --------------------------------------------


@tool(args_schema=IncidentsListInput)
@serialize_pydantic_return
async def incidents_list(
    api_key: str,
    page_size: int | None = None,
    after: str | None = None,
    sort_by: str | None = None,
    filter_mode: str | None = None,
) -> IncidentsListOutput:
    """List incidents from incident.io with their severity, status, and timestamps."""
    if not api_key or not api_key.strip():
        return IncidentsListOutput(success=False, error=_EMPTY_KEY_ERROR)
    params: dict[str, Any] = {}
    if page_size is not None:
        params["page_size"] = page_size
    if after:
        params["after"] = after.strip()
    if sort_by:
        params["sort_by"] = sort_by
    if filter_mode:
        params["filter_mode"] = filter_mode

    data, error = await _request("GET", "/v2/incidents", api_key, params=params)
    if error is not None or data is None:
        return IncidentsListOutput(success=False, error=error)
    return IncidentsListOutput(
        success=True,
        incidents=data.get("incidents") or [],
        pagination_meta=data.get("pagination_meta"),
    )


@tool(args_schema=IncidentsCreateInput)
@serialize_pydantic_return
async def incidents_create(
    api_key: str,
    idempotency_key: str,
    severity_id: str,
    visibility: str,
    name: str | None = None,
    summary: str | None = None,
    incident_type_id: str | None = None,
    incident_status_id: str | None = None,
) -> IncidentsCreateOutput:
    """Create a new incident. Requires idempotency_key, severity_id, and visibility."""
    if not api_key or not api_key.strip():
        return IncidentsCreateOutput(success=False, error=_EMPTY_KEY_ERROR)
    body: dict[str, Any] = {
        "idempotency_key": idempotency_key,
        "severity_id": severity_id,
        "visibility": visibility,
    }
    if name:
        body["name"] = name
    if summary:
        body["summary"] = summary
    if incident_type_id:
        body["incident_type_id"] = incident_type_id
    if incident_status_id:
        body["incident_status_id"] = incident_status_id

    data, error = await _request("POST", "/v2/incidents", api_key, json_body=body)
    if error is not None or data is None:
        return IncidentsCreateOutput(success=False, error=error)
    return IncidentsCreateOutput(success=True, incident=data.get("incident") or data)


@tool(args_schema=IncidentsShowInput)
@serialize_pydantic_return
async def incidents_show(api_key: str, id: str) -> IncidentsShowOutput:
    """Retrieve detailed information about a specific incident by its ID."""
    if not api_key or not api_key.strip():
        return IncidentsShowOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", f"/v2/incidents/{id.strip()}", api_key)
    if error is not None or data is None:
        return IncidentsShowOutput(success=False, error=error)
    return IncidentsShowOutput(success=True, incident=data.get("incident") or data)


@tool(args_schema=IncidentsUpdateInput)
@serialize_pydantic_return
async def incidents_update(
    api_key: str,
    id: str,
    notify_incident_channel: bool,
    name: str | None = None,
    summary: str | None = None,
    severity_id: str | None = None,
    incident_status_id: str | None = None,
    incident_type_id: str | None = None,
) -> IncidentsUpdateOutput:
    """Update an existing incident's name, summary, severity, status, or type."""
    if not api_key or not api_key.strip():
        return IncidentsUpdateOutput(success=False, error=_EMPTY_KEY_ERROR)
    incident: dict[str, Any] = {}
    if name:
        incident["name"] = name
    if summary:
        incident["summary"] = summary
    if severity_id:
        incident["severity_id"] = severity_id
    if incident_status_id:
        incident["incident_status_id"] = incident_status_id
    if incident_type_id:
        incident["incident_type_id"] = incident_type_id
    body: dict[str, Any] = {
        "incident": incident,
        "notify_incident_channel": notify_incident_channel,
    }

    data, error = await _request(
        "POST", f"/v2/incidents/{id.strip()}/actions/edit", api_key, json_body=body
    )
    if error is not None or data is None:
        return IncidentsUpdateOutput(success=False, error=error)
    return IncidentsUpdateOutput(success=True, incident=data.get("incident") or data)


# --- @tool functions: Actions ----------------------------------------------


@tool(args_schema=ActionsListInput)
@serialize_pydantic_return
async def actions_list(
    api_key: str,
    incident_id: str | None = None,
    incident_mode: str | None = None,
) -> ActionsListOutput:
    """List actions from incident.io. Optionally filter by incident ID or mode."""
    if not api_key or not api_key.strip():
        return ActionsListOutput(success=False, error=_EMPTY_KEY_ERROR)
    params: dict[str, Any] = {}
    if incident_id:
        params["incident_id"] = incident_id.strip()
    if incident_mode:
        params["incident_mode"] = incident_mode

    data, error = await _request("GET", "/v2/actions", api_key, params=params)
    if error is not None or data is None:
        return ActionsListOutput(success=False, error=error)
    return ActionsListOutput(success=True, actions=data.get("actions") or [])


@tool(args_schema=ActionsShowInput)
@serialize_pydantic_return
async def actions_show(api_key: str, id: str) -> ActionsShowOutput:
    """Get detailed information about a specific action from incident.io."""
    if not api_key or not api_key.strip():
        return ActionsShowOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", f"/v2/actions/{id.strip()}", api_key)
    if error is not None or data is None:
        return ActionsShowOutput(success=False, error=error)
    return ActionsShowOutput(success=True, action=data.get("action") or data)


# --- @tool functions: Follow-ups -------------------------------------------


@tool(args_schema=FollowUpsListInput)
@serialize_pydantic_return
async def follow_ups_list(
    api_key: str,
    incident_id: str | None = None,
    incident_mode: str | None = None,
) -> FollowUpsListOutput:
    """List follow-ups from incident.io. Optionally filter by incident ID or mode."""
    if not api_key or not api_key.strip():
        return FollowUpsListOutput(success=False, error=_EMPTY_KEY_ERROR)
    params: dict[str, Any] = {}
    if incident_id:
        params["incident_id"] = incident_id.strip()
    if incident_mode:
        params["incident_mode"] = incident_mode

    data, error = await _request("GET", "/v2/follow_ups", api_key, params=params)
    if error is not None or data is None:
        return FollowUpsListOutput(success=False, error=error)
    return FollowUpsListOutput(success=True, follow_ups=data.get("follow_ups") or [])


@tool(args_schema=FollowUpsShowInput)
@serialize_pydantic_return
async def follow_ups_show(api_key: str, id: str) -> FollowUpsShowOutput:
    """Get detailed information about a specific follow-up from incident.io."""
    if not api_key or not api_key.strip():
        return FollowUpsShowOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", f"/v2/follow_ups/{id.strip()}", api_key)
    if error is not None or data is None:
        return FollowUpsShowOutput(success=False, error=error)
    return FollowUpsShowOutput(success=True, follow_up=data.get("follow_up") or data)


# --- @tool functions: Users ------------------------------------------------


@tool(args_schema=UsersListInput)
@serialize_pydantic_return
async def users_list(
    api_key: str,
    page_size: int | None = None,
    after: str | None = None,
    email: str | None = None,
    slack_user_id: str | None = None,
) -> UsersListOutput:
    """List all users in the incident.io workspace with id, name, email, and role."""
    if not api_key or not api_key.strip():
        return UsersListOutput(success=False, error=_EMPTY_KEY_ERROR)
    params: dict[str, Any] = {}
    if page_size is not None:
        params["page_size"] = page_size
    if after:
        params["after"] = after.strip()
    if email:
        params["email"] = email.strip()
    if slack_user_id:
        params["slack_user_id"] = slack_user_id.strip()

    data, error = await _request("GET", "/v2/users", api_key, params=params)
    if error is not None or data is None:
        return UsersListOutput(success=False, error=error)
    return UsersListOutput(
        success=True,
        users=data.get("users") or [],
        pagination_meta=data.get("pagination_meta"),
    )


@tool(args_schema=UsersShowInput)
@serialize_pydantic_return
async def users_show(api_key: str, id: str) -> UsersShowOutput:
    """Get detailed information about a specific user by their ID."""
    if not api_key or not api_key.strip():
        return UsersShowOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", f"/v2/users/{id.strip()}", api_key)
    if error is not None or data is None:
        return UsersShowOutput(success=False, error=error)
    return UsersShowOutput(success=True, user=data.get("user") or data)


# --- @tool functions: Workflows --------------------------------------------


@tool(args_schema=WorkflowsListInput)
@serialize_pydantic_return
async def workflows_list(api_key: str) -> WorkflowsListOutput:
    """List all workflows in the incident.io workspace."""
    if not api_key or not api_key.strip():
        return WorkflowsListOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", "/v2/workflows", api_key)
    if error is not None or data is None:
        return WorkflowsListOutput(success=False, error=error)
    return WorkflowsListOutput(success=True, workflows=data.get("workflows") or [])


@tool(args_schema=WorkflowsCreateInput)
@serialize_pydantic_return
async def workflows_create(
    api_key: str,
    name: str,
    folder: str | None = None,
    state: str = "draft",
    trigger: str = "incident.updated",
    steps: list[Any] | None = None,
    condition_groups: list[Any] | None = None,
    runs_on_incidents: str = "newly_created",
    runs_on_incident_modes: list[Any] | None = None,
    include_private_incidents: bool = True,
    continue_on_step_error: bool = False,
    once_for: list[Any] | None = None,
    expressions: list[Any] | None = None,
    delay: dict[str, Any] | None = None,
) -> WorkflowsCreateOutput:
    """Create a new workflow in incident.io."""
    if not api_key or not api_key.strip():
        return WorkflowsCreateOutput(success=False, error=_EMPTY_KEY_ERROR)
    body: dict[str, Any] = {
        "name": name,
        "trigger": trigger or "incident.updated",
        "once_for": once_for if once_for is not None else [],
        "condition_groups": condition_groups if condition_groups is not None else [],
        "steps": steps if steps is not None else [],
        "expressions": expressions if expressions is not None else [],
        "include_private_incidents": include_private_incidents,
        "runs_on_incident_modes": (
            runs_on_incident_modes if runs_on_incident_modes is not None else ["standard"]
        ),
        "continue_on_step_error": continue_on_step_error,
        "runs_on_incidents": runs_on_incidents or "newly_created",
        "state": state or "draft",
    }
    if folder:
        body["folder"] = folder
    if delay is not None:
        body["delay"] = delay

    data, error = await _request("POST", "/v2/workflows", api_key, json_body=body)
    if error is not None or data is None:
        return WorkflowsCreateOutput(success=False, error=error)
    return WorkflowsCreateOutput(
        success=True,
        workflow=data.get("workflow") or data,
        management_meta=data.get("management_meta"),
    )


@tool(args_schema=WorkflowsShowInput)
@serialize_pydantic_return
async def workflows_show(
    api_key: str,
    id: str,
    skip_step_upgrades: bool | None = None,
) -> WorkflowsShowOutput:
    """Get details of a specific workflow in incident.io."""
    if not api_key or not api_key.strip():
        return WorkflowsShowOutput(success=False, error=_EMPTY_KEY_ERROR)
    params: dict[str, Any] = {}
    if skip_step_upgrades is not None:
        params["skip_step_upgrades"] = str(skip_step_upgrades).lower()

    data, error = await _request(
        "GET", f"/v2/workflows/{id.strip()}", api_key, params=params
    )
    if error is not None or data is None:
        return WorkflowsShowOutput(success=False, error=error)
    return WorkflowsShowOutput(
        success=True,
        workflow=data.get("workflow") or data,
        management_meta=data.get("management_meta"),
    )


@tool(args_schema=WorkflowsUpdateInput)
@serialize_pydantic_return
async def workflows_update(
    api_key: str,
    id: str,
    name: str,
    steps: list[Any],
    condition_groups: list[Any],
    runs_on_incidents: str,
    runs_on_incident_modes: list[Any],
    include_private_incidents: bool,
    continue_on_step_error: bool,
    once_for: list[Any],
    expressions: list[Any],
    state: str | None = None,
    folder: str | None = None,
    delay: dict[str, Any] | None = None,
) -> WorkflowsUpdateOutput:
    """Update an existing workflow in incident.io."""
    if not api_key or not api_key.strip():
        return WorkflowsUpdateOutput(success=False, error=_EMPTY_KEY_ERROR)
    body: dict[str, Any] = {
        "name": name,
        "once_for": once_for,
        "condition_groups": condition_groups,
        "steps": steps,
        "expressions": expressions,
        "include_private_incidents": include_private_incidents,
        "runs_on_incident_modes": runs_on_incident_modes,
        "continue_on_step_error": continue_on_step_error,
        "runs_on_incidents": runs_on_incidents,
    }
    if state:
        body["state"] = state
    if folder:
        body["folder"] = folder
    if delay is not None:
        body["delay"] = delay

    data, error = await _request("PUT", f"/v2/workflows/{id.strip()}", api_key, json_body=body)
    if error is not None or data is None:
        return WorkflowsUpdateOutput(success=False, error=error)
    return WorkflowsUpdateOutput(
        success=True,
        workflow=data.get("workflow") or data,
        management_meta=data.get("management_meta"),
    )


@tool(args_schema=WorkflowsDeleteInput)
@serialize_pydantic_return
async def workflows_delete(api_key: str, id: str) -> WorkflowsDeleteOutput:
    """Delete a workflow in incident.io."""
    if not api_key or not api_key.strip():
        return WorkflowsDeleteOutput(success=False, error=_EMPTY_KEY_ERROR)
    _data, error = await _request("DELETE", f"/v2/workflows/{id.strip()}", api_key)
    if error is not None:
        return WorkflowsDeleteOutput(success=False, error=error)
    return WorkflowsDeleteOutput(success=True, message="Workflow deleted successfully")


# --- @tool functions: Schedules --------------------------------------------


@tool(args_schema=SchedulesListInput)
@serialize_pydantic_return
async def schedules_list(
    api_key: str,
    page_size: int | None = None,
    after: str | None = None,
) -> SchedulesListOutput:
    """List all schedules in incident.io."""
    if not api_key or not api_key.strip():
        return SchedulesListOutput(success=False, error=_EMPTY_KEY_ERROR)
    params: dict[str, Any] = {}
    if page_size is not None:
        params["page_size"] = page_size
    if after:
        params["after"] = after

    data, error = await _request("GET", "/v2/schedules", api_key, params=params)
    if error is not None or data is None:
        return SchedulesListOutput(success=False, error=error)
    return SchedulesListOutput(
        success=True,
        schedules=data.get("schedules") or [],
        pagination_meta=data.get("pagination_meta"),
    )


@tool(args_schema=SchedulesCreateInput)
@serialize_pydantic_return
async def schedules_create(
    api_key: str,
    name: str,
    timezone: str,
    rotations_config: dict[str, Any],
) -> SchedulesCreateOutput:
    """Create a new schedule in incident.io."""
    if not api_key or not api_key.strip():
        return SchedulesCreateOutput(success=False, error=_EMPTY_KEY_ERROR)
    body: dict[str, Any] = {
        "schedule": {"name": name, "timezone": timezone, "config": rotations_config}
    }
    data, error = await _request("POST", "/v2/schedules", api_key, json_body=body)
    if error is not None or data is None:
        return SchedulesCreateOutput(success=False, error=error)
    return SchedulesCreateOutput(success=True, schedule=data.get("schedule") or data)


@tool(args_schema=SchedulesShowInput)
@serialize_pydantic_return
async def schedules_show(api_key: str, id: str) -> SchedulesShowOutput:
    """Get details of a specific schedule in incident.io."""
    if not api_key or not api_key.strip():
        return SchedulesShowOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", f"/v2/schedules/{id.strip()}", api_key)
    if error is not None or data is None:
        return SchedulesShowOutput(success=False, error=error)
    return SchedulesShowOutput(success=True, schedule=data.get("schedule") or data)


@tool(args_schema=SchedulesUpdateInput)
@serialize_pydantic_return
async def schedules_update(
    api_key: str,
    id: str,
    name: str | None = None,
    timezone: str | None = None,
    rotations_config: dict[str, Any] | None = None,
) -> SchedulesUpdateOutput:
    """Update an existing schedule in incident.io."""
    if not api_key or not api_key.strip():
        return SchedulesUpdateOutput(success=False, error=_EMPTY_KEY_ERROR)
    schedule: dict[str, Any] = {}
    if name:
        schedule["name"] = name
    if timezone:
        schedule["timezone"] = timezone
    if rotations_config is not None:
        schedule["config"] = rotations_config
    body: dict[str, Any] = {"schedule": schedule}

    data, error = await _request("PUT", f"/v2/schedules/{id.strip()}", api_key, json_body=body)
    if error is not None or data is None:
        return SchedulesUpdateOutput(success=False, error=error)
    return SchedulesUpdateOutput(success=True, schedule=data.get("schedule") or data)


@tool(args_schema=SchedulesDeleteInput)
@serialize_pydantic_return
async def schedules_delete(api_key: str, id: str) -> SchedulesDeleteOutput:
    """Delete a schedule in incident.io."""
    if not api_key or not api_key.strip():
        return SchedulesDeleteOutput(success=False, error=_EMPTY_KEY_ERROR)
    _data, error = await _request("DELETE", f"/v2/schedules/{id.strip()}", api_key)
    if error is not None:
        return SchedulesDeleteOutput(success=False, error=error)
    return SchedulesDeleteOutput(success=True, message="Schedule deleted successfully")


# --- @tool functions: Escalations ------------------------------------------


@tool(args_schema=EscalationsListInput)
@serialize_pydantic_return
async def escalations_list(
    api_key: str,
    page_size: int | None = None,
    after: str | None = None,
) -> EscalationsListOutput:
    """List all escalations in incident.io."""
    if not api_key or not api_key.strip():
        return EscalationsListOutput(success=False, error=_EMPTY_KEY_ERROR)
    params: dict[str, Any] = {}
    if page_size is not None:
        params["page_size"] = page_size
    if after:
        params["after"] = after

    data, error = await _request("GET", "/v2/escalations", api_key, params=params)
    if error is not None or data is None:
        return EscalationsListOutput(success=False, error=error)
    return EscalationsListOutput(
        success=True,
        escalations=data.get("escalations") or [],
        pagination_meta=data.get("pagination_meta"),
    )


@tool(args_schema=EscalationsCreateInput)
@serialize_pydantic_return
async def escalations_create(
    api_key: str,
    idempotency_key: str,
    title: str,
    escalation_path_id: str | None = None,
    user_ids: str | None = None,
) -> EscalationsCreateOutput:
    """Create a new escalation in incident.io."""
    if not api_key or not api_key.strip():
        return EscalationsCreateOutput(success=False, error=_EMPTY_KEY_ERROR)
    body: dict[str, Any] = {"idempotency_key": idempotency_key, "title": title}
    if escalation_path_id:
        body["escalation_path_id"] = escalation_path_id
    if user_ids:
        body["user_ids"] = [uid.strip() for uid in user_ids.split(",")]

    data, error = await _request("POST", "/v2/escalations", api_key, json_body=body)
    if error is not None or data is None:
        return EscalationsCreateOutput(success=False, error=error)
    return EscalationsCreateOutput(success=True, escalation=data.get("escalation") or data)


@tool(args_schema=EscalationsShowInput)
@serialize_pydantic_return
async def escalations_show(api_key: str, id: str) -> EscalationsShowOutput:
    """Get details of a specific escalation in incident.io."""
    if not api_key or not api_key.strip():
        return EscalationsShowOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", f"/v2/escalations/{id.strip()}", api_key)
    if error is not None or data is None:
        return EscalationsShowOutput(success=False, error=error)
    return EscalationsShowOutput(success=True, escalation=data.get("escalation") or data)


# --- @tool functions: Custom Fields ----------------------------------------


@tool(args_schema=CustomFieldsListInput)
@serialize_pydantic_return
async def custom_fields_list(api_key: str) -> CustomFieldsListOutput:
    """List all custom fields from incident.io."""
    if not api_key or not api_key.strip():
        return CustomFieldsListOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", "/v2/custom_fields", api_key)
    if error is not None or data is None:
        return CustomFieldsListOutput(success=False, error=error)
    return CustomFieldsListOutput(success=True, custom_fields=data.get("custom_fields") or [])


@tool(args_schema=CustomFieldsCreateInput)
@serialize_pydantic_return
async def custom_fields_create(
    api_key: str,
    name: str,
    description: str,
    field_type: str,
) -> CustomFieldsCreateOutput:
    """Create a new custom field in incident.io."""
    if not api_key or not api_key.strip():
        return CustomFieldsCreateOutput(success=False, error=_EMPTY_KEY_ERROR)
    body: dict[str, Any] = {
        "name": name,
        "field_type": field_type,
        "description": description,
    }
    data, error = await _request("POST", "/v2/custom_fields", api_key, json_body=body)
    if error is not None or data is None:
        return CustomFieldsCreateOutput(success=False, error=error)
    return CustomFieldsCreateOutput(success=True, custom_field=data.get("custom_field") or data)


@tool(args_schema=CustomFieldsShowInput)
@serialize_pydantic_return
async def custom_fields_show(api_key: str, id: str) -> CustomFieldsShowOutput:
    """Get detailed information about a specific custom field from incident.io."""
    if not api_key or not api_key.strip():
        return CustomFieldsShowOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", f"/v2/custom_fields/{id.strip()}", api_key)
    if error is not None or data is None:
        return CustomFieldsShowOutput(success=False, error=error)
    return CustomFieldsShowOutput(success=True, custom_field=data.get("custom_field") or data)


@tool(args_schema=CustomFieldsUpdateInput)
@serialize_pydantic_return
async def custom_fields_update(
    api_key: str,
    id: str,
    name: str,
    description: str,
) -> CustomFieldsUpdateOutput:
    """Update an existing custom field in incident.io."""
    if not api_key or not api_key.strip():
        return CustomFieldsUpdateOutput(success=False, error=_EMPTY_KEY_ERROR)
    body: dict[str, Any] = {"name": name, "description": description}
    data, error = await _request(
        "PUT", f"/v2/custom_fields/{id.strip()}", api_key, json_body=body
    )
    if error is not None or data is None:
        return CustomFieldsUpdateOutput(success=False, error=error)
    return CustomFieldsUpdateOutput(success=True, custom_field=data.get("custom_field") or data)


@tool(args_schema=CustomFieldsDeleteInput)
@serialize_pydantic_return
async def custom_fields_delete(api_key: str, id: str) -> CustomFieldsDeleteOutput:
    """Delete a custom field from incident.io."""
    if not api_key or not api_key.strip():
        return CustomFieldsDeleteOutput(success=False, error=_EMPTY_KEY_ERROR)
    _data, error = await _request("DELETE", f"/v2/custom_fields/{id.strip()}", api_key)
    if error is not None:
        return CustomFieldsDeleteOutput(success=False, error=error)
    return CustomFieldsDeleteOutput(success=True, message="Custom field successfully deleted")


# --- @tool functions: Reference data ---------------------------------------


@tool(args_schema=SeveritiesListInput)
@serialize_pydantic_return
async def severities_list(api_key: str) -> SeveritiesListOutput:
    """List all severity levels configured in the incident.io workspace."""
    if not api_key or not api_key.strip():
        return SeveritiesListOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", "/v1/severities", api_key)
    if error is not None or data is None:
        return SeveritiesListOutput(success=False, error=error)
    return SeveritiesListOutput(success=True, severities=data.get("severities") or [])


@tool(args_schema=IncidentStatusesListInput)
@serialize_pydantic_return
async def incident_statuses_list(api_key: str) -> IncidentStatusesListOutput:
    """List all incident statuses configured in the incident.io workspace."""
    if not api_key or not api_key.strip():
        return IncidentStatusesListOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", "/v1/incident_statuses", api_key)
    if error is not None or data is None:
        return IncidentStatusesListOutput(success=False, error=error)
    return IncidentStatusesListOutput(
        success=True, incident_statuses=data.get("incident_statuses") or []
    )


@tool(args_schema=IncidentTypesListInput)
@serialize_pydantic_return
async def incident_types_list(api_key: str) -> IncidentTypesListOutput:
    """List all incident types configured in the incident.io workspace."""
    if not api_key or not api_key.strip():
        return IncidentTypesListOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", "/v1/incident_types", api_key)
    if error is not None or data is None:
        return IncidentTypesListOutput(success=False, error=error)
    return IncidentTypesListOutput(success=True, incident_types=data.get("incident_types") or [])


# --- @tool functions: Incident Roles ---------------------------------------


@tool(args_schema=IncidentRolesListInput)
@serialize_pydantic_return
async def incident_roles_list(api_key: str) -> IncidentRolesListOutput:
    """List all incident roles in incident.io."""
    if not api_key or not api_key.strip():
        return IncidentRolesListOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", "/v2/incident_roles", api_key)
    if error is not None or data is None:
        return IncidentRolesListOutput(success=False, error=error)
    return IncidentRolesListOutput(success=True, incident_roles=data.get("incident_roles") or [])


@tool(args_schema=IncidentRolesCreateInput)
@serialize_pydantic_return
async def incident_roles_create(
    api_key: str,
    name: str,
    description: str,
    instructions: str,
    shortform: str,
) -> IncidentRolesCreateOutput:
    """Create a new incident role in incident.io."""
    if not api_key or not api_key.strip():
        return IncidentRolesCreateOutput(success=False, error=_EMPTY_KEY_ERROR)
    body: dict[str, Any] = {
        "name": name,
        "description": description,
        "instructions": instructions,
        "shortform": shortform,
    }
    data, error = await _request("POST", "/v2/incident_roles", api_key, json_body=body)
    if error is not None or data is None:
        return IncidentRolesCreateOutput(success=False, error=error)
    return IncidentRolesCreateOutput(success=True, incident_role=data.get("incident_role") or data)


@tool(args_schema=IncidentRolesShowInput)
@serialize_pydantic_return
async def incident_roles_show(api_key: str, id: str) -> IncidentRolesShowOutput:
    """Get details of a specific incident role in incident.io."""
    if not api_key or not api_key.strip():
        return IncidentRolesShowOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", f"/v2/incident_roles/{id.strip()}", api_key)
    if error is not None or data is None:
        return IncidentRolesShowOutput(success=False, error=error)
    return IncidentRolesShowOutput(success=True, incident_role=data.get("incident_role") or data)


@tool(args_schema=IncidentRolesUpdateInput)
@serialize_pydantic_return
async def incident_roles_update(
    api_key: str,
    id: str,
    name: str,
    description: str,
    instructions: str,
    shortform: str,
) -> IncidentRolesUpdateOutput:
    """Update an existing incident role in incident.io."""
    if not api_key or not api_key.strip():
        return IncidentRolesUpdateOutput(success=False, error=_EMPTY_KEY_ERROR)
    body: dict[str, Any] = {
        "name": name,
        "description": description,
        "instructions": instructions,
        "shortform": shortform,
    }
    data, error = await _request(
        "PUT", f"/v2/incident_roles/{id.strip()}", api_key, json_body=body
    )
    if error is not None or data is None:
        return IncidentRolesUpdateOutput(success=False, error=error)
    return IncidentRolesUpdateOutput(success=True, incident_role=data.get("incident_role") or data)


@tool(args_schema=IncidentRolesDeleteInput)
@serialize_pydantic_return
async def incident_roles_delete(api_key: str, id: str) -> IncidentRolesDeleteOutput:
    """Delete an incident role in incident.io."""
    if not api_key or not api_key.strip():
        return IncidentRolesDeleteOutput(success=False, error=_EMPTY_KEY_ERROR)
    _data, error = await _request("DELETE", f"/v2/incident_roles/{id.strip()}", api_key)
    if error is not None:
        return IncidentRolesDeleteOutput(success=False, error=error)
    return IncidentRolesDeleteOutput(success=True, message="Incident role deleted successfully")


# --- @tool functions: Incident Timestamps ----------------------------------


@tool(args_schema=IncidentTimestampsListInput)
@serialize_pydantic_return
async def incident_timestamps_list(api_key: str) -> IncidentTimestampsListOutput:
    """List all incident timestamp definitions in incident.io."""
    if not api_key or not api_key.strip():
        return IncidentTimestampsListOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", "/v2/incident_timestamps", api_key)
    if error is not None or data is None:
        return IncidentTimestampsListOutput(success=False, error=error)
    return IncidentTimestampsListOutput(
        success=True, incident_timestamps=data.get("incident_timestamps") or []
    )


@tool(args_schema=IncidentTimestampsShowInput)
@serialize_pydantic_return
async def incident_timestamps_show(api_key: str, id: str) -> IncidentTimestampsShowOutput:
    """Get details of a specific incident timestamp definition in incident.io."""
    if not api_key or not api_key.strip():
        return IncidentTimestampsShowOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", f"/v2/incident_timestamps/{id.strip()}", api_key)
    if error is not None or data is None:
        return IncidentTimestampsShowOutput(success=False, error=error)
    return IncidentTimestampsShowOutput(
        success=True, incident_timestamp=data.get("incident_timestamp") or data
    )


# --- @tool functions: Incident Updates -------------------------------------


@tool(args_schema=IncidentUpdatesListInput)
@serialize_pydantic_return
async def incident_updates_list(
    api_key: str,
    incident_id: str | None = None,
    page_size: int | None = None,
    after: str | None = None,
) -> IncidentUpdatesListOutput:
    """List incident updates in incident.io. Optionally filter by incident ID."""
    if not api_key or not api_key.strip():
        return IncidentUpdatesListOutput(success=False, error=_EMPTY_KEY_ERROR)
    params: dict[str, Any] = {}
    if incident_id:
        params["incident_id"] = incident_id.strip()
    if page_size is not None:
        params["page_size"] = page_size
    if after:
        params["after"] = after.strip()

    data, error = await _request("GET", "/v2/incident_updates", api_key, params=params)
    if error is not None or data is None:
        return IncidentUpdatesListOutput(success=False, error=error)
    return IncidentUpdatesListOutput(
        success=True,
        incident_updates=data.get("incident_updates") or [],
        pagination_meta=data.get("pagination_meta"),
    )


# --- @tool functions: Schedule Entries -------------------------------------


@tool(args_schema=ScheduleEntriesListInput)
@serialize_pydantic_return
async def schedule_entries_list(
    api_key: str,
    schedule_id: str,
    entry_window_start: str | None = None,
    entry_window_end: str | None = None,
) -> ScheduleEntriesListOutput:
    """List all entries for a specific schedule in incident.io."""
    if not api_key or not api_key.strip():
        return ScheduleEntriesListOutput(success=False, error=_EMPTY_KEY_ERROR)
    params: dict[str, Any] = {"schedule_id": schedule_id.strip()}
    if entry_window_start:
        params["entry_window_start"] = entry_window_start
    if entry_window_end:
        params["entry_window_end"] = entry_window_end

    data, error = await _request("GET", "/v2/schedule_entries", api_key, params=params)
    if error is not None or data is None:
        return ScheduleEntriesListOutput(success=False, error=error)
    raw_entries = data.get("schedule_entries") or {}
    schedule_entries = {
        "final": raw_entries.get("final") or [],
        "overrides": raw_entries.get("overrides") or [],
        "scheduled": raw_entries.get("scheduled") or [],
    }
    return ScheduleEntriesListOutput(
        success=True,
        schedule_entries=schedule_entries,
        pagination_meta=data.get("pagination_meta"),
    )


# --- @tool functions: Schedule Overrides -----------------------------------


@tool(args_schema=ScheduleOverridesCreateInput)
@serialize_pydantic_return
async def schedule_overrides_create(
    api_key: str,
    rotation_id: str,
    layer_id: str,
    schedule_id: str,
    start_at: str,
    end_at: str,
    user_id: str | None = None,
    user_email: str | None = None,
    user_slack_id: str | None = None,
) -> ScheduleOverridesCreateOutput:
    """Create a new schedule override in incident.io."""
    if not api_key or not api_key.strip():
        return ScheduleOverridesCreateOutput(success=False, error=_EMPTY_KEY_ERROR)
    user: dict[str, Any] = {}
    if user_id:
        user["id"] = user_id
    if user_email:
        user["email"] = user_email
    if user_slack_id:
        user["slack_user_id"] = user_slack_id
    body: dict[str, Any] = {
        "layer_id": layer_id.strip(),
        "rotation_id": rotation_id,
        "schedule_id": schedule_id,
        "user": user,
        "start_at": start_at,
        "end_at": end_at,
    }

    data, error = await _request("POST", "/v2/schedule_overrides", api_key, json_body=body)
    if error is not None or data is None:
        return ScheduleOverridesCreateOutput(success=False, error=error)
    return ScheduleOverridesCreateOutput(success=True, override=data.get("override") or data)


# --- @tool functions: Escalation Paths -------------------------------------


@tool(args_schema=EscalationPathsListInput)
@serialize_pydantic_return
async def escalation_paths_list(
    api_key: str,
    page_size: int | None = None,
    after: str | None = None,
) -> EscalationPathsListOutput:
    """List escalation paths in incident.io."""
    if not api_key or not api_key.strip():
        return EscalationPathsListOutput(success=False, error=_EMPTY_KEY_ERROR)
    params: dict[str, Any] = {}
    if page_size is not None:
        params["page_size"] = page_size
    if after:
        params["after"] = after

    data, error = await _request("GET", "/v2/escalation_paths", api_key, params=params)
    if error is not None or data is None:
        return EscalationPathsListOutput(success=False, error=error)
    return EscalationPathsListOutput(
        success=True,
        escalation_paths=data.get("escalation_paths") or [],
        pagination_meta=data.get("pagination_meta"),
    )


@tool(args_schema=EscalationPathsCreateInput)
@serialize_pydantic_return
async def escalation_paths_create(
    api_key: str,
    name: str,
    path: list[Any],
    working_hours: list[Any] | None = None,
) -> EscalationPathsCreateOutput:
    """Create a new escalation path in incident.io."""
    if not api_key or not api_key.strip():
        return EscalationPathsCreateOutput(success=False, error=_EMPTY_KEY_ERROR)
    body: dict[str, Any] = {"name": name, "path": path}
    if working_hours is not None:
        body["working_hours"] = working_hours

    data, error = await _request("POST", "/v2/escalation_paths", api_key, json_body=body)
    if error is not None or data is None:
        return EscalationPathsCreateOutput(success=False, error=error)
    return EscalationPathsCreateOutput(
        success=True, escalation_path=data.get("escalation_path") or data
    )


@tool(args_schema=EscalationPathsShowInput)
@serialize_pydantic_return
async def escalation_paths_show(api_key: str, id: str) -> EscalationPathsShowOutput:
    """Get details of a specific escalation path in incident.io."""
    if not api_key or not api_key.strip():
        return EscalationPathsShowOutput(success=False, error=_EMPTY_KEY_ERROR)
    data, error = await _request("GET", f"/v2/escalation_paths/{id.strip()}", api_key)
    if error is not None or data is None:
        return EscalationPathsShowOutput(success=False, error=error)
    return EscalationPathsShowOutput(
        success=True, escalation_path=data.get("escalation_path") or data
    )


@tool(args_schema=EscalationPathsUpdateInput)
@serialize_pydantic_return
async def escalation_paths_update(
    api_key: str,
    id: str,
    name: str,
    path: list[Any],
    working_hours: list[Any] | None = None,
) -> EscalationPathsUpdateOutput:
    """Update an existing escalation path in incident.io."""
    if not api_key or not api_key.strip():
        return EscalationPathsUpdateOutput(success=False, error=_EMPTY_KEY_ERROR)
    body: dict[str, Any] = {"name": name, "path": path}
    if working_hours is not None:
        body["working_hours"] = working_hours

    data, error = await _request(
        "PUT", f"/v2/escalation_paths/{id.strip()}", api_key, json_body=body
    )
    if error is not None or data is None:
        return EscalationPathsUpdateOutput(success=False, error=error)
    return EscalationPathsUpdateOutput(
        success=True, escalation_path=data.get("escalation_path") or data
    )


@tool(args_schema=EscalationPathsDeleteInput)
@serialize_pydantic_return
async def escalation_paths_delete(api_key: str, id: str) -> EscalationPathsDeleteOutput:
    """Delete an escalation path in incident.io."""
    if not api_key or not api_key.strip():
        return EscalationPathsDeleteOutput(success=False, error=_EMPTY_KEY_ERROR)
    _data, error = await _request("DELETE", f"/v2/escalation_paths/{id.strip()}", api_key)
    if error is not None:
        return EscalationPathsDeleteOutput(success=False, error=error)
    return EscalationPathsDeleteOutput(success=True, message="Escalation path deleted successfully")
