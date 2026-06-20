"""Pydantic response models for the incident.io integration's @tool functions.

incident.io follows the modulex *api_key* runtime convention: each tool
function takes ``api_key: str`` directly and the modulex ``ToolExecutor``
injects it from the resolved credential.

Error model: every call is wrapped in try/except so non-2xx responses,
timeouts, and unexpected exceptions surface as ``success=False`` + ``error``
rather than raising. Every output model carries both shapes.

The incident.io REST API returns richly nested JSON. To stay faithful to
the upstream payloads (and avoid over-tightening shapes that the API may
extend), list/object resources are surfaced as permissive
``dict``/``list`` fields rather than fully-typed sub-models.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ActionsListOutput",
    "ActionsShowOutput",
    "CustomFieldsCreateOutput",
    "CustomFieldsDeleteOutput",
    "CustomFieldsListOutput",
    "CustomFieldsShowOutput",
    "CustomFieldsUpdateOutput",
    "EscalationPathsCreateOutput",
    "EscalationPathsDeleteOutput",
    "EscalationPathsListOutput",
    "EscalationPathsShowOutput",
    "EscalationPathsUpdateOutput",
    "EscalationsCreateOutput",
    "EscalationsListOutput",
    "EscalationsShowOutput",
    "FollowUpsListOutput",
    "FollowUpsShowOutput",
    "IncidentRolesCreateOutput",
    "IncidentRolesDeleteOutput",
    "IncidentRolesListOutput",
    "IncidentRolesShowOutput",
    "IncidentRolesUpdateOutput",
    "IncidentStatusesListOutput",
    "IncidentTimestampsListOutput",
    "IncidentTimestampsShowOutput",
    "IncidentTypesListOutput",
    "IncidentUpdatesListOutput",
    "IncidentsCreateOutput",
    "IncidentsListOutput",
    "IncidentsShowOutput",
    "IncidentsUpdateOutput",
    "ScheduleEntriesListOutput",
    "ScheduleOverridesCreateOutput",
    "SchedulesCreateOutput",
    "SchedulesDeleteOutput",
    "SchedulesListOutput",
    "SchedulesShowOutput",
    "SchedulesUpdateOutput",
    "SeveritiesListOutput",
    "UsersListOutput",
    "UsersShowOutput",
    "WorkflowsCreateOutput",
    "WorkflowsDeleteOutput",
    "WorkflowsListOutput",
    "WorkflowsShowOutput",
    "WorkflowsUpdateOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Incidents -------------------------------------------------------------


class IncidentsListOutput(_Base):
    success: bool
    error: str | None = None
    incidents: list[dict[str, Any]] = Field(default_factory=list)
    pagination_meta: dict[str, Any] | None = None


class IncidentsCreateOutput(_Base):
    success: bool
    error: str | None = None
    incident: dict[str, Any] | None = None


class IncidentsShowOutput(_Base):
    success: bool
    error: str | None = None
    incident: dict[str, Any] | None = None


class IncidentsUpdateOutput(_Base):
    success: bool
    error: str | None = None
    incident: dict[str, Any] | None = None


# --- Actions ---------------------------------------------------------------


class ActionsListOutput(_Base):
    success: bool
    error: str | None = None
    actions: list[dict[str, Any]] = Field(default_factory=list)


class ActionsShowOutput(_Base):
    success: bool
    error: str | None = None
    action: dict[str, Any] | None = None


# --- Follow-ups ------------------------------------------------------------


class FollowUpsListOutput(_Base):
    success: bool
    error: str | None = None
    follow_ups: list[dict[str, Any]] = Field(default_factory=list)


class FollowUpsShowOutput(_Base):
    success: bool
    error: str | None = None
    follow_up: dict[str, Any] | None = None


# --- Users -----------------------------------------------------------------


class UsersListOutput(_Base):
    success: bool
    error: str | None = None
    users: list[dict[str, Any]] = Field(default_factory=list)
    pagination_meta: dict[str, Any] | None = None


class UsersShowOutput(_Base):
    success: bool
    error: str | None = None
    user: dict[str, Any] | None = None


# --- Workflows -------------------------------------------------------------


class WorkflowsListOutput(_Base):
    success: bool
    error: str | None = None
    workflows: list[dict[str, Any]] = Field(default_factory=list)


class WorkflowsCreateOutput(_Base):
    success: bool
    error: str | None = None
    workflow: dict[str, Any] | None = None
    management_meta: dict[str, Any] | None = None


class WorkflowsShowOutput(_Base):
    success: bool
    error: str | None = None
    workflow: dict[str, Any] | None = None
    management_meta: dict[str, Any] | None = None


class WorkflowsUpdateOutput(_Base):
    success: bool
    error: str | None = None
    workflow: dict[str, Any] | None = None
    management_meta: dict[str, Any] | None = None


class WorkflowsDeleteOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None


# --- Schedules -------------------------------------------------------------


class SchedulesListOutput(_Base):
    success: bool
    error: str | None = None
    schedules: list[dict[str, Any]] = Field(default_factory=list)
    pagination_meta: dict[str, Any] | None = None


class SchedulesCreateOutput(_Base):
    success: bool
    error: str | None = None
    schedule: dict[str, Any] | None = None


class SchedulesShowOutput(_Base):
    success: bool
    error: str | None = None
    schedule: dict[str, Any] | None = None


class SchedulesUpdateOutput(_Base):
    success: bool
    error: str | None = None
    schedule: dict[str, Any] | None = None


class SchedulesDeleteOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None


# --- Escalations -----------------------------------------------------------


class EscalationsListOutput(_Base):
    success: bool
    error: str | None = None
    escalations: list[dict[str, Any]] = Field(default_factory=list)
    pagination_meta: dict[str, Any] | None = None


class EscalationsCreateOutput(_Base):
    success: bool
    error: str | None = None
    escalation: dict[str, Any] | None = None


class EscalationsShowOutput(_Base):
    success: bool
    error: str | None = None
    escalation: dict[str, Any] | None = None


# --- Custom Fields ---------------------------------------------------------


class CustomFieldsListOutput(_Base):
    success: bool
    error: str | None = None
    custom_fields: list[dict[str, Any]] = Field(default_factory=list)


class CustomFieldsCreateOutput(_Base):
    success: bool
    error: str | None = None
    custom_field: dict[str, Any] | None = None


class CustomFieldsShowOutput(_Base):
    success: bool
    error: str | None = None
    custom_field: dict[str, Any] | None = None


class CustomFieldsUpdateOutput(_Base):
    success: bool
    error: str | None = None
    custom_field: dict[str, Any] | None = None


class CustomFieldsDeleteOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None


# --- Reference data --------------------------------------------------------


class SeveritiesListOutput(_Base):
    success: bool
    error: str | None = None
    severities: list[dict[str, Any]] = Field(default_factory=list)


class IncidentStatusesListOutput(_Base):
    success: bool
    error: str | None = None
    incident_statuses: list[dict[str, Any]] = Field(default_factory=list)


class IncidentTypesListOutput(_Base):
    success: bool
    error: str | None = None
    incident_types: list[dict[str, Any]] = Field(default_factory=list)


# --- Incident Roles --------------------------------------------------------


class IncidentRolesListOutput(_Base):
    success: bool
    error: str | None = None
    incident_roles: list[dict[str, Any]] = Field(default_factory=list)


class IncidentRolesCreateOutput(_Base):
    success: bool
    error: str | None = None
    incident_role: dict[str, Any] | None = None


class IncidentRolesShowOutput(_Base):
    success: bool
    error: str | None = None
    incident_role: dict[str, Any] | None = None


class IncidentRolesUpdateOutput(_Base):
    success: bool
    error: str | None = None
    incident_role: dict[str, Any] | None = None


class IncidentRolesDeleteOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None


# --- Incident Timestamps ---------------------------------------------------


class IncidentTimestampsListOutput(_Base):
    success: bool
    error: str | None = None
    incident_timestamps: list[dict[str, Any]] = Field(default_factory=list)


class IncidentTimestampsShowOutput(_Base):
    success: bool
    error: str | None = None
    incident_timestamp: dict[str, Any] | None = None


# --- Incident Updates ------------------------------------------------------


class IncidentUpdatesListOutput(_Base):
    success: bool
    error: str | None = None
    incident_updates: list[dict[str, Any]] = Field(default_factory=list)
    pagination_meta: dict[str, Any] | None = None


# --- Schedule Entries ------------------------------------------------------


class ScheduleEntriesListOutput(_Base):
    success: bool
    error: str | None = None
    schedule_entries: dict[str, Any] | None = None
    pagination_meta: dict[str, Any] | None = None


# --- Schedule Overrides ----------------------------------------------------


class ScheduleOverridesCreateOutput(_Base):
    success: bool
    error: str | None = None
    override: dict[str, Any] | None = None


# --- Escalation Paths ------------------------------------------------------


class EscalationPathsListOutput(_Base):
    success: bool
    error: str | None = None
    escalation_paths: list[dict[str, Any]] = Field(default_factory=list)
    pagination_meta: dict[str, Any] | None = None


class EscalationPathsCreateOutput(_Base):
    success: bool
    error: str | None = None
    escalation_path: dict[str, Any] | None = None


class EscalationPathsShowOutput(_Base):
    success: bool
    error: str | None = None
    escalation_path: dict[str, Any] | None = None


class EscalationPathsUpdateOutput(_Base):
    success: bool
    error: str | None = None
    escalation_path: dict[str, Any] | None = None


class EscalationPathsDeleteOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
