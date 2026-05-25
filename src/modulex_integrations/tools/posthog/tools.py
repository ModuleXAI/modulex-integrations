"""PostHog LangChain ``@tool`` functions — 78 actions.

Two API surfaces are exposed:

- **Project REST** (`{base_url}/api/projects/{project_id}/…`) — 70+
  actions for dashboards, experiments, feature flags, insights,
  surveys, cohorts, persons, groups, session recordings, actions,
  annotations, alerts, early-access features, definitions, etc.
  Uses Bearer token auth (personal API key).
- **Ingest** (`{ingest_url}/i/v0/e/`, `/batch/`, `/flags`) — 6
  capture/identify/alias/evaluate actions. **No Bearer header**;
  `project_api_key` is in the JSON body.

Two `_call_*` helpers do the actual HTTP. All 78 actions are thin
wrappers that build a URL + payload then go through one of them.
Output is uniform via the generic ``PostHogResult`` envelope — every
``result`` field carries the upstream JSON shape verbatim (matches
legacy "return raw API data" intent).

Two legacy quirks preserved:

- **`delete_action`** falls back to a rename if PostHog's
  soft-delete PATCH fails (documented upstream bug).
- **`delete_action_by_name` / `delete_early_access_feature_by_name`**
  are 2-call workflows: list with `?search=` → find exact match →
  delete via DELETE / PATCH / rename chain.
"""
from __future__ import annotations

import time
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.posthog.outputs import PostHogResult

__all__ = [
    "alias_user",
    "batch_capture_events",
    "bulk_delete_persons",
    "capture_event",
    "create_action",
    "create_alert",
    "create_annotation",
    "create_cohort",
    "create_dashboard",
    "create_early_access_feature",
    "create_experiment",
    "create_feature_flag",
    "create_insight",
    "create_survey",
    "delete_action",
    "delete_action_by_name",
    "delete_alert",
    "delete_annotation",
    "delete_cohort",
    "delete_dashboard",
    "delete_early_access_feature",
    "delete_early_access_feature_by_name",
    "delete_experiment",
    "delete_feature_flag",
    "delete_insight",
    "delete_person",
    "delete_session_recording",
    "delete_survey",
    "evaluate_feature_flags",
    "find_group",
    "get_action",
    "get_actions",
    "get_alert",
    "get_alerts",
    "get_annotation",
    "get_annotations",
    "get_cohort",
    "get_cohort_persons",
    "get_cohorts",
    "get_dashboard",
    "get_dashboards",
    "get_early_access_feature",
    "get_early_access_features",
    "get_error_tracking_issue",
    "get_event_definitions",
    "get_experiment",
    "get_experiment_results",
    "get_experiments",
    "get_feature_flag",
    "get_feature_flags",
    "get_group_types",
    "get_groups",
    "get_insight",
    "get_insights",
    "get_organizations",
    "get_person",
    "get_persons",
    "get_projects",
    "get_property_definitions",
    "get_session_recording",
    "get_session_recordings",
    "get_survey",
    "get_surveys",
    "group_identify",
    "identify_user",
    "list_error_tracking_issues",
    "run_query",
    "update_action",
    "update_alert",
    "update_annotation",
    "update_cohort",
    "update_dashboard",
    "update_early_access_feature",
    "update_experiment",
    "update_feature_flag",
    "update_insight",
    "update_person",
    "update_survey",
]

_DEFAULT_BASE = "https://app.posthog.com"
_DEFAULT_INGEST = "https://us.i.posthog.com"
_TIMEOUT = 60.0


def _base(base_url: str | None) -> str:
    """Normalize a user-supplied PostHog instance URL to a host root.

    Accepts (and corrects) common mistakes:
      * ``https://us.posthog.com``           → ``https://us.posthog.com``
      * ``https://us.posthog.com/``          → ``https://us.posthog.com``
      * ``https://us.posthog.com/api``       → ``https://us.posthog.com``
      * ``https://us.posthog.com/api/``      → ``https://us.posthog.com``
      * ``https://us.posthog.com/api/projects/`` → ``https://us.posthog.com``
    """
    url = (base_url or _DEFAULT_BASE).rstrip("/")
    # Strip any trailing /api or /api/projects (with or without trailing slash)
    for suffix in ("/api/projects", "/api"):
        if url.lower().endswith(suffix):
            url = url[: -len(suffix)]
    return url.rstrip("/")


def _ingest(ingest_url: str | None) -> str:
    return (ingest_url or _DEFAULT_INGEST).rstrip("/")


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _validate_key(api_key: str, action: str) -> str | None:
    if not api_key or not api_key.strip():
        return f"PostHog API key is empty for {action}"
    return None


def _api_err(status: int, body: str) -> str:
    return f"API error: {status} - {body}"


async def _call_project(
    method: str,
    api_key: str,
    base_url: str | None,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    success_codes: tuple[int, ...] = (200,),
) -> tuple[bool, str | None, Any]:
    """Make a project-scoped REST call with Bearer auth."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                method,
                f"{_base(base_url)}{path}",
                headers=_headers(api_key),
                json=json_body,
                params=params,
            )
        if response.status_code not in success_codes:
            return False, _api_err(response.status_code, response.text), None
        if response.status_code == 204 or not response.content:
            return True, None, None
        return True, None, response.json()
    except Exception as exc:
        return False, str(exc), None


async def _call_ingest(
    method: str,
    ingest_url: str | None,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[bool, str | None, Any]:
    """Ingest-API call (no Bearer; project_api_key lives in the body)."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                method,
                f"{_ingest(ingest_url)}{path}",
                headers={"Content-Type": "application/json"},
                json=json_body,
                params=params,
            )
        if response.status_code != 200:
            return False, _api_err(response.status_code, response.text), None
        return True, None, response.json() if response.content else None
    except Exception as exc:
        return False, str(exc), None


# --- Generic input shapes -------------------------------------------------


class _ProjectBase(BaseModel):
    api_key: str = Field(description="PostHog personal API key")
    project_id: int = Field(description="PostHog project ID")
    base_url: str | None = Field(default=None)


class _IngestBase(BaseModel):
    project_api_key: str = Field(description="PostHog project API key")
    ingest_url: str | None = Field(default=None)


# --- Input schemas (one per action) ---------------------------------------

# Dashboards
class DashboardGetAllInput(_ProjectBase):
    limit: int = 100
    offset: int = 0
    search: str | None = None
    pinned: bool | None = None


class DashboardGetInput(_ProjectBase):
    dashboard_id: int


class DashboardCreateInput(_ProjectBase):
    name: str
    description: str | None = None
    pinned: bool | None = None
    tags: list[str] | None = None


class DashboardUpdateInput(_ProjectBase):
    dashboard_id: int
    name: str | None = None
    description: str | None = None
    pinned: bool | None = None
    tags: list[str] | None = None


class DashboardDeleteInput(_ProjectBase):
    dashboard_id: int


# Experiments
class ExperimentListInput(_ProjectBase):
    pass


class ExperimentGetInput(_ProjectBase):
    experiment_id: int


class ExperimentCreateInput(_ProjectBase):
    name: str
    feature_flag_key: str
    description: str | None = None
    experiment_type: str = "product"
    primary_metrics: list[dict[str, Any]] | None = None
    secondary_metrics: list[dict[str, Any]] | None = None
    variants: list[dict[str, Any]] | None = None
    minimum_detectable_effect: float = 30
    filter_test_accounts: bool = True


class ExperimentUpdateInput(_ProjectBase):
    experiment_id: int
    name: str | None = None
    description: str | None = None
    primary_metrics: list[dict[str, Any]] | None = None
    secondary_metrics: list[dict[str, Any]] | None = None
    launch: bool | None = None
    conclude: str | None = None
    archive: bool | None = None


class ExperimentDeleteInput(_ProjectBase):
    experiment_id: int


class ExperimentResultsInput(_ProjectBase):
    experiment_id: int
    refresh: bool = False


# Feature flags
class FeatureFlagListInput(_ProjectBase):
    pass


class FeatureFlagGetInput(_ProjectBase):
    flag_id: int | None = None
    flag_key: str | None = None


class FeatureFlagCreateInput(_ProjectBase):
    key: str
    name: str
    description: str | None = None
    filters: dict[str, Any] | None = None
    active: bool = True
    tags: list[str] | None = None


class FeatureFlagUpdateInput(_ProjectBase):
    flag_key: str
    name: str | None = None
    description: str | None = None
    filters: dict[str, Any] | None = None
    active: bool | None = None
    tags: list[str] | None = None


class FeatureFlagDeleteInput(_ProjectBase):
    flag_id: int


# Insights
class InsightGetAllInput(_ProjectBase):
    limit: int = 100
    offset: int = 0
    search: str | None = None


class InsightGetInput(_ProjectBase):
    insight_id: int


class InsightCreateInput(_ProjectBase):
    name: str
    description: str | None = None
    filters: dict[str, Any] | None = None
    query: dict[str, Any] | None = None
    dashboards: list[int] | None = None
    tags: list[str] | None = None


class InsightUpdateInput(_ProjectBase):
    insight_id: int
    name: str | None = None
    description: str | None = None
    filters: dict[str, Any] | None = None
    query: dict[str, Any] | None = None
    tags: list[str] | None = None


class InsightDeleteInput(_ProjectBase):
    insight_id: int


# Query
class QueryRunInput(_ProjectBase):
    query: dict[str, Any]


# Error tracking
class ErrorTrackingListInput(_ProjectBase):
    limit: int = 100
    offset: int = 0
    search: str | None = None
    status: str | None = None


class ErrorTrackingDetailsInput(_ProjectBase):
    issue_id: str


# Surveys
class SurveyGetAllInput(_ProjectBase):
    limit: int = 100
    offset: int = 0
    search: str | None = None


class SurveyGetInput(_ProjectBase):
    survey_id: str


class SurveyCreateInput(_ProjectBase):
    name: str
    type: str = "popover"
    description: str | None = None
    questions: list[dict[str, Any]] | None = None
    conditions: dict[str, Any] | None = None
    linked_flag_id: int | None = None
    targeting_flag_filters: dict[str, Any] | None = None
    appearance: dict[str, Any] | None = None
    start_date: str | None = None
    end_date: str | None = None


class SurveyUpdateInput(_ProjectBase):
    survey_id: str
    name: str | None = None
    description: str | None = None
    questions: list[dict[str, Any]] | None = None
    conditions: dict[str, Any] | None = None
    archived: bool | None = None
    start_date: str | None = None
    end_date: str | None = None


class SurveyDeleteInput(_ProjectBase):
    survey_id: str


# Org + projects
class OrganizationGetAllInput(BaseModel):
    api_key: str
    base_url: str | None = None


class ProjectGetAllInput(BaseModel):
    api_key: str
    organization_id: str | None = None
    base_url: str | None = None


# Definitions
class EventDefinitionsInput(_ProjectBase):
    limit: int = 100
    offset: int = 0
    search: str | None = None


class PropertyDefinitionsInput(_ProjectBase):
    limit: int = 100
    offset: int = 0
    search: str | None = None
    event_names: list[str] | None = None
    type: str | None = None


# Capture / identify
class CaptureEventInput(_IngestBase):
    distinct_id: str
    event: str
    properties: dict[str, Any] | None = None
    timestamp: str | None = None


class BatchCaptureEventsInput(_IngestBase):
    events: list[dict[str, Any]]
    historical_migration: bool = False


class IdentifyUserInput(_IngestBase):
    distinct_id: str
    properties: dict[str, Any]


class AliasUserInput(_IngestBase):
    distinct_id: str
    alias: str


class EvaluateFeatureFlagsInput(_IngestBase):
    distinct_id: str
    groups: dict[str, str] | None = None
    person_properties: dict[str, Any] | None = None
    group_properties: dict[str, dict[str, Any]] | None = None


class GroupIdentifyInput(_IngestBase):
    group_type: str
    group_key: str
    properties: dict[str, Any]


# Persons
class PersonsGetAllInput(_ProjectBase):
    limit: int = 100
    offset: int = 0
    search: str | None = None
    distinct_id: str | None = None
    email: str | None = None


class PersonGetInput(_ProjectBase):
    person_id: str


class PersonUpdateInput(_ProjectBase):
    person_id: int
    properties: dict[str, Any]


class PersonDeleteInput(_ProjectBase):
    person_id: int
    delete_events: bool = False


class PersonBulkDeleteInput(_ProjectBase):
    person_ids: list[int]
    delete_events: bool = False


# Groups
class GroupsGetAllInput(_ProjectBase):
    group_type_index: int
    search: str | None = None


class FindGroupInput(_ProjectBase):
    group_type_index: int
    group_key: str


class GroupTypesInput(_ProjectBase):
    pass


# Cohorts
class CohortGetAllInput(_ProjectBase):
    pass


class CohortGetInput(_ProjectBase):
    cohort_id: int


class CohortCreateInput(_ProjectBase):
    name: str
    description: str | None = None
    is_static: bool = False
    filters: dict[str, Any] | None = None
    groups: list[dict[str, Any]] | None = None


class CohortUpdateInput(_ProjectBase):
    cohort_id: int
    name: str | None = None
    description: str | None = None
    filters: dict[str, Any] | None = None
    groups: list[dict[str, Any]] | None = None


class CohortDeleteInput(_ProjectBase):
    cohort_id: int


class CohortPersonsInput(_ProjectBase):
    cohort_id: int
    limit: int = 100


# Session recordings
class SessionRecordingsGetAllInput(_ProjectBase):
    limit: int = 100
    offset: int = 0


class SessionRecordingGetInput(_ProjectBase):
    recording_id: str


class SessionRecordingDeleteInput(_ProjectBase):
    recording_id: str


# Actions
class ActionsGetAllInput(_ProjectBase):
    limit: int = 100
    offset: int = 0
    search: str | None = None


class ActionGetInput(_ProjectBase):
    action_id: int


class ActionCreateInput(_ProjectBase):
    name: str
    description: str | None = None
    steps: list[dict[str, Any]] | None = None
    tags: list[str] | None = None


class ActionUpdateInput(_ProjectBase):
    action_id: int
    name: str | None = None
    description: str | None = None
    steps: list[dict[str, Any]] | None = None
    tags: list[str] | None = None


class ActionDeleteInput(_ProjectBase):
    action_id: int


class ActionDeleteByNameInput(_ProjectBase):
    name: str


# Annotations
class AnnotationsGetAllInput(_ProjectBase):
    limit: int = 100
    offset: int = 0
    search: str | None = None


class AnnotationGetInput(_ProjectBase):
    annotation_id: int


class AnnotationCreateInput(_ProjectBase):
    content: str
    date_marker: str
    dashboard_item: int | None = None
    scope: str = "organization"


class AnnotationUpdateInput(_ProjectBase):
    annotation_id: int
    content: str | None = None
    date_marker: str | None = None
    scope: str | None = None


class AnnotationDeleteInput(_ProjectBase):
    annotation_id: int


# Alerts
class AlertsGetAllInput(_ProjectBase):
    limit: int = 100
    offset: int = 0
    insight_id: int | None = None


class AlertGetInput(_ProjectBase):
    alert_id: str


class AlertCreateInput(_ProjectBase):
    insight_id: int
    name: str
    threshold: dict[str, Any] | None = None
    subscribed_users: list[int] | None = None
    enabled: bool = True
    notification_targets: dict[str, Any] | None = None


class AlertUpdateInput(_ProjectBase):
    alert_id: str
    name: str | None = None
    threshold: dict[str, Any] | None = None
    subscribed_users: list[int] | None = None
    enabled: bool | None = None
    notification_targets: dict[str, Any] | None = None


class AlertDeleteInput(_ProjectBase):
    alert_id: str


# Early access features
class EarlyAccessFeaturesGetAllInput(_ProjectBase):
    limit: int = 100
    offset: int = 0


class EarlyAccessFeatureGetInput(_ProjectBase):
    feature_id: str


class EarlyAccessFeatureCreateInput(_ProjectBase):
    name: str
    description: str | None = None
    stage: str = "beta"
    documentation_url: str | None = None
    feature_flag_id: int | None = None


class EarlyAccessFeatureUpdateInput(_ProjectBase):
    feature_id: str
    name: str | None = None
    description: str | None = None
    stage: str | None = None
    documentation_url: str | None = None


class EarlyAccessFeatureDeleteInput(_ProjectBase):
    feature_id: str


class EarlyAccessFeatureDeleteByNameInput(_ProjectBase):
    name: str


# --- Shared filter/payload helpers ----------------------------------------


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _list_params(
    limit: int | None = None,
    offset: int | None = None,
    **extra: Any,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    for key, value in extra.items():
        if value is not None:
            params[key] = value
    return params


# --- Dashboards -----------------------------------------------------------


@tool(args_schema=DashboardGetAllInput)
@serialize_pydantic_return
async def get_dashboards(
    api_key: str,
    project_id: int,
    base_url: str | None = None,
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
    pinned: bool | None = None,
) -> PostHogResult:
    """List dashboards."""
    err = _validate_key(api_key, "get_dashboards")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/dashboards/",
        params=_list_params(limit=limit, offset=offset, search=search, pinned=pinned),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=DashboardGetInput)
@serialize_pydantic_return
async def get_dashboard(
    api_key: str,
    project_id: int,
    dashboard_id: int,
    base_url: str | None = None,
) -> PostHogResult:
    """Get a dashboard."""
    err = _validate_key(api_key, "get_dashboard")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET", api_key, base_url, f"/api/projects/{project_id}/dashboards/{dashboard_id}/"
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=DashboardCreateInput)
@serialize_pydantic_return
async def create_dashboard(
    api_key: str,
    project_id: int,
    name: str,
    base_url: str | None = None,
    description: str | None = None,
    pinned: bool | None = None,
    tags: list[str] | None = None,
) -> PostHogResult:
    """Create a dashboard."""
    err = _validate_key(api_key, "create_dashboard")
    if err:
        return PostHogResult(success=False, error=err)
    body = _drop_none(
        {"name": name, "description": description, "pinned": pinned, "tags": tags}
    )
    ok, e, data = await _call_project(
        "POST",
        api_key,
        base_url,
        f"/api/projects/{project_id}/dashboards/",
        json_body=body,
        success_codes=(200, 201),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=DashboardUpdateInput)
@serialize_pydantic_return
async def update_dashboard(
    api_key: str,
    project_id: int,
    dashboard_id: int,
    base_url: str | None = None,
    name: str | None = None,
    description: str | None = None,
    pinned: bool | None = None,
    tags: list[str] | None = None,
) -> PostHogResult:
    """Update a dashboard."""
    err = _validate_key(api_key, "update_dashboard")
    if err:
        return PostHogResult(success=False, error=err)
    body = _drop_none(
        {"name": name, "description": description, "pinned": pinned, "tags": tags}
    )
    ok, e, data = await _call_project(
        "PATCH",
        api_key,
        base_url,
        f"/api/projects/{project_id}/dashboards/{dashboard_id}/",
        json_body=body,
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=DashboardDeleteInput)
@serialize_pydantic_return
async def delete_dashboard(
    api_key: str,
    project_id: int,
    dashboard_id: int,
    base_url: str | None = None,
) -> PostHogResult:
    """Delete a dashboard."""
    err = _validate_key(api_key, "delete_dashboard")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, _ = await _call_project(
        "DELETE",
        api_key,
        base_url,
        f"/api/projects/{project_id}/dashboards/{dashboard_id}/",
        success_codes=(200, 204),
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True, result={"deleted": True, "dashboard_id": dashboard_id}
    )


# --- Experiments ----------------------------------------------------------


@tool(args_schema=ExperimentListInput)
@serialize_pydantic_return
async def get_experiments(
    api_key: str, project_id: int, base_url: str | None = None
) -> PostHogResult:
    """List experiments."""
    err = _validate_key(api_key, "get_experiments")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET", api_key, base_url, f"/api/projects/{project_id}/experiments/"
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=ExperimentGetInput)
@serialize_pydantic_return
async def get_experiment(
    api_key: str, project_id: int, experiment_id: int, base_url: str | None = None
) -> PostHogResult:
    """Get an experiment."""
    err = _validate_key(api_key, "get_experiment")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/experiments/{experiment_id}/",
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=ExperimentCreateInput)
@serialize_pydantic_return
async def create_experiment(
    api_key: str,
    project_id: int,
    name: str,
    feature_flag_key: str,
    base_url: str | None = None,
    description: str | None = None,
    experiment_type: str = "product",
    primary_metrics: list[dict[str, Any]] | None = None,
    secondary_metrics: list[dict[str, Any]] | None = None,
    variants: list[dict[str, Any]] | None = None,
    minimum_detectable_effect: float = 30,
    filter_test_accounts: bool = True,
) -> PostHogResult:
    """Create an A/B test experiment."""
    err = _validate_key(api_key, "create_experiment")
    if err:
        return PostHogResult(success=False, error=err)
    body: dict[str, Any] = {
        "name": name,
        "feature_flag_key": feature_flag_key,
        "type": experiment_type,
        "parameters": {
            "minimum_detectable_effect": minimum_detectable_effect,
            "feature_flag_variants": variants
            or [
                {"key": "control", "rollout_percentage": 50},
                {"key": "test", "rollout_percentage": 50},
            ],
        },
        "filters": {"filter_test_accounts": filter_test_accounts},
    }
    if description:
        body["description"] = description
    if primary_metrics:
        body["metrics"] = primary_metrics
    if secondary_metrics:
        body["metrics_secondary"] = secondary_metrics

    ok, e, data = await _call_project(
        "POST",
        api_key,
        base_url,
        f"/api/projects/{project_id}/experiments/",
        json_body=body,
        success_codes=(200, 201),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=ExperimentUpdateInput)
@serialize_pydantic_return
async def update_experiment(
    api_key: str,
    project_id: int,
    experiment_id: int,
    base_url: str | None = None,
    name: str | None = None,
    description: str | None = None,
    primary_metrics: list[dict[str, Any]] | None = None,
    secondary_metrics: list[dict[str, Any]] | None = None,
    launch: bool | None = None,
    conclude: str | None = None,
    archive: bool | None = None,
) -> PostHogResult:
    """Update an experiment."""
    err = _validate_key(api_key, "update_experiment")
    if err:
        return PostHogResult(success=False, error=err)
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if description is not None:
        body["description"] = description
    if primary_metrics is not None:
        body["metrics"] = primary_metrics
    if secondary_metrics is not None:
        body["metrics_secondary"] = secondary_metrics
    if launch:
        body["start_date"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if conclude:
        body["end_date"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        body["conclusion"] = conclude
    if archive is not None:
        body["archived"] = archive
    ok, e, data = await _call_project(
        "PATCH",
        api_key,
        base_url,
        f"/api/projects/{project_id}/experiments/{experiment_id}/",
        json_body=body,
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=ExperimentDeleteInput)
@serialize_pydantic_return
async def delete_experiment(
    api_key: str, project_id: int, experiment_id: int, base_url: str | None = None
) -> PostHogResult:
    """Delete an experiment."""
    err = _validate_key(api_key, "delete_experiment")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, _ = await _call_project(
        "DELETE",
        api_key,
        base_url,
        f"/api/projects/{project_id}/experiments/{experiment_id}/",
        success_codes=(200, 204),
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True, result={"deleted": True, "experiment_id": experiment_id}
    )


@tool(args_schema=ExperimentResultsInput)
@serialize_pydantic_return
async def get_experiment_results(
    api_key: str,
    project_id: int,
    experiment_id: int,
    base_url: str | None = None,
    refresh: bool = False,
) -> PostHogResult:
    """Get experiment results."""
    err = _validate_key(api_key, "get_experiment_results")
    if err:
        return PostHogResult(success=False, error=err)
    params: dict[str, Any] = {}
    if refresh:
        params["refresh"] = "true"
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/experiments/{experiment_id}/results/",
        params=params or None,
    )
    return PostHogResult(success=ok, error=e, result=data)


# --- Feature flags --------------------------------------------------------


@tool(args_schema=FeatureFlagListInput)
@serialize_pydantic_return
async def get_feature_flags(
    api_key: str, project_id: int, base_url: str | None = None
) -> PostHogResult:
    """List feature flags."""
    err = _validate_key(api_key, "get_feature_flags")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET", api_key, base_url, f"/api/projects/{project_id}/feature_flags/"
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=FeatureFlagGetInput)
@serialize_pydantic_return
async def get_feature_flag(
    api_key: str,
    project_id: int,
    flag_id: int | None = None,
    flag_key: str | None = None,
    base_url: str | None = None,
) -> PostHogResult:
    """Get a feature flag by ID or key."""
    err = _validate_key(api_key, "get_feature_flag")
    if err:
        return PostHogResult(success=False, error=err)
    if flag_id is None and not flag_key:
        return PostHogResult(
            success=False, error="Either flag_id or flag_key must be provided"
        )
    if flag_id is not None:
        ok, e, data = await _call_project(
            "GET",
            api_key,
            base_url,
            f"/api/projects/{project_id}/feature_flags/{flag_id}/",
        )
    else:
        ok, e, data = await _call_project(
            "GET",
            api_key,
            base_url,
            f"/api/projects/{project_id}/feature_flags/",
            params={"search": flag_key},
        )
        if ok and isinstance(data, dict):
            results = data.get("results") or []
            for flag in results:
                if flag.get("key") == flag_key:
                    data = flag
                    break
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=FeatureFlagCreateInput)
@serialize_pydantic_return
async def create_feature_flag(
    api_key: str,
    project_id: int,
    key: str,
    name: str,
    base_url: str | None = None,
    description: str | None = None,
    filters: dict[str, Any] | None = None,
    active: bool = True,
    tags: list[str] | None = None,
) -> PostHogResult:
    """Create a feature flag."""
    err = _validate_key(api_key, "create_feature_flag")
    if err:
        return PostHogResult(success=False, error=err)
    body: dict[str, Any] = {"key": key, "name": name, "active": active}
    if description:
        body["description"] = description
    if filters:
        body["filters"] = filters
    if tags:
        body["tags"] = tags
    ok, e, data = await _call_project(
        "POST",
        api_key,
        base_url,
        f"/api/projects/{project_id}/feature_flags/",
        json_body=body,
        success_codes=(200, 201),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=FeatureFlagUpdateInput)
@serialize_pydantic_return
async def update_feature_flag(
    api_key: str,
    project_id: int,
    flag_key: str,
    base_url: str | None = None,
    name: str | None = None,
    description: str | None = None,
    filters: dict[str, Any] | None = None,
    active: bool | None = None,
    tags: list[str] | None = None,
) -> PostHogResult:
    """Update a feature flag (looked up by key)."""
    err = _validate_key(api_key, "update_feature_flag")
    if err:
        return PostHogResult(success=False, error=err)
    # First find the flag ID by key.
    ok, e, lookup = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/feature_flags/",
        params={"search": flag_key},
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    results = (lookup or {}).get("results") or []
    flag = next((f for f in results if f.get("key") == flag_key), None)
    if not flag:
        return PostHogResult(success=False, error=f"Feature flag '{flag_key}' not found")

    body = _drop_none(
        {
            "name": name,
            "description": description,
            "filters": filters,
            "active": active,
            "tags": tags,
        }
    )
    ok, e, data = await _call_project(
        "PATCH",
        api_key,
        base_url,
        f"/api/projects/{project_id}/feature_flags/{flag['id']}/",
        json_body=body,
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=FeatureFlagDeleteInput)
@serialize_pydantic_return
async def delete_feature_flag(
    api_key: str, project_id: int, flag_id: int, base_url: str | None = None
) -> PostHogResult:
    """Delete a feature flag."""
    err = _validate_key(api_key, "delete_feature_flag")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, _ = await _call_project(
        "DELETE",
        api_key,
        base_url,
        f"/api/projects/{project_id}/feature_flags/{flag_id}/",
        success_codes=(200, 204),
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(success=True, result={"deleted": True, "flag_id": flag_id})


# --- Insights -------------------------------------------------------------


@tool(args_schema=InsightGetAllInput)
@serialize_pydantic_return
async def get_insights(
    api_key: str,
    project_id: int,
    base_url: str | None = None,
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
) -> PostHogResult:
    """List insights."""
    err = _validate_key(api_key, "get_insights")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/insights/",
        params=_list_params(limit=limit, offset=offset, search=search),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=InsightGetInput)
@serialize_pydantic_return
async def get_insight(
    api_key: str, project_id: int, insight_id: int, base_url: str | None = None
) -> PostHogResult:
    """Get an insight."""
    err = _validate_key(api_key, "get_insight")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/insights/{insight_id}/",
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=InsightCreateInput)
@serialize_pydantic_return
async def create_insight(
    api_key: str,
    project_id: int,
    name: str,
    base_url: str | None = None,
    description: str | None = None,
    filters: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
    dashboards: list[int] | None = None,
    tags: list[str] | None = None,
) -> PostHogResult:
    """Create an insight."""
    err = _validate_key(api_key, "create_insight")
    if err:
        return PostHogResult(success=False, error=err)
    body = _drop_none(
        {
            "name": name,
            "description": description,
            "filters": filters,
            "query": query,
            "dashboards": dashboards,
            "tags": tags,
        }
    )
    ok, e, data = await _call_project(
        "POST",
        api_key,
        base_url,
        f"/api/projects/{project_id}/insights/",
        json_body=body,
        success_codes=(200, 201),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=InsightUpdateInput)
@serialize_pydantic_return
async def update_insight(
    api_key: str,
    project_id: int,
    insight_id: int,
    base_url: str | None = None,
    name: str | None = None,
    description: str | None = None,
    filters: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> PostHogResult:
    """Update an insight."""
    err = _validate_key(api_key, "update_insight")
    if err:
        return PostHogResult(success=False, error=err)
    body = _drop_none(
        {
            "name": name,
            "description": description,
            "filters": filters,
            "query": query,
            "tags": tags,
        }
    )
    ok, e, data = await _call_project(
        "PATCH",
        api_key,
        base_url,
        f"/api/projects/{project_id}/insights/{insight_id}/",
        json_body=body,
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=InsightDeleteInput)
@serialize_pydantic_return
async def delete_insight(
    api_key: str, project_id: int, insight_id: int, base_url: str | None = None
) -> PostHogResult:
    """Delete an insight."""
    err = _validate_key(api_key, "delete_insight")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, _ = await _call_project(
        "DELETE",
        api_key,
        base_url,
        f"/api/projects/{project_id}/insights/{insight_id}/",
        success_codes=(200, 204),
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True, result={"deleted": True, "insight_id": insight_id}
    )


# --- Query / error tracking / surveys -------------------------------------


@tool(args_schema=QueryRunInput)
@serialize_pydantic_return
async def run_query(
    api_key: str,
    project_id: int,
    query: dict[str, Any],
    base_url: str | None = None,
) -> PostHogResult:
    """Run an ad-hoc HogQL/JSON query."""
    err = _validate_key(api_key, "run_query")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "POST",
        api_key,
        base_url,
        f"/api/projects/{project_id}/query/",
        json_body={"query": query},
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=ErrorTrackingListInput)
@serialize_pydantic_return
async def list_error_tracking_issues(
    api_key: str,
    project_id: int,
    base_url: str | None = None,
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
    status: str | None = None,
) -> PostHogResult:
    """List error tracking issues."""
    err = _validate_key(api_key, "list_error_tracking_issues")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/error_tracking/issue/",
        params=_list_params(
            limit=limit, offset=offset, search=search, status=status
        ),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=ErrorTrackingDetailsInput)
@serialize_pydantic_return
async def get_error_tracking_issue(
    api_key: str, project_id: int, issue_id: str, base_url: str | None = None
) -> PostHogResult:
    """Get an error tracking issue."""
    err = _validate_key(api_key, "get_error_tracking_issue")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/error_tracking/issue/{issue_id}/",
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=SurveyGetAllInput)
@serialize_pydantic_return
async def get_surveys(
    api_key: str,
    project_id: int,
    base_url: str | None = None,
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
) -> PostHogResult:
    """List surveys."""
    err = _validate_key(api_key, "get_surveys")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/surveys/",
        params=_list_params(limit=limit, offset=offset, search=search),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=SurveyGetInput)
@serialize_pydantic_return
async def get_survey(
    api_key: str, project_id: int, survey_id: str, base_url: str | None = None
) -> PostHogResult:
    """Get a survey."""
    err = _validate_key(api_key, "get_survey")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/surveys/{survey_id}/",
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=SurveyCreateInput)
@serialize_pydantic_return
async def create_survey(
    api_key: str,
    project_id: int,
    name: str,
    type: str = "popover",
    base_url: str | None = None,
    description: str | None = None,
    questions: list[dict[str, Any]] | None = None,
    conditions: dict[str, Any] | None = None,
    linked_flag_id: int | None = None,
    targeting_flag_filters: dict[str, Any] | None = None,
    appearance: dict[str, Any] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> PostHogResult:
    """Create a survey."""
    err = _validate_key(api_key, "create_survey")
    if err:
        return PostHogResult(success=False, error=err)
    body = _drop_none(
        {
            "name": name,
            "type": type,
            "description": description,
            "questions": questions,
            "conditions": conditions,
            "linked_flag_id": linked_flag_id,
            "targeting_flag_filters": targeting_flag_filters,
            "appearance": appearance,
            "start_date": start_date,
            "end_date": end_date,
        }
    )
    ok, e, data = await _call_project(
        "POST",
        api_key,
        base_url,
        f"/api/projects/{project_id}/surveys/",
        json_body=body,
        success_codes=(200, 201),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=SurveyUpdateInput)
@serialize_pydantic_return
async def update_survey(
    api_key: str,
    project_id: int,
    survey_id: str,
    base_url: str | None = None,
    name: str | None = None,
    description: str | None = None,
    questions: list[dict[str, Any]] | None = None,
    conditions: dict[str, Any] | None = None,
    archived: bool | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> PostHogResult:
    """Update a survey."""
    err = _validate_key(api_key, "update_survey")
    if err:
        return PostHogResult(success=False, error=err)
    body = _drop_none(
        {
            "name": name,
            "description": description,
            "questions": questions,
            "conditions": conditions,
            "archived": archived,
            "start_date": start_date,
            "end_date": end_date,
        }
    )
    ok, e, data = await _call_project(
        "PATCH",
        api_key,
        base_url,
        f"/api/projects/{project_id}/surveys/{survey_id}/",
        json_body=body,
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=SurveyDeleteInput)
@serialize_pydantic_return
async def delete_survey(
    api_key: str, project_id: int, survey_id: str, base_url: str | None = None
) -> PostHogResult:
    """Delete a survey."""
    err = _validate_key(api_key, "delete_survey")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, _ = await _call_project(
        "DELETE",
        api_key,
        base_url,
        f"/api/projects/{project_id}/surveys/{survey_id}/",
        success_codes=(200, 204),
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True, result={"deleted": True, "survey_id": survey_id}
    )


# --- Org / projects / definitions -----------------------------------------


@tool(args_schema=OrganizationGetAllInput)
@serialize_pydantic_return
async def get_organizations(
    api_key: str, base_url: str | None = None
) -> PostHogResult:
    """List organizations the user belongs to."""
    err = _validate_key(api_key, "get_organizations")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET", api_key, base_url, "/api/organizations/"
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=ProjectGetAllInput)
@serialize_pydantic_return
async def get_projects(
    api_key: str,
    organization_id: str | None = None,
    base_url: str | None = None,
) -> PostHogResult:
    """List projects (optionally scoped to an org)."""
    err = _validate_key(api_key, "get_projects")
    if err:
        return PostHogResult(success=False, error=err)
    path = (
        f"/api/organizations/{organization_id}/projects/"
        if organization_id
        else "/api/projects/"
    )
    ok, e, data = await _call_project("GET", api_key, base_url, path)
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=EventDefinitionsInput)
@serialize_pydantic_return
async def get_event_definitions(
    api_key: str,
    project_id: int,
    base_url: str | None = None,
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
) -> PostHogResult:
    """List event definitions."""
    err = _validate_key(api_key, "get_event_definitions")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/event_definitions/",
        params=_list_params(limit=limit, offset=offset, search=search),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=PropertyDefinitionsInput)
@serialize_pydantic_return
async def get_property_definitions(
    api_key: str,
    project_id: int,
    base_url: str | None = None,
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
    event_names: list[str] | None = None,
    type: str | None = None,
) -> PostHogResult:
    """List property definitions."""
    err = _validate_key(api_key, "get_property_definitions")
    if err:
        return PostHogResult(success=False, error=err)
    params: dict[str, Any] = _list_params(limit=limit, offset=offset, search=search)
    if event_names:
        params["event_names"] = ",".join(event_names)
    if type:
        params["type"] = type
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/property_definitions/",
        params=params,
    )
    return PostHogResult(success=ok, error=e, result=data)


# --- Capture / identify (ingest) ------------------------------------------


@tool(args_schema=CaptureEventInput)
@serialize_pydantic_return
async def capture_event(
    project_api_key: str,
    distinct_id: str,
    event: str,
    properties: dict[str, Any] | None = None,
    timestamp: str | None = None,
    ingest_url: str | None = None,
) -> PostHogResult:
    """Capture a single event (ingest API)."""
    body: dict[str, Any] = {
        "api_key": project_api_key,
        "event": event,
        "distinct_id": distinct_id,
    }
    if properties:
        body["properties"] = properties
    if timestamp:
        body["timestamp"] = timestamp
    ok, e, _ = await _call_ingest("POST", ingest_url, "/i/v0/e/", json_body=body)
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True,
        result={"status": "event captured", "event": event, "distinct_id": distinct_id},
    )


@tool(args_schema=BatchCaptureEventsInput)
@serialize_pydantic_return
async def batch_capture_events(
    project_api_key: str,
    events: list[dict[str, Any]],
    historical_migration: bool = False,
    ingest_url: str | None = None,
) -> PostHogResult:
    """Send multiple events in one batch."""
    body = {
        "api_key": project_api_key,
        "batch": events,
        "historical_migration": historical_migration,
    }
    ok, e, _ = await _call_ingest("POST", ingest_url, "/batch/", json_body=body)
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True,
        result={"status": "batch captured", "event_count": len(events)},
    )


@tool(args_schema=IdentifyUserInput)
@serialize_pydantic_return
async def identify_user(
    project_api_key: str,
    distinct_id: str,
    properties: dict[str, Any],
    ingest_url: str | None = None,
) -> PostHogResult:
    """Identify / update properties on a person via $identify."""
    body = {
        "api_key": project_api_key,
        "event": "$identify",
        "distinct_id": distinct_id,
        "properties": {"$set": properties},
    }
    ok, e, _ = await _call_ingest("POST", ingest_url, "/i/v0/e/", json_body=body)
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True,
        result={"status": "user identified", "distinct_id": distinct_id},
    )


@tool(args_schema=AliasUserInput)
@serialize_pydantic_return
async def alias_user(
    project_api_key: str,
    distinct_id: str,
    alias: str,
    ingest_url: str | None = None,
) -> PostHogResult:
    """Create an alias between two distinct IDs."""
    body = {
        "api_key": project_api_key,
        "event": "$create_alias",
        "distinct_id": distinct_id,
        "properties": {"alias": alias},
    }
    ok, e, _ = await _call_ingest("POST", ingest_url, "/i/v0/e/", json_body=body)
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True,
        result={"status": "alias created", "distinct_id": distinct_id, "alias": alias},
    )


@tool(args_schema=EvaluateFeatureFlagsInput)
@serialize_pydantic_return
async def evaluate_feature_flags(
    project_api_key: str,
    distinct_id: str,
    groups: dict[str, str] | None = None,
    person_properties: dict[str, Any] | None = None,
    group_properties: dict[str, dict[str, Any]] | None = None,
    ingest_url: str | None = None,
) -> PostHogResult:
    """Evaluate feature flags for a user (server-side eval)."""
    body: dict[str, Any] = {"api_key": project_api_key, "distinct_id": distinct_id}
    if groups:
        body["groups"] = groups
    if person_properties:
        body["person_properties"] = person_properties
    if group_properties:
        body["group_properties"] = group_properties
    ok, e, data = await _call_ingest(
        "POST", ingest_url, "/flags?v=2", json_body=body
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=GroupIdentifyInput)
@serialize_pydantic_return
async def group_identify(
    project_api_key: str,
    group_type: str,
    group_key: str,
    properties: dict[str, Any],
    ingest_url: str | None = None,
) -> PostHogResult:
    """Identify a group ($groupidentify)."""
    body = {
        "api_key": project_api_key,
        "event": "$groupidentify",
        "distinct_id": "groups_setup_id",
        "properties": {
            "$group_type": group_type,
            "$group_key": group_key,
            "$group_set": properties,
        },
    }
    ok, e, _ = await _call_ingest("POST", ingest_url, "/i/v0/e/", json_body=body)
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True,
        result={
            "status": "group identified",
            "group_type": group_type,
            "group_key": group_key,
        },
    )


# --- Persons --------------------------------------------------------------


@tool(args_schema=PersonsGetAllInput)
@serialize_pydantic_return
async def get_persons(
    api_key: str,
    project_id: int,
    base_url: str | None = None,
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
    distinct_id: str | None = None,
    email: str | None = None,
) -> PostHogResult:
    """List persons."""
    err = _validate_key(api_key, "get_persons")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/persons/",
        params=_list_params(
            limit=limit,
            offset=offset,
            search=search,
            distinct_id=distinct_id,
            email=email,
        ),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=PersonGetInput)
@serialize_pydantic_return
async def get_person(
    api_key: str, project_id: int, person_id: str, base_url: str | None = None
) -> PostHogResult:
    """Get a person."""
    err = _validate_key(api_key, "get_person")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/persons/{person_id}/",
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=PersonUpdateInput)
@serialize_pydantic_return
async def update_person(
    api_key: str,
    project_id: int,
    person_id: int,
    properties: dict[str, Any],
    base_url: str | None = None,
) -> PostHogResult:
    """Update person properties."""
    err = _validate_key(api_key, "update_person")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "PATCH",
        api_key,
        base_url,
        f"/api/projects/{project_id}/persons/{person_id}/",
        json_body={"properties": properties},
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=PersonDeleteInput)
@serialize_pydantic_return
async def delete_person(
    api_key: str,
    project_id: int,
    person_id: int,
    delete_events: bool = False,
    base_url: str | None = None,
) -> PostHogResult:
    """Delete a person (optionally with events)."""
    err = _validate_key(api_key, "delete_person")
    if err:
        return PostHogResult(success=False, error=err)
    params: dict[str, Any] = {}
    if delete_events:
        params["delete_events"] = "true"
    ok, e, _ = await _call_project(
        "DELETE",
        api_key,
        base_url,
        f"/api/projects/{project_id}/persons/{person_id}/",
        params=params or None,
        success_codes=(200, 204),
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(success=True, result={"deleted": True, "person_id": person_id})


@tool(args_schema=PersonBulkDeleteInput)
@serialize_pydantic_return
async def bulk_delete_persons(
    api_key: str,
    project_id: int,
    person_ids: list[int],
    delete_events: bool = False,
    base_url: str | None = None,
) -> PostHogResult:
    """Bulk-delete multiple persons."""
    err = _validate_key(api_key, "bulk_delete_persons")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, _ = await _call_project(
        "POST",
        api_key,
        base_url,
        f"/api/projects/{project_id}/persons/bulk_delete/",
        json_body={"ids": person_ids, "delete_events": delete_events},
        success_codes=(200, 204),
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True, result={"deleted": True, "count": len(person_ids)}
    )


# --- Groups ---------------------------------------------------------------


@tool(args_schema=GroupsGetAllInput)
@serialize_pydantic_return
async def get_groups(
    api_key: str,
    project_id: int,
    group_type_index: int,
    base_url: str | None = None,
    search: str | None = None,
) -> PostHogResult:
    """List groups of a specific type."""
    err = _validate_key(api_key, "get_groups")
    if err:
        return PostHogResult(success=False, error=err)
    params: dict[str, Any] = {"group_type_index": group_type_index}
    if search:
        params["search"] = search
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/groups/",
        params=params,
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=FindGroupInput)
@serialize_pydantic_return
async def find_group(
    api_key: str,
    project_id: int,
    group_type_index: int,
    group_key: str,
    base_url: str | None = None,
) -> PostHogResult:
    """Find a specific group by type + key."""
    err = _validate_key(api_key, "find_group")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/groups/find/",
        params={"group_type_index": group_type_index, "group_key": group_key},
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=GroupTypesInput)
@serialize_pydantic_return
async def get_group_types(
    api_key: str, project_id: int, base_url: str | None = None
) -> PostHogResult:
    """List configured group types."""
    err = _validate_key(api_key, "get_group_types")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET", api_key, base_url, f"/api/projects/{project_id}/groups_types/"
    )
    return PostHogResult(success=ok, error=e, result=data)


# --- Cohorts --------------------------------------------------------------


@tool(args_schema=CohortGetAllInput)
@serialize_pydantic_return
async def get_cohorts(
    api_key: str, project_id: int, base_url: str | None = None
) -> PostHogResult:
    """List cohorts."""
    err = _validate_key(api_key, "get_cohorts")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET", api_key, base_url, f"/api/projects/{project_id}/cohorts/"
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=CohortGetInput)
@serialize_pydantic_return
async def get_cohort(
    api_key: str, project_id: int, cohort_id: int, base_url: str | None = None
) -> PostHogResult:
    """Get a cohort."""
    err = _validate_key(api_key, "get_cohort")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/cohorts/{cohort_id}/",
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=CohortCreateInput)
@serialize_pydantic_return
async def create_cohort(
    api_key: str,
    project_id: int,
    name: str,
    base_url: str | None = None,
    description: str | None = None,
    is_static: bool = False,
    filters: dict[str, Any] | None = None,
    groups: list[dict[str, Any]] | None = None,
) -> PostHogResult:
    """Create a cohort (static or dynamic)."""
    err = _validate_key(api_key, "create_cohort")
    if err:
        return PostHogResult(success=False, error=err)
    body: dict[str, Any] = {"name": name, "is_static": is_static}
    if description:
        body["description"] = description
    if filters:
        body["filters"] = filters
    if groups:
        body["groups"] = groups
    ok, e, data = await _call_project(
        "POST",
        api_key,
        base_url,
        f"/api/projects/{project_id}/cohorts/",
        json_body=body,
        success_codes=(200, 201),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=CohortUpdateInput)
@serialize_pydantic_return
async def update_cohort(
    api_key: str,
    project_id: int,
    cohort_id: int,
    base_url: str | None = None,
    name: str | None = None,
    description: str | None = None,
    filters: dict[str, Any] | None = None,
    groups: list[dict[str, Any]] | None = None,
) -> PostHogResult:
    """Update a cohort."""
    err = _validate_key(api_key, "update_cohort")
    if err:
        return PostHogResult(success=False, error=err)
    body = _drop_none(
        {
            "name": name,
            "description": description,
            "filters": filters,
            "groups": groups,
        }
    )
    ok, e, data = await _call_project(
        "PATCH",
        api_key,
        base_url,
        f"/api/projects/{project_id}/cohorts/{cohort_id}/",
        json_body=body,
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=CohortDeleteInput)
@serialize_pydantic_return
async def delete_cohort(
    api_key: str, project_id: int, cohort_id: int, base_url: str | None = None
) -> PostHogResult:
    """Soft-delete a cohort."""
    err = _validate_key(api_key, "delete_cohort")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, _ = await _call_project(
        "PATCH",
        api_key,
        base_url,
        f"/api/projects/{project_id}/cohorts/{cohort_id}/",
        json_body={"deleted": True},
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(success=True, result={"deleted": True, "cohort_id": cohort_id})


@tool(args_schema=CohortPersonsInput)
@serialize_pydantic_return
async def get_cohort_persons(
    api_key: str,
    project_id: int,
    cohort_id: int,
    base_url: str | None = None,
    limit: int = 100,
) -> PostHogResult:
    """List persons in a cohort."""
    err = _validate_key(api_key, "get_cohort_persons")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/cohorts/{cohort_id}/persons/",
        params={"limit": limit},
    )
    return PostHogResult(success=ok, error=e, result=data)


# --- Session recordings ---------------------------------------------------


@tool(args_schema=SessionRecordingsGetAllInput)
@serialize_pydantic_return
async def get_session_recordings(
    api_key: str,
    project_id: int,
    base_url: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> PostHogResult:
    """List session recordings (metadata only)."""
    err = _validate_key(api_key, "get_session_recordings")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/session_recordings/",
        params={"limit": limit, "offset": offset},
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=SessionRecordingGetInput)
@serialize_pydantic_return
async def get_session_recording(
    api_key: str, project_id: int, recording_id: str, base_url: str | None = None
) -> PostHogResult:
    """Get a specific session recording."""
    err = _validate_key(api_key, "get_session_recording")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/session_recordings/{recording_id}/",
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=SessionRecordingDeleteInput)
@serialize_pydantic_return
async def delete_session_recording(
    api_key: str, project_id: int, recording_id: str, base_url: str | None = None
) -> PostHogResult:
    """Delete a session recording."""
    err = _validate_key(api_key, "delete_session_recording")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, _ = await _call_project(
        "DELETE",
        api_key,
        base_url,
        f"/api/projects/{project_id}/session_recordings/{recording_id}/",
        success_codes=(200, 204),
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True, result={"deleted": True, "recording_id": recording_id}
    )


# --- Actions --------------------------------------------------------------


@tool(args_schema=ActionsGetAllInput)
@serialize_pydantic_return
async def get_actions(
    api_key: str,
    project_id: int,
    base_url: str | None = None,
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
) -> PostHogResult:
    """List actions."""
    err = _validate_key(api_key, "get_actions")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/actions/",
        params=_list_params(limit=limit, offset=offset, search=search),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=ActionGetInput)
@serialize_pydantic_return
async def get_action(
    api_key: str, project_id: int, action_id: int, base_url: str | None = None
) -> PostHogResult:
    """Get an action."""
    err = _validate_key(api_key, "get_action")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/actions/{action_id}/",
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=ActionCreateInput)
@serialize_pydantic_return
async def create_action(
    api_key: str,
    project_id: int,
    name: str,
    base_url: str | None = None,
    description: str | None = None,
    steps: list[dict[str, Any]] | None = None,
    tags: list[str] | None = None,
) -> PostHogResult:
    """Create an action."""
    err = _validate_key(api_key, "create_action")
    if err:
        return PostHogResult(success=False, error=err)
    body = _drop_none({"name": name, "description": description, "steps": steps, "tags": tags})
    ok, e, data = await _call_project(
        "POST",
        api_key,
        base_url,
        f"/api/projects/{project_id}/actions/",
        json_body=body,
        success_codes=(200, 201),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=ActionUpdateInput)
@serialize_pydantic_return
async def update_action(
    api_key: str,
    project_id: int,
    action_id: int,
    base_url: str | None = None,
    name: str | None = None,
    description: str | None = None,
    steps: list[dict[str, Any]] | None = None,
    tags: list[str] | None = None,
) -> PostHogResult:
    """Update an action."""
    err = _validate_key(api_key, "update_action")
    if err:
        return PostHogResult(success=False, error=err)
    body = _drop_none({"name": name, "description": description, "steps": steps, "tags": tags})
    ok, e, data = await _call_project(
        "PATCH",
        api_key,
        base_url,
        f"/api/projects/{project_id}/actions/{action_id}/",
        json_body=body,
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=ActionDeleteInput)
@serialize_pydantic_return
async def delete_action(
    api_key: str, project_id: int, action_id: int, base_url: str | None = None
) -> PostHogResult:
    """Delete an action (soft-delete → rename fallback for legacy API bug)."""
    err = _validate_key(api_key, "delete_action")
    if err:
        return PostHogResult(success=False, error=err)
    path = f"/api/projects/{project_id}/actions/{action_id}/"
    ok, _e, _data = await _call_project(
        "PATCH", api_key, base_url, path, json_body={"deleted": True}
    )
    if ok:
        return PostHogResult(
            success=True, result={"deleted": True, "action_id": action_id}
        )
    # Soft-delete failed — fall back to renaming with a unique archived name.
    rename_ok, e, _ = await _call_project(
        "PATCH",
        api_key,
        base_url,
        path,
        json_body={"name": f"__archived_{action_id}_{int(time.time())}__"},
    )
    if rename_ok:
        return PostHogResult(
            success=True,
            result={
                "renamed": True,
                "action_id": action_id,
                "note": "Soft-delete failed, action was renamed instead",
            },
        )
    return PostHogResult(success=False, error=e)


@tool(args_schema=ActionDeleteByNameInput)
@serialize_pydantic_return
async def delete_action_by_name(
    api_key: str, project_id: int, name: str, base_url: str | None = None
) -> PostHogResult:
    """Find an action by name and delete it (DELETE → PATCH → rename fallback)."""
    err = _validate_key(api_key, "delete_action_by_name")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/actions/",
        params={"search": name, "limit": 100},
    )
    if not ok:
        return PostHogResult(success=False, error=f"API error during search: {e}")
    results = (data or {}).get("results") or []
    target = next(
        (a for a in results if a.get("name") == name and not a.get("deleted", False)),
        None,
    )
    if not target:
        return PostHogResult(
            success=True,
            result={"deleted": False, "name": name, "note": "Action not found - nothing to delete"},
        )
    action_id = target.get("id")
    path = f"/api/projects/{project_id}/actions/{action_id}/"

    hard_ok, _e1, _ = await _call_project(
        "DELETE", api_key, base_url, path, success_codes=(200, 204)
    )
    if hard_ok:
        return PostHogResult(
            success=True, result={"deleted": True, "name": name, "action_id": action_id}
        )
    soft_ok, _e2, _ = await _call_project(
        "PATCH", api_key, base_url, path, json_body={"deleted": True}
    )
    if soft_ok:
        return PostHogResult(
            success=True, result={"deleted": True, "name": name, "action_id": action_id}
        )
    suffix = f"_deleted_{int(time.time())}"
    rename_ok, rename_e, _ = await _call_project(
        "PATCH", api_key, base_url, path, json_body={"name": f"{name}{suffix}"}
    )
    if rename_ok:
        return PostHogResult(
            success=True,
            result={
                "deleted": False,
                "renamed": True,
                "name": name,
                "action_id": action_id,
                "new_name": f"{name}{suffix}",
                "note": "Delete failed, renamed instead to avoid conflict",
            },
        )
    return PostHogResult(success=False, error=f"API error during delete/rename: {rename_e}")


# --- Annotations ----------------------------------------------------------


@tool(args_schema=AnnotationsGetAllInput)
@serialize_pydantic_return
async def get_annotations(
    api_key: str,
    project_id: int,
    base_url: str | None = None,
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
) -> PostHogResult:
    """List annotations."""
    err = _validate_key(api_key, "get_annotations")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/annotations/",
        params=_list_params(limit=limit, offset=offset, search=search),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=AnnotationGetInput)
@serialize_pydantic_return
async def get_annotation(
    api_key: str,
    project_id: int,
    annotation_id: int,
    base_url: str | None = None,
) -> PostHogResult:
    """Get an annotation."""
    err = _validate_key(api_key, "get_annotation")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/annotations/{annotation_id}/",
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=AnnotationCreateInput)
@serialize_pydantic_return
async def create_annotation(
    api_key: str,
    project_id: int,
    content: str,
    date_marker: str,
    base_url: str | None = None,
    dashboard_item: int | None = None,
    scope: str = "organization",
) -> PostHogResult:
    """Create an annotation."""
    err = _validate_key(api_key, "create_annotation")
    if err:
        return PostHogResult(success=False, error=err)
    body: dict[str, Any] = {
        "content": content,
        "date_marker": date_marker,
        "scope": scope,
    }
    if dashboard_item:
        body["dashboard_item"] = dashboard_item
    ok, e, data = await _call_project(
        "POST",
        api_key,
        base_url,
        f"/api/projects/{project_id}/annotations/",
        json_body=body,
        success_codes=(200, 201),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=AnnotationUpdateInput)
@serialize_pydantic_return
async def update_annotation(
    api_key: str,
    project_id: int,
    annotation_id: int,
    base_url: str | None = None,
    content: str | None = None,
    date_marker: str | None = None,
    scope: str | None = None,
) -> PostHogResult:
    """Update an annotation."""
    err = _validate_key(api_key, "update_annotation")
    if err:
        return PostHogResult(success=False, error=err)
    body = _drop_none(
        {"content": content, "date_marker": date_marker, "scope": scope}
    )
    ok, e, data = await _call_project(
        "PATCH",
        api_key,
        base_url,
        f"/api/projects/{project_id}/annotations/{annotation_id}/",
        json_body=body,
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=AnnotationDeleteInput)
@serialize_pydantic_return
async def delete_annotation(
    api_key: str,
    project_id: int,
    annotation_id: int,
    base_url: str | None = None,
) -> PostHogResult:
    """Delete an annotation."""
    err = _validate_key(api_key, "delete_annotation")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, _ = await _call_project(
        "DELETE",
        api_key,
        base_url,
        f"/api/projects/{project_id}/annotations/{annotation_id}/",
        success_codes=(200, 204),
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True, result={"deleted": True, "annotation_id": annotation_id}
    )


# --- Alerts ---------------------------------------------------------------


@tool(args_schema=AlertsGetAllInput)
@serialize_pydantic_return
async def get_alerts(
    api_key: str,
    project_id: int,
    base_url: str | None = None,
    limit: int = 100,
    offset: int = 0,
    insight_id: int | None = None,
) -> PostHogResult:
    """List alerts."""
    err = _validate_key(api_key, "get_alerts")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/alerts/",
        params=_list_params(limit=limit, offset=offset, insight=insight_id),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=AlertGetInput)
@serialize_pydantic_return
async def get_alert(
    api_key: str, project_id: int, alert_id: str, base_url: str | None = None
) -> PostHogResult:
    """Get an alert."""
    err = _validate_key(api_key, "get_alert")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/alerts/{alert_id}/",
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=AlertCreateInput)
@serialize_pydantic_return
async def create_alert(
    api_key: str,
    project_id: int,
    insight_id: int,
    name: str,
    base_url: str | None = None,
    threshold: dict[str, Any] | None = None,
    subscribed_users: list[int] | None = None,
    enabled: bool = True,
    notification_targets: dict[str, Any] | None = None,
) -> PostHogResult:
    """Create an alert."""
    err = _validate_key(api_key, "create_alert")
    if err:
        return PostHogResult(success=False, error=err)
    body: dict[str, Any] = {
        "insight": insight_id,
        "name": name,
        "enabled": enabled,
    }
    if threshold:
        body["threshold"] = threshold
    if subscribed_users:
        body["subscribed_users"] = subscribed_users
    if notification_targets:
        body["notification_targets"] = notification_targets
    ok, e, data = await _call_project(
        "POST",
        api_key,
        base_url,
        f"/api/projects/{project_id}/alerts/",
        json_body=body,
        success_codes=(200, 201),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=AlertUpdateInput)
@serialize_pydantic_return
async def update_alert(
    api_key: str,
    project_id: int,
    alert_id: str,
    base_url: str | None = None,
    name: str | None = None,
    threshold: dict[str, Any] | None = None,
    subscribed_users: list[int] | None = None,
    enabled: bool | None = None,
    notification_targets: dict[str, Any] | None = None,
) -> PostHogResult:
    """Update an alert."""
    err = _validate_key(api_key, "update_alert")
    if err:
        return PostHogResult(success=False, error=err)
    body = _drop_none(
        {
            "name": name,
            "threshold": threshold,
            "subscribed_users": subscribed_users,
            "enabled": enabled,
            "notification_targets": notification_targets,
        }
    )
    ok, e, data = await _call_project(
        "PATCH",
        api_key,
        base_url,
        f"/api/projects/{project_id}/alerts/{alert_id}/",
        json_body=body,
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=AlertDeleteInput)
@serialize_pydantic_return
async def delete_alert(
    api_key: str, project_id: int, alert_id: str, base_url: str | None = None
) -> PostHogResult:
    """Delete an alert."""
    err = _validate_key(api_key, "delete_alert")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, _ = await _call_project(
        "DELETE",
        api_key,
        base_url,
        f"/api/projects/{project_id}/alerts/{alert_id}/",
        success_codes=(200, 204),
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(success=True, result={"deleted": True, "alert_id": alert_id})


# --- Early access features ------------------------------------------------


@tool(args_schema=EarlyAccessFeaturesGetAllInput)
@serialize_pydantic_return
async def get_early_access_features(
    api_key: str,
    project_id: int,
    base_url: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> PostHogResult:
    """List early-access features."""
    err = _validate_key(api_key, "get_early_access_features")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/early_access_feature/",
        params={"limit": limit, "offset": offset},
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=EarlyAccessFeatureGetInput)
@serialize_pydantic_return
async def get_early_access_feature(
    api_key: str, project_id: int, feature_id: str, base_url: str | None = None
) -> PostHogResult:
    """Get an early-access feature."""
    err = _validate_key(api_key, "get_early_access_feature")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/early_access_feature/{feature_id}/",
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=EarlyAccessFeatureCreateInput)
@serialize_pydantic_return
async def create_early_access_feature(
    api_key: str,
    project_id: int,
    name: str,
    base_url: str | None = None,
    description: str | None = None,
    stage: str = "beta",
    documentation_url: str | None = None,
    feature_flag_id: int | None = None,
) -> PostHogResult:
    """Create an early-access feature."""
    err = _validate_key(api_key, "create_early_access_feature")
    if err:
        return PostHogResult(success=False, error=err)
    body: dict[str, Any] = {"name": name, "stage": stage}
    if description:
        body["description"] = description
    if documentation_url:
        body["documentation_url"] = documentation_url
    if feature_flag_id:
        body["feature_flag_id"] = feature_flag_id
    ok, e, data = await _call_project(
        "POST",
        api_key,
        base_url,
        f"/api/projects/{project_id}/early_access_feature/",
        json_body=body,
        success_codes=(200, 201),
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=EarlyAccessFeatureUpdateInput)
@serialize_pydantic_return
async def update_early_access_feature(
    api_key: str,
    project_id: int,
    feature_id: str,
    base_url: str | None = None,
    name: str | None = None,
    description: str | None = None,
    stage: str | None = None,
    documentation_url: str | None = None,
) -> PostHogResult:
    """Update an early-access feature."""
    err = _validate_key(api_key, "update_early_access_feature")
    if err:
        return PostHogResult(success=False, error=err)
    body = _drop_none(
        {
            "name": name,
            "description": description,
            "stage": stage,
            "documentation_url": documentation_url,
        }
    )
    ok, e, data = await _call_project(
        "PATCH",
        api_key,
        base_url,
        f"/api/projects/{project_id}/early_access_feature/{feature_id}/",
        json_body=body,
    )
    return PostHogResult(success=ok, error=e, result=data)


@tool(args_schema=EarlyAccessFeatureDeleteInput)
@serialize_pydantic_return
async def delete_early_access_feature(
    api_key: str, project_id: int, feature_id: str, base_url: str | None = None
) -> PostHogResult:
    """Delete an early-access feature."""
    err = _validate_key(api_key, "delete_early_access_feature")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, _ = await _call_project(
        "DELETE",
        api_key,
        base_url,
        f"/api/projects/{project_id}/early_access_feature/{feature_id}/",
        success_codes=(200, 204),
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True, result={"deleted": True, "feature_id": feature_id}
    )


@tool(args_schema=EarlyAccessFeatureDeleteByNameInput)
@serialize_pydantic_return
async def delete_early_access_feature_by_name(
    api_key: str, project_id: int, name: str, base_url: str | None = None
) -> PostHogResult:
    """Find an early-access feature by name + delete it."""
    err = _validate_key(api_key, "delete_early_access_feature_by_name")
    if err:
        return PostHogResult(success=False, error=err)
    ok, e, data = await _call_project(
        "GET",
        api_key,
        base_url,
        f"/api/projects/{project_id}/early_access_feature/",
    )
    if not ok:
        return PostHogResult(success=False, error=f"API error during search: {e}")
    results = (data or {}).get("results") or []
    target = next((f for f in results if f.get("name") == name), None)
    if not target:
        return PostHogResult(
            success=True,
            result={
                "deleted": False,
                "name": name,
                "note": "Feature not found - nothing to delete",
            },
        )
    feature_id = target.get("id")
    ok, e, _ = await _call_project(
        "DELETE",
        api_key,
        base_url,
        f"/api/projects/{project_id}/early_access_feature/{feature_id}/",
        success_codes=(200, 204),
    )
    if not ok:
        return PostHogResult(success=False, error=e)
    return PostHogResult(
        success=True, result={"deleted": True, "name": name, "feature_id": feature_id}
    )
