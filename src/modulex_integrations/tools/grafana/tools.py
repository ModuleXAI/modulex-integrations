"""Grafana LangChain ``@tool`` functions.

Twenty-five async tools wrapping the Grafana HTTP API. **The calling
convention is key-based**: the modulex ``ToolExecutor`` injects an
``api_key: str`` (the Grafana service account token) and a
``base_url: str`` (the instance URL, resolved from the credential's
``GRAFANA_BASE_URL`` environment variable) directly into each function.

Because Grafana is self-hostable, every action targets the operator's
own instance base URL — the runtime fills ``base_url`` from the
credential, so the LLM never has to supply it. An optional
``organization_id`` action parameter selects a specific org on
multi-org instances via the ``X-Grafana-Org-Id`` header.

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions. Non-2xx HTTP responses do *not*
raise.
"""
from __future__ import annotations

import json
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.grafana.outputs import (
    AlertRule,
    Annotation,
    CheckDataSourceHealthOutput,
    ContactPoint,
    CreateAlertRuleOutput,
    CreateAnnotationOutput,
    CreateContactPointOutput,
    CreateDashboardOutput,
    CreateFolderOutput,
    DashboardSearchResult,
    DataSource,
    DeleteAlertRuleOutput,
    DeleteAnnotationOutput,
    DeleteDashboardOutput,
    DeleteFolderOutput,
    Folder,
    FolderParent,
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

__all__ = [
    "check_data_source_health",
    "create_alert_rule",
    "create_annotation",
    "create_contact_point",
    "create_dashboard",
    "create_folder",
    "delete_alert_rule",
    "delete_annotation",
    "delete_dashboard",
    "delete_folder",
    "get_alert_rule",
    "get_dashboard",
    "get_data_source",
    "get_folder",
    "get_health",
    "list_alert_rules",
    "list_annotations",
    "list_contact_points",
    "list_dashboards",
    "list_data_sources",
    "list_folders",
    "update_alert_rule",
    "update_annotation",
    "update_dashboard",
    "update_folder",
]

_TIMEOUT = 30.0

_BASE_URL_DESC = (
    "Grafana instance URL (injected from the credential; leave unset)."
)
_ORG_ID_DESC = (
    "Organization ID for multi-org Grafana instances (e.g. 1, 2). "
    "Sent as the X-Grafana-Org-Id header when set."
)


# --- Shared helpers --------------------------------------------------------


def _headers(api_key: str, organization_id: str | None) -> dict[str, str]:
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if organization_id:
        headers["X-Grafana-Org-Id"] = organization_id
    return headers


def _missing_credentials(api_key: str, base_url: str) -> str | None:
    """Return an error string if a required credential is missing/empty."""
    if not api_key or not api_key.strip():
        return (
            "Grafana service account token is empty. "
            "Please configure a valid Grafana credential."
        )
    if not base_url or not base_url.strip():
        return (
            "Grafana instance URL is empty. Please set GRAFANA_BASE_URL "
            "on the credential (e.g. https://your-grafana.com)."
        )
    return None


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _map_alert_rule(rule: dict[str, Any]) -> AlertRule:
    return AlertRule(
        id=rule.get("id"),
        uid=rule.get("uid"),
        title=rule.get("title"),
        condition=rule.get("condition"),
        data=rule.get("data") or [],
        updated=rule.get("updated"),
        no_data_state=rule.get("noDataState"),
        exec_err_state=rule.get("execErrState"),
        for_=rule.get("for"),
        keep_firing_for=rule.get("keep_firing_for") or rule.get("keepFiringFor"),
        missing_series_evals_to_resolve=(
            rule.get("missingSeriesEvalsToResolve")
            if rule.get("missingSeriesEvalsToResolve") is not None
            else rule.get("missing_series_evals_to_resolve")
        ),
        annotations=rule.get("annotations") or {},
        labels=rule.get("labels") or {},
        is_paused=rule.get("isPaused"),
        folder_uid=rule.get("folderUID"),
        rule_group=rule.get("ruleGroup"),
        org_id=rule.get("orgID") if rule.get("orgID") is not None else rule.get("orgId"),
        provenance=rule.get("provenance") or "",
        notification_settings=rule.get("notification_settings"),
        record=rule.get("record"),
    )


def _map_annotation(item: dict[str, Any]) -> Annotation:
    return Annotation(
        id=item.get("id"),
        alert_id=item.get("alertId"),
        dashboard_id=item.get("dashboardId"),
        dashboard_uid=item.get("dashboardUID"),
        panel_id=item.get("panelId"),
        user_id=item.get("userId"),
        user_name=item.get("userName"),
        new_state=item.get("newState"),
        prev_state=item.get("prevState"),
        time=item.get("time"),
        time_end=item.get("timeEnd"),
        text=item.get("text"),
        metric=item.get("metric"),
        tags=item.get("tags") or [],
        data=item.get("data") or {},
    )


def _map_data_source(ds: dict[str, Any]) -> DataSource:
    return DataSource(
        id=ds.get("id"),
        uid=ds.get("uid"),
        org_id=ds.get("orgId"),
        name=ds.get("name"),
        type=ds.get("type"),
        type_logo_url=ds.get("typeLogoUrl"),
        access=ds.get("access"),
        url=ds.get("url"),
        user=ds.get("user"),
        database=ds.get("database"),
        basic_auth=ds.get("basicAuth"),
        basic_auth_user=ds.get("basicAuthUser"),
        with_credentials=ds.get("withCredentials"),
        is_default=ds.get("isDefault"),
        json_data=ds.get("jsonData") or {},
        secure_json_fields=ds.get("secureJsonFields") or {},
        version=ds.get("version"),
        read_only=ds.get("readOnly"),
    )


def _map_folder(f: dict[str, Any]) -> Folder:
    return Folder(
        id=f.get("id"),
        uid=f.get("uid"),
        title=f.get("title"),
        url=f.get("url"),
        parent_uid=f.get("parentUid"),
        parents=[
            FolderParent(uid=p.get("uid"), title=p.get("title"), url=p.get("url"))
            for p in (f.get("parents") or [])
        ],
        has_acl=f.get("hasAcl"),
        can_save=f.get("canSave"),
        can_edit=f.get("canEdit"),
        can_admin=f.get("canAdmin"),
        created_by=f.get("createdBy"),
        created=f.get("created"),
        updated_by=f.get("updatedBy"),
        updated=f.get("updated"),
        version=f.get("version"),
    )


# --- Input schemas (args_schema for each @tool) ----------------------------


class _CommonInput(BaseModel):
    api_key: str = Field(
        description="Grafana service account token (provided by credential system)"
    )
    base_url: str = Field(default="", description=_BASE_URL_DESC)
    organization_id: str | None = Field(default=None, description=_ORG_ID_DESC)


class ListDashboardsInput(_CommonInput):
    query: str | None = Field(default=None, description="Filter dashboards by title")
    tag: str | None = Field(
        default=None, description="Filter by tag (comma-separated for multiple)"
    )
    folder_uids: str | None = Field(
        default=None, description="Filter by folder UIDs (comma-separated)"
    )
    dashboard_uids: str | None = Field(
        default=None, description="Filter by dashboard UIDs (comma-separated)"
    )
    starred: bool | None = Field(default=None, description="Only return starred dashboards")
    limit: int | None = Field(default=None, description="Maximum dashboards to return")
    page: int | None = Field(default=None, description="Page number for pagination (1-based)")


class GetDashboardInput(_CommonInput):
    dashboard_uid: str = Field(description="The UID of the dashboard to retrieve")


class CreateDashboardInput(_CommonInput):
    title: str = Field(description="The title of the new dashboard")
    folder_uid: str | None = Field(
        default=None, description="UID of the folder to create the dashboard in"
    )
    tags: str | None = Field(default=None, description="Comma-separated list of tags")
    timezone: str | None = Field(
        default=None, description="Dashboard timezone (e.g. browser, utc)"
    )
    refresh: str | None = Field(
        default=None, description="Auto-refresh interval (e.g. 5s, 1m, 5m)"
    )
    panels: str | None = Field(
        default=None, description="JSON array of panel configurations"
    )
    overwrite: bool | None = Field(
        default=None, description="Overwrite an existing dashboard with the same title"
    )
    message: str | None = Field(
        default=None, description="Commit message for the dashboard version"
    )


class UpdateDashboardInput(_CommonInput):
    dashboard_uid: str = Field(description="The UID of the dashboard to update")
    title: str | None = Field(default=None, description="New title for the dashboard")
    folder_uid: str | None = Field(
        default=None, description="New folder UID to move the dashboard to"
    )
    tags: str | None = Field(default=None, description="Comma-separated list of new tags")
    timezone: str | None = Field(
        default=None, description="Dashboard timezone (e.g. browser, utc)"
    )
    refresh: str | None = Field(
        default=None, description="Auto-refresh interval (e.g. 5s, 1m, 5m)"
    )
    panels: str | None = Field(
        default=None, description="JSON array of panel configurations"
    )
    overwrite: bool | None = Field(
        default=None, description="Overwrite even on a version conflict"
    )
    message: str | None = Field(
        default=None, description="Commit message for this version"
    )


class DeleteDashboardInput(_CommonInput):
    dashboard_uid: str = Field(description="The UID of the dashboard to delete")


class ListAlertRulesInput(_CommonInput):
    pass


class GetAlertRuleInput(_CommonInput):
    alert_rule_uid: str = Field(description="The UID of the alert rule to retrieve")


class CreateAlertRuleInput(_CommonInput):
    title: str = Field(description="The title of the alert rule")
    folder_uid: str = Field(description="UID of the folder to create the alert in")
    rule_group: str = Field(description="The name of the rule group")
    data: str = Field(description="JSON array of query/expression data objects")
    condition: str | None = Field(
        default=None,
        description="RefId of the query/expression used as the alert condition",
    )
    for_duration: str | None = Field(
        default=None, description="Duration to wait before firing (e.g. 5m, 1h)"
    )
    no_data_state: str | None = Field(
        default=None, description="State when no data is returned (NoData, Alerting, OK)"
    )
    exec_err_state: str | None = Field(
        default=None, description="State on execution error (Error, Alerting, OK)"
    )
    annotations: str | None = Field(default=None, description="JSON object of annotations")
    labels: str | None = Field(default=None, description="JSON object of labels")
    uid: str | None = Field(default=None, description="Optional custom UID for the rule")
    is_paused: bool | None = Field(
        default=None, description="Whether the rule is paused on creation"
    )
    keep_firing_for: str | None = Field(
        default=None, description="Duration to keep firing after the condition stops"
    )
    missing_series_evals_to_resolve: int | None = Field(
        default=None, description="Missing series evaluations before resolving"
    )
    notification_settings: str | None = Field(
        default=None, description="JSON object of per-rule notification settings"
    )
    record: str | None = Field(
        default=None, description="JSON object configuring this as a recording rule"
    )
    disable_provenance: bool | None = Field(
        default=None, description="Set X-Disable-Provenance so the rule stays UI-editable"
    )


class UpdateAlertRuleInput(_CommonInput):
    alert_rule_uid: str = Field(description="The UID of the alert rule to update")
    title: str | None = Field(default=None, description="New title for the alert rule")
    folder_uid: str | None = Field(default=None, description="New folder UID for the rule")
    rule_group: str | None = Field(default=None, description="New rule group name")
    condition: str | None = Field(default=None, description="New condition refId")
    data: str | None = Field(
        default=None, description="New JSON array of query/expression data objects"
    )
    for_duration: str | None = Field(
        default=None, description="Duration to wait before firing (e.g. 5m, 1h)"
    )
    no_data_state: str | None = Field(
        default=None, description="State when no data is returned (NoData, Alerting, OK)"
    )
    exec_err_state: str | None = Field(
        default=None, description="State on execution error (Error, Alerting, OK)"
    )
    annotations: str | None = Field(default=None, description="JSON object of annotations")
    labels: str | None = Field(default=None, description="JSON object of labels")
    is_paused: bool | None = Field(default=None, description="Whether the rule is paused")
    keep_firing_for: str | None = Field(
        default=None, description="Duration to keep firing after the condition stops"
    )
    missing_series_evals_to_resolve: int | None = Field(
        default=None, description="Missing series evaluations before resolving"
    )
    notification_settings: str | None = Field(
        default=None, description="JSON object of per-rule notification settings"
    )
    record: str | None = Field(
        default=None, description="JSON object configuring this as a recording rule"
    )
    disable_provenance: bool | None = Field(
        default=None, description="Set X-Disable-Provenance so the rule stays UI-editable"
    )


class DeleteAlertRuleInput(_CommonInput):
    alert_rule_uid: str = Field(description="The UID of the alert rule to delete")


class ListContactPointsInput(_CommonInput):
    name: str | None = Field(
        default=None, description="Filter contact points by exact name match"
    )


class CreateContactPointInput(_CommonInput):
    name: str = Field(description="Name of the contact point")
    type: str = Field(
        description="Receiver type (e.g. slack, email, pagerduty, webhook)"
    )
    settings: str = Field(
        description="JSON object of type-specific receiver settings"
    )
    disable_resolve_message: bool | None = Field(
        default=None, description="Do not send a notification when the alert resolves"
    )
    disable_provenance: bool | None = Field(
        default=None,
        description="Set X-Disable-Provenance so the contact point stays UI-editable",
    )


class CreateAnnotationInput(_CommonInput):
    text: str = Field(description="The text content of the annotation")
    tags: str | None = Field(default=None, description="Comma-separated list of tags")
    dashboard_uid: str | None = Field(
        default=None,
        description="UID of the dashboard to annotate; omit for a global annotation",
    )
    panel_id: int | None = Field(
        default=None, description="ID of the panel to attach the annotation to"
    )
    time: int | None = Field(
        default=None, description="Start time in epoch milliseconds (defaults to now)"
    )
    time_end: int | None = Field(
        default=None, description="End time in epoch milliseconds for range annotations"
    )


class ListAnnotationsInput(_CommonInput):
    from_: int | None = Field(
        default=None, description="Start time in epoch milliseconds"
    )
    to: int | None = Field(default=None, description="End time in epoch milliseconds")
    dashboard_uid: str | None = Field(
        default=None, description="Dashboard UID to query annotations from"
    )
    dashboard_id: int | None = Field(
        default=None, description="Legacy numeric dashboard ID filter"
    )
    panel_id: int | None = Field(default=None, description="Filter by panel ID")
    alert_id: int | None = Field(default=None, description="Filter by alert ID")
    user_id: int | None = Field(
        default=None, description="Filter by ID of the creating user"
    )
    tags: str | None = Field(
        default=None, description="Comma-separated list of tags to filter by"
    )
    type: str | None = Field(
        default=None, description="Filter by type (alert or annotation)"
    )
    limit: int | None = Field(
        default=None, description="Maximum number of annotations to return"
    )


class UpdateAnnotationInput(_CommonInput):
    annotation_id: int = Field(description="The ID of the annotation to update")
    text: str | None = Field(default=None, description="New text content")
    tags: str | None = Field(default=None, description="Comma-separated list of new tags")
    time: int | None = Field(default=None, description="New start time in epoch ms")
    time_end: int | None = Field(default=None, description="New end time in epoch ms")


class DeleteAnnotationInput(_CommonInput):
    annotation_id: int = Field(description="The ID of the annotation to delete")


class ListDataSourcesInput(_CommonInput):
    pass


class GetDataSourceInput(_CommonInput):
    data_source_id: str = Field(
        description="The ID or UID of the data source to retrieve"
    )


class CheckDataSourceHealthInput(_CommonInput):
    data_source_uid: str = Field(
        description="The UID of the data source to health-check"
    )


class ListFoldersInput(_CommonInput):
    limit: int | None = Field(default=None, description="Maximum folders to return")
    page: int | None = Field(default=None, description="Page number for pagination")
    parent_uid: str | None = Field(
        default=None, description="List children of this folder UID"
    )


class CreateFolderInput(_CommonInput):
    title: str = Field(description="The title of the new folder")
    uid: str | None = Field(default=None, description="Optional UID for the folder")
    parent_uid: str | None = Field(
        default=None, description="Parent folder UID for nested folders"
    )


class GetFolderInput(_CommonInput):
    folder_uid: str = Field(description="The UID of the folder to retrieve")


class UpdateFolderInput(_CommonInput):
    folder_uid: str = Field(description="The UID of the folder to update")
    title: str = Field(description="New title for the folder")


class DeleteFolderInput(_CommonInput):
    folder_uid: str = Field(description="The UID of the folder to delete")
    force_delete_rules: bool | None = Field(
        default=None, description="Delete alert rules stored in the folder along with it"
    )


class GetHealthInput(_CommonInput):
    pass


# --- @tool functions: dashboards -------------------------------------------


@tool(args_schema=ListDashboardsInput)
@serialize_pydantic_return
async def list_dashboards(
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
    query: str | None = None,
    tag: str | None = None,
    folder_uids: str | None = None,
    dashboard_uids: str | None = None,
    starred: bool | None = None,
    limit: int | None = None,
    page: int | None = None,
) -> ListDashboardsOutput:
    """Search and list all dashboards."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return ListDashboardsOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    params: list[tuple[str, Any]] = [("type", "dash-db")]
    if query:
        params.append(("query", query))
    for t in _csv(tag):
        params.append(("tag", t))
    for uid in _csv(folder_uids):
        params.append(("folderUIDs", uid))
    for uid in _csv(dashboard_uids):
        params.append(("dashboardUIDs", uid))
    if starred:
        params.append(("starred", "true"))
    if limit is not None:
        params.append(("limit", str(limit)))
    if page is not None:
        params.append(("page", str(page)))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/api/search",
                headers=_headers(api_key, organization_id),
                params=params,
            )
        if response.status_code != 200:
            return ListDashboardsOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListDashboardsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDashboardsOutput(success=False, error=f"List dashboards failed: {exc}")

    items = data if isinstance(data, list) else []
    return ListDashboardsOutput(
        success=True,
        dashboards=[
            DashboardSearchResult(
                id=d.get("id"),
                uid=d.get("uid"),
                title=d.get("title"),
                uri=d.get("uri"),
                url=d.get("url"),
                type=d.get("type"),
                tags=d.get("tags") or [],
                is_starred=d.get("isStarred"),
                folder_id=d.get("folderId"),
                folder_uid=d.get("folderUid"),
                folder_title=d.get("folderTitle"),
                folder_url=d.get("folderUrl"),
            )
            for d in items
        ],
    )


@tool(args_schema=GetDashboardInput)
@serialize_pydantic_return
async def get_dashboard(
    dashboard_uid: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
) -> GetDashboardOutput:
    """Get a dashboard by its UID."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return GetDashboardOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/api/dashboards/uid/{dashboard_uid.strip()}",
                headers=_headers(api_key, organization_id),
            )
        if response.status_code != 200:
            return GetDashboardOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetDashboardOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetDashboardOutput(success=False, error=f"Get dashboard failed: {exc}")

    return GetDashboardOutput(
        success=True,
        dashboard=data.get("dashboard"),
        meta=data.get("meta"),
    )


@tool(args_schema=CreateDashboardInput)
@serialize_pydantic_return
async def create_dashboard(
    title: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
    folder_uid: str | None = None,
    tags: str | None = None,
    timezone: str | None = None,
    refresh: str | None = None,
    panels: str | None = None,
    overwrite: bool | None = None,
    message: str | None = None,
) -> CreateDashboardOutput:
    """Create a new dashboard."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return CreateDashboardOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    parsed_panels: list[Any] = []
    if panels:
        try:
            parsed_panels = json.loads(panels)
        except json.JSONDecodeError:
            parsed_panels = []

    dashboard: dict[str, Any] = {
        "title": title,
        "tags": _csv(tags),
        "timezone": timezone or "browser",
        "schemaVersion": 39,
        "version": 0,
        "refresh": refresh or "",
        "panels": parsed_panels,
    }
    body: dict[str, Any] = {"dashboard": dashboard, "overwrite": bool(overwrite)}
    if folder_uid:
        body["folderUid"] = folder_uid
    if message:
        body["message"] = message

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/api/dashboards/db",
                headers=_headers(api_key, organization_id),
                json=body,
            )
        if response.status_code != 200:
            return CreateDashboardOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateDashboardOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDashboardOutput(success=False, error=f"Create dashboard failed: {exc}")

    return CreateDashboardOutput(
        success=True,
        id=data.get("id"),
        uid=data.get("uid"),
        url=data.get("url"),
        status=data.get("status"),
        version=data.get("version"),
        slug=data.get("slug"),
    )


@tool(args_schema=UpdateDashboardInput)
@serialize_pydantic_return
async def update_dashboard(
    dashboard_uid: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
    title: str | None = None,
    folder_uid: str | None = None,
    tags: str | None = None,
    timezone: str | None = None,
    refresh: str | None = None,
    panels: str | None = None,
    overwrite: bool | None = None,
    message: str | None = None,
) -> UpdateDashboardOutput:
    """Update an existing dashboard. Fetches the current dashboard and merges your changes."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return UpdateDashboardOutput(success=False, error=err)
    base_url = base_url.rstrip("/")
    headers = _headers(api_key, organization_id)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            current = await client.get(
                f"{base_url}/api/dashboards/uid/{dashboard_uid.strip()}",
                headers=headers,
            )
            if current.status_code != 200:
                return UpdateDashboardOutput(
                    success=False,
                    error=f"Grafana API error ({current.status_code}): {current.text}",
                )
            current_data = current.json()
            dashboard: dict[str, Any] = current_data.get("dashboard") or {}

            if title is not None:
                dashboard["title"] = title
            if tags is not None:
                dashboard["tags"] = _csv(tags)
            if timezone is not None:
                dashboard["timezone"] = timezone
            if refresh is not None:
                dashboard["refresh"] = refresh
            if panels is not None:
                try:
                    dashboard["panels"] = json.loads(panels)
                except json.JSONDecodeError:
                    return UpdateDashboardOutput(
                        success=False, error="Invalid JSON for panels parameter."
                    )
            dashboard["uid"] = dashboard_uid.strip()

            body: dict[str, Any] = {
                "dashboard": dashboard,
                "overwrite": bool(overwrite),
            }
            if folder_uid:
                body["folderUid"] = folder_uid
            if message:
                body["message"] = message

            response = await client.post(
                f"{base_url}/api/dashboards/db", headers=headers, json=body
            )
        if response.status_code != 200:
            return UpdateDashboardOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateDashboardOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateDashboardOutput(success=False, error=f"Update dashboard failed: {exc}")

    return UpdateDashboardOutput(
        success=True,
        id=data.get("id"),
        uid=data.get("uid"),
        url=data.get("url"),
        status=data.get("status"),
        version=data.get("version"),
        slug=data.get("slug"),
    )


@tool(args_schema=DeleteDashboardInput)
@serialize_pydantic_return
async def delete_dashboard(
    dashboard_uid: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
) -> DeleteDashboardOutput:
    """Delete a dashboard by its UID."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return DeleteDashboardOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{base_url}/api/dashboards/uid/{dashboard_uid.strip()}",
                headers=_headers(api_key, organization_id),
            )
        if response.status_code != 200:
            return DeleteDashboardOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return DeleteDashboardOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteDashboardOutput(success=False, error=f"Delete dashboard failed: {exc}")

    return DeleteDashboardOutput(
        success=True,
        title=data.get("title") or "",
        message=data.get("message") or "Dashboard deleted",
        id=data.get("id") or 0,
    )


# --- @tool functions: alert rules ------------------------------------------


@tool(args_schema=ListAlertRulesInput)
@serialize_pydantic_return
async def list_alert_rules(
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
) -> ListAlertRulesOutput:
    """List all alert rules in the Grafana instance."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return ListAlertRulesOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/api/v1/provisioning/alert-rules",
                headers=_headers(api_key, organization_id),
            )
        if response.status_code != 200:
            return ListAlertRulesOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListAlertRulesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAlertRulesOutput(success=False, error=f"List alert rules failed: {exc}")

    items = data if isinstance(data, list) else []
    return ListAlertRulesOutput(
        success=True, rules=[_map_alert_rule(r) for r in items]
    )


@tool(args_schema=GetAlertRuleInput)
@serialize_pydantic_return
async def get_alert_rule(
    alert_rule_uid: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
) -> GetAlertRuleOutput:
    """Get a specific alert rule by its UID."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return GetAlertRuleOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/api/v1/provisioning/alert-rules/{alert_rule_uid.strip()}",
                headers=_headers(api_key, organization_id),
            )
        if response.status_code != 200:
            return GetAlertRuleOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetAlertRuleOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetAlertRuleOutput(success=False, error=f"Get alert rule failed: {exc}")

    return GetAlertRuleOutput(success=True, rule=_map_alert_rule(data))


@tool(args_schema=CreateAlertRuleInput)
@serialize_pydantic_return
async def create_alert_rule(
    title: str,
    folder_uid: str,
    rule_group: str,
    data: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
    condition: str | None = None,
    for_duration: str | None = None,
    no_data_state: str | None = None,
    exec_err_state: str | None = None,
    annotations: str | None = None,
    labels: str | None = None,
    uid: str | None = None,
    is_paused: bool | None = None,
    keep_firing_for: str | None = None,
    missing_series_evals_to_resolve: int | None = None,
    notification_settings: str | None = None,
    record: str | None = None,
    disable_provenance: bool | None = None,
) -> CreateAlertRuleOutput:
    """Create a new alert rule."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return CreateAlertRuleOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    try:
        data_array = json.loads(data)
    except json.JSONDecodeError:
        return CreateAlertRuleOutput(
            success=False, error="Invalid JSON for data parameter."
        )

    body: dict[str, Any] = {
        "title": title,
        "folderUID": folder_uid,
        "ruleGroup": rule_group,
        "data": data_array,
    }
    if organization_id:
        try:
            body["orgID"] = int(organization_id)
        except ValueError:
            pass
    if condition:
        body["condition"] = condition
    if uid:
        body["uid"] = uid.strip()
    if for_duration:
        body["for"] = for_duration
    if no_data_state:
        body["noDataState"] = no_data_state
    if exec_err_state:
        body["execErrState"] = exec_err_state
    if is_paused is not None:
        body["isPaused"] = is_paused
    if keep_firing_for:
        body["keep_firing_for"] = keep_firing_for
    if missing_series_evals_to_resolve is not None:
        body["missingSeriesEvalsToResolve"] = missing_series_evals_to_resolve

    for raw, key, label in (
        (annotations, "annotations", "annotations"),
        (labels, "labels", "labels"),
        (notification_settings, "notification_settings", "notificationSettings"),
        (record, "record", "record"),
    ):
        if raw:
            try:
                body[key] = json.loads(raw)
            except json.JSONDecodeError:
                return CreateAlertRuleOutput(
                    success=False, error=f"Invalid JSON for {label} parameter."
                )

    headers = _headers(api_key, organization_id)
    if disable_provenance:
        headers["X-Disable-Provenance"] = "true"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/api/v1/provisioning/alert-rules",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateAlertRuleOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        result = response.json()
    except httpx.TimeoutException:
        return CreateAlertRuleOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateAlertRuleOutput(success=False, error=f"Create alert rule failed: {exc}")

    return CreateAlertRuleOutput(success=True, rule=_map_alert_rule(result))


@tool(args_schema=UpdateAlertRuleInput)
@serialize_pydantic_return
async def update_alert_rule(
    alert_rule_uid: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
    title: str | None = None,
    folder_uid: str | None = None,
    rule_group: str | None = None,
    condition: str | None = None,
    data: str | None = None,
    for_duration: str | None = None,
    no_data_state: str | None = None,
    exec_err_state: str | None = None,
    annotations: str | None = None,
    labels: str | None = None,
    is_paused: bool | None = None,
    keep_firing_for: str | None = None,
    missing_series_evals_to_resolve: int | None = None,
    notification_settings: str | None = None,
    record: str | None = None,
    disable_provenance: bool | None = None,
) -> UpdateAlertRuleOutput:
    """Update an existing alert rule. Fetches the current rule and merges your changes."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return UpdateAlertRuleOutput(success=False, error=err)
    base_url = base_url.rstrip("/")
    headers = _headers(api_key, organization_id)
    if disable_provenance:
        headers["X-Disable-Provenance"] = "true"
    rule_url = f"{base_url}/api/v1/provisioning/alert-rules/{alert_rule_uid.strip()}"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            current = await client.get(rule_url, headers=headers)
            if current.status_code != 200:
                return UpdateAlertRuleOutput(
                    success=False,
                    error=f"Grafana API error ({current.status_code}): {current.text}",
                )
            body: dict[str, Any] = current.json()

            if title is not None:
                body["title"] = title
            if folder_uid is not None:
                body["folderUID"] = folder_uid
            if rule_group is not None:
                body["ruleGroup"] = rule_group
            if condition is not None:
                body["condition"] = condition
            if for_duration is not None:
                body["for"] = for_duration
            if no_data_state is not None:
                body["noDataState"] = no_data_state
            if exec_err_state is not None:
                body["execErrState"] = exec_err_state
            if is_paused is not None:
                body["isPaused"] = is_paused
            if keep_firing_for is not None:
                body["keep_firing_for"] = keep_firing_for
            if missing_series_evals_to_resolve is not None:
                body["missingSeriesEvalsToResolve"] = missing_series_evals_to_resolve

            for raw, key, label in (
                (data, "data", "data"),
                (annotations, "annotations", "annotations"),
                (labels, "labels", "labels"),
                (notification_settings, "notification_settings", "notificationSettings"),
                (record, "record", "record"),
            ):
                if raw is not None:
                    try:
                        body[key] = json.loads(raw)
                    except json.JSONDecodeError:
                        return UpdateAlertRuleOutput(
                            success=False,
                            error=f"Invalid JSON for {label} parameter.",
                        )

            response = await client.put(rule_url, headers=headers, json=body)
        if response.status_code != 200:
            return UpdateAlertRuleOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        result = response.json()
    except httpx.TimeoutException:
        return UpdateAlertRuleOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateAlertRuleOutput(success=False, error=f"Update alert rule failed: {exc}")

    return UpdateAlertRuleOutput(success=True, rule=_map_alert_rule(result))


@tool(args_schema=DeleteAlertRuleInput)
@serialize_pydantic_return
async def delete_alert_rule(
    alert_rule_uid: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
) -> DeleteAlertRuleOutput:
    """Delete an alert rule by its UID."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return DeleteAlertRuleOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{base_url}/api/v1/provisioning/alert-rules/{alert_rule_uid.strip()}",
                headers=_headers(api_key, organization_id),
            )
        if response.status_code not in (200, 204):
            return DeleteAlertRuleOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteAlertRuleOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteAlertRuleOutput(success=False, error=f"Delete alert rule failed: {exc}")

    return DeleteAlertRuleOutput(
        success=True, message="Alert rule deleted successfully"
    )


# --- @tool functions: contact points ---------------------------------------


@tool(args_schema=ListContactPointsInput)
@serialize_pydantic_return
async def list_contact_points(
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
    name: str | None = None,
) -> ListContactPointsOutput:
    """List all alert notification contact points."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return ListContactPointsOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    params: dict[str, Any] = {}
    if name:
        params["name"] = name

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/api/v1/provisioning/contact-points",
                headers=_headers(api_key, organization_id),
                params=params,
            )
        if response.status_code != 200:
            return ListContactPointsOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListContactPointsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListContactPointsOutput(
            success=False, error=f"List contact points failed: {exc}"
        )

    items = data if isinstance(data, list) else []
    return ListContactPointsOutput(
        success=True,
        contact_points=[
            ContactPoint(
                uid=cp.get("uid"),
                name=cp.get("name"),
                type=cp.get("type"),
                settings=cp.get("settings") or {},
                disable_resolve_message=cp.get("disableResolveMessage"),
                provenance=cp.get("provenance") or "",
            )
            for cp in items
        ],
    )


@tool(args_schema=CreateContactPointInput)
@serialize_pydantic_return
async def create_contact_point(
    name: str,
    type: str,
    settings: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
    disable_resolve_message: bool | None = None,
    disable_provenance: bool | None = None,
) -> CreateContactPointOutput:
    """Create a notification contact point (e.g. Slack, email, PagerDuty)."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return CreateContactPointOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    try:
        parsed_settings = json.loads(settings)
    except json.JSONDecodeError:
        return CreateContactPointOutput(
            success=False, error="Invalid JSON for settings parameter."
        )

    body: dict[str, Any] = {"name": name, "type": type, "settings": parsed_settings}
    if disable_resolve_message is not None:
        body["disableResolveMessage"] = disable_resolve_message

    headers = _headers(api_key, organization_id)
    if disable_provenance:
        headers["X-Disable-Provenance"] = "true"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/api/v1/provisioning/contact-points",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201, 202):
            return CreateContactPointOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateContactPointOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateContactPointOutput(
            success=False, error=f"Create contact point failed: {exc}"
        )

    return CreateContactPointOutput(
        success=True,
        uid=data.get("uid") or "",
        name=data.get("name") or "",
        type=data.get("type") or "",
        settings=data.get("settings") or {},
        disable_resolve_message=data.get("disableResolveMessage"),
        provenance=data.get("provenance") or "",
    )


# --- @tool functions: annotations ------------------------------------------


@tool(args_schema=CreateAnnotationInput)
@serialize_pydantic_return
async def create_annotation(
    text: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
    tags: str | None = None,
    dashboard_uid: str | None = None,
    panel_id: int | None = None,
    time: int | None = None,
    time_end: int | None = None,
) -> CreateAnnotationOutput:
    """Create an annotation on a dashboard or as a global annotation."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return CreateAnnotationOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    body: dict[str, Any] = {"text": text}
    if time:
        body["time"] = time
    if time_end:
        body["timeEnd"] = time_end
    if dashboard_uid:
        body["dashboardUID"] = dashboard_uid
    if panel_id:
        body["panelId"] = panel_id
    if tags:
        body["tags"] = _csv(tags)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/api/annotations",
                headers=_headers(api_key, organization_id),
                json=body,
            )
        if response.status_code != 200:
            return CreateAnnotationOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateAnnotationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateAnnotationOutput(success=False, error=f"Create annotation failed: {exc}")

    return CreateAnnotationOutput(
        success=True,
        id=data.get("id"),
        message=data.get("message") or "Annotation created successfully",
    )


@tool(args_schema=ListAnnotationsInput)
@serialize_pydantic_return
async def list_annotations(
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
    from_: int | None = None,
    to: int | None = None,
    dashboard_uid: str | None = None,
    dashboard_id: int | None = None,
    panel_id: int | None = None,
    alert_id: int | None = None,
    user_id: int | None = None,
    tags: str | None = None,
    type: str | None = None,
    limit: int | None = None,
) -> ListAnnotationsOutput:
    """Query annotations by time range, dashboard, or tags."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return ListAnnotationsOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    params: list[tuple[str, Any]] = []
    if from_:
        params.append(("from", str(from_)))
    if to:
        params.append(("to", str(to)))
    if dashboard_uid:
        params.append(("dashboardUID", dashboard_uid))
    if dashboard_id:
        params.append(("dashboardId", str(dashboard_id)))
    if panel_id:
        params.append(("panelId", str(panel_id)))
    if alert_id:
        params.append(("alertId", str(alert_id)))
    if user_id:
        params.append(("userId", str(user_id)))
    for t in _csv(tags):
        params.append(("tags", t))
    if type:
        params.append(("type", type))
    if limit:
        params.append(("limit", str(limit)))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/api/annotations",
                headers=_headers(api_key, organization_id),
                params=params,
            )
        if response.status_code != 200:
            return ListAnnotationsOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListAnnotationsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAnnotationsOutput(success=False, error=f"List annotations failed: {exc}")

    raw: list[Any] = []
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, list):
                raw.extend(entry)
            else:
                raw.append(entry)
    return ListAnnotationsOutput(
        success=True,
        annotations=[_map_annotation(a) for a in raw if isinstance(a, dict)],
    )


@tool(args_schema=UpdateAnnotationInput)
@serialize_pydantic_return
async def update_annotation(
    annotation_id: int,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
    text: str | None = None,
    tags: str | None = None,
    time: int | None = None,
    time_end: int | None = None,
) -> UpdateAnnotationOutput:
    """Update an existing annotation."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return UpdateAnnotationOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    body: dict[str, Any] = {}
    if text is not None:
        body["text"] = text
    if time:
        body["time"] = time
    if time_end:
        body["timeEnd"] = time_end
    if tags:
        body["tags"] = _csv(tags)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{base_url}/api/annotations/{annotation_id}",
                headers=_headers(api_key, organization_id),
                json=body,
            )
        if response.status_code != 200:
            return UpdateAnnotationOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateAnnotationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateAnnotationOutput(success=False, error=f"Update annotation failed: {exc}")

    return UpdateAnnotationOutput(
        success=True,
        id=data.get("id") or 0,
        message=data.get("message") or "Annotation updated successfully",
    )


@tool(args_schema=DeleteAnnotationInput)
@serialize_pydantic_return
async def delete_annotation(
    annotation_id: int,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
) -> DeleteAnnotationOutput:
    """Delete an annotation by its ID."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return DeleteAnnotationOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{base_url}/api/annotations/{annotation_id}",
                headers=_headers(api_key, organization_id),
            )
        if response.status_code != 200:
            return DeleteAnnotationOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return DeleteAnnotationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteAnnotationOutput(success=False, error=f"Delete annotation failed: {exc}")

    return DeleteAnnotationOutput(
        success=True,
        message=data.get("message") or "Annotation deleted successfully",
    )


# --- @tool functions: data sources -----------------------------------------


@tool(args_schema=ListDataSourcesInput)
@serialize_pydantic_return
async def list_data_sources(
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
) -> ListDataSourcesOutput:
    """List all data sources configured in Grafana."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return ListDataSourcesOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/api/datasources",
                headers=_headers(api_key, organization_id),
            )
        if response.status_code != 200:
            return ListDataSourcesOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListDataSourcesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDataSourcesOutput(success=False, error=f"List data sources failed: {exc}")

    items = data if isinstance(data, list) else []
    return ListDataSourcesOutput(
        success=True, data_sources=[_map_data_source(ds) for ds in items]
    )


@tool(args_schema=GetDataSourceInput)
@serialize_pydantic_return
async def get_data_source(
    data_source_id: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
) -> GetDataSourceOutput:
    """Get a data source by its ID or UID."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return GetDataSourceOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    ds_id = data_source_id.strip()
    if ds_id.isdigit() and len(ds_id) <= 18:
        url = f"{base_url}/api/datasources/{ds_id}"
    else:
        url = f"{base_url}/api/datasources/uid/{ds_id}"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                url, headers=_headers(api_key, organization_id)
            )
        if response.status_code != 200:
            return GetDataSourceOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetDataSourceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetDataSourceOutput(success=False, error=f"Get data source failed: {exc}")

    return GetDataSourceOutput(success=True, data_source=_map_data_source(data))


@tool(args_schema=CheckDataSourceHealthInput)
@serialize_pydantic_return
async def check_data_source_health(
    data_source_uid: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
) -> CheckDataSourceHealthOutput:
    """Test connectivity to a data source by its UID."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return CheckDataSourceHealthOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/api/datasources/uid/{data_source_uid.strip()}/health",
                headers=_headers(api_key, organization_id),
            )
        if response.status_code != 200:
            return CheckDataSourceHealthOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CheckDataSourceHealthOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CheckDataSourceHealthOutput(
            success=False, error=f"Check data source health failed: {exc}"
        )

    return CheckDataSourceHealthOutput(
        success=True,
        status=data.get("status") or "UNKNOWN",
        message=data.get("message") or "",
    )


# --- @tool functions: folders ----------------------------------------------


@tool(args_schema=ListFoldersInput)
@serialize_pydantic_return
async def list_folders(
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
    limit: int | None = None,
    page: int | None = None,
    parent_uid: str | None = None,
) -> ListFoldersOutput:
    """List all folders in Grafana."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return ListFoldersOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if page is not None:
        params["page"] = page
    if parent_uid:
        params["parentUid"] = parent_uid.strip()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/api/folders",
                headers=_headers(api_key, organization_id),
                params=params,
            )
        if response.status_code != 200:
            return ListFoldersOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListFoldersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFoldersOutput(success=False, error=f"List folders failed: {exc}")

    items = data if isinstance(data, list) else []
    return ListFoldersOutput(success=True, folders=[_map_folder(f) for f in items])


@tool(args_schema=CreateFolderInput)
@serialize_pydantic_return
async def create_folder(
    title: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
    uid: str | None = None,
    parent_uid: str | None = None,
) -> CreateFolderOutput:
    """Create a new folder in Grafana."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return CreateFolderOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    body: dict[str, Any] = {"title": title}
    if uid:
        body["uid"] = uid
    if parent_uid:
        body["parentUid"] = parent_uid

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/api/folders",
                headers=_headers(api_key, organization_id),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateFolderOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateFolderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateFolderOutput(success=False, error=f"Create folder failed: {exc}")

    return CreateFolderOutput(success=True, folder=_map_folder(data))


@tool(args_schema=GetFolderInput)
@serialize_pydantic_return
async def get_folder(
    folder_uid: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
) -> GetFolderOutput:
    """Get a folder by its UID."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return GetFolderOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/api/folders/{folder_uid.strip()}",
                headers=_headers(api_key, organization_id),
            )
        if response.status_code != 200:
            return GetFolderOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetFolderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetFolderOutput(success=False, error=f"Get folder failed: {exc}")

    return GetFolderOutput(success=True, folder=_map_folder(data))


@tool(args_schema=UpdateFolderInput)
@serialize_pydantic_return
async def update_folder(
    folder_uid: str,
    title: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
) -> UpdateFolderOutput:
    """Update (rename) a folder. Fetches the current folder and merges your changes."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return UpdateFolderOutput(success=False, error=err)
    base_url = base_url.rstrip("/")
    headers = _headers(api_key, organization_id)
    folder_url = f"{base_url}/api/folders/{folder_uid.strip()}"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            current = await client.get(folder_url, headers=headers)
            if current.status_code != 200:
                return UpdateFolderOutput(
                    success=False,
                    error=f"Grafana API error ({current.status_code}): {current.text}",
                )
            current_data = current.json()
            body: dict[str, Any] = {
                "title": title,
                "version": current_data.get("version"),
                "overwrite": True,
            }
            response = await client.put(folder_url, headers=headers, json=body)
        if response.status_code != 200:
            return UpdateFolderOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateFolderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateFolderOutput(success=False, error=f"Update folder failed: {exc}")

    return UpdateFolderOutput(success=True, folder=_map_folder(data))


@tool(args_schema=DeleteFolderInput)
@serialize_pydantic_return
async def delete_folder(
    folder_uid: str,
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
    force_delete_rules: bool | None = None,
) -> DeleteFolderOutput:
    """Delete a folder by its UID."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return DeleteFolderOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    params: dict[str, Any] = {}
    if force_delete_rules:
        params["forceDeleteRules"] = "true"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{base_url}/api/folders/{folder_uid.strip()}",
                headers=_headers(api_key, organization_id),
                params=params,
            )
        if response.status_code not in (200, 204):
            return DeleteFolderOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError):
            data = {}
    except httpx.TimeoutException:
        return DeleteFolderOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteFolderOutput(success=False, error=f"Delete folder failed: {exc}")

    return DeleteFolderOutput(
        success=True,
        uid=folder_uid.strip(),
        message=(data.get("message") if isinstance(data, dict) else None) or "Folder deleted",
    )


# --- @tool functions: health -----------------------------------------------


@tool(args_schema=GetHealthInput)
@serialize_pydantic_return
async def get_health(
    api_key: str,
    base_url: str = "",
    organization_id: str | None = None,
) -> GetHealthOutput:
    """Check the health of the Grafana instance (version, database status)."""
    err = _missing_credentials(api_key, base_url)
    if err:
        return GetHealthOutput(success=False, error=err)
    base_url = base_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{base_url}/api/health",
                headers=_headers(api_key, organization_id),
            )
        if response.status_code != 200:
            return GetHealthOutput(
                success=False,
                error=f"Grafana API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetHealthOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetHealthOutput(success=False, error=f"Get health failed: {exc}")

    return GetHealthOutput(
        success=True,
        commit=data.get("commit") or "",
        database=data.get("database") or "",
        version=data.get("version") or "",
    )
