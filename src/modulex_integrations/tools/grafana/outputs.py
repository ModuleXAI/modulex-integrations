"""Pydantic response models for the Grafana integration's @tool functions.

Grafana's tools follow the modulex *api_key* runtime convention: each
function signature takes ``api_key: str`` and ``base_url: str`` directly
(the base URL is injected from the credential's ``GRAFANA_BASE_URL``
environment variable, since Grafana is self-hostable and every instance
lives at a different address).

Error model: the HTTP layer returns proper status codes, but every tool
wraps its call in try/except so non-2xx responses, timeouts, and
unexpected exceptions surface as ``success=False`` + ``error`` rather
than raising. Every output model therefore carries both shapes; on
success branches ``error`` stays ``None`` and on failure branches the
data fields stay at their pydantic defaults.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AlertRule",
    "Annotation",
    "CheckDataSourceHealthOutput",
    "ContactPoint",
    "CreateAlertRuleOutput",
    "CreateAnnotationOutput",
    "CreateContactPointOutput",
    "CreateDashboardOutput",
    "CreateFolderOutput",
    "DashboardSearchResult",
    "DataSource",
    "DeleteAlertRuleOutput",
    "DeleteAnnotationOutput",
    "DeleteDashboardOutput",
    "DeleteFolderOutput",
    "Folder",
    "FolderParent",
    "GetAlertRuleOutput",
    "GetDashboardOutput",
    "GetDataSourceOutput",
    "GetFolderOutput",
    "GetHealthOutput",
    "ListAlertRulesOutput",
    "ListAnnotationsOutput",
    "ListContactPointsOutput",
    "ListDashboardsOutput",
    "ListDataSourcesOutput",
    "ListFoldersOutput",
    "UpdateAlertRuleOutput",
    "UpdateAnnotationOutput",
    "UpdateDashboardOutput",
    "UpdateFolderOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class DashboardSearchResult(_Base):
    """A single dashboard search-result row from ``/api/search``."""

    id: int | None = None
    uid: str | None = None
    title: str | None = None
    uri: str | None = None
    url: str | None = None
    type: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_starred: bool | None = None
    folder_id: int | None = None
    folder_uid: str | None = None
    folder_title: str | None = None
    folder_url: str | None = None


class AlertRule(_Base):
    """A provisioned alert rule (shared by list/get/create/update)."""

    id: int | None = None
    uid: str | None = None
    title: str | None = None
    condition: str | None = None
    data: list[Any] = Field(default_factory=list)
    updated: str | None = None
    no_data_state: str | None = None
    exec_err_state: str | None = None
    for_: str | None = None
    keep_firing_for: str | None = None
    missing_series_evals_to_resolve: int | None = None
    annotations: dict[str, Any] = Field(default_factory=dict)
    labels: dict[str, Any] = Field(default_factory=dict)
    is_paused: bool | None = None
    folder_uid: str | None = None
    rule_group: str | None = None
    org_id: int | None = None
    provenance: str | None = None
    notification_settings: dict[str, Any] | None = None
    record: dict[str, Any] | None = None


class Annotation(_Base):
    """A single annotation row from ``/api/annotations``."""

    id: int | None = None
    alert_id: int | None = None
    dashboard_id: int | None = None
    dashboard_uid: str | None = None
    panel_id: int | None = None
    user_id: int | None = None
    user_name: str | None = None
    new_state: str | None = None
    prev_state: str | None = None
    time: int | None = None
    time_end: int | None = None
    text: str | None = None
    metric: str | None = None
    tags: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)


class DataSource(_Base):
    """A single data source from ``/api/datasources``."""

    id: int | None = None
    uid: str | None = None
    org_id: int | None = None
    name: str | None = None
    type: str | None = None
    type_logo_url: str | None = None
    access: str | None = None
    url: str | None = None
    user: str | None = None
    database: str | None = None
    basic_auth: bool | None = None
    basic_auth_user: str | None = None
    with_credentials: bool | None = None
    is_default: bool | None = None
    json_data: dict[str, Any] = Field(default_factory=dict)
    secure_json_fields: dict[str, Any] = Field(default_factory=dict)
    version: int | None = None
    read_only: bool | None = None


class FolderParent(_Base):
    """An ancestor folder entry (nested folders only)."""

    uid: str | None = None
    title: str | None = None
    url: str | None = None


class Folder(_Base):
    """A single folder from ``/api/folders``."""

    id: int | None = None
    uid: str | None = None
    title: str | None = None
    url: str | None = None
    parent_uid: str | None = None
    parents: list[FolderParent] = Field(default_factory=list)
    has_acl: bool | None = None
    can_save: bool | None = None
    can_edit: bool | None = None
    can_admin: bool | None = None
    created_by: str | None = None
    created: str | None = None
    updated_by: str | None = None
    updated: str | None = None
    version: int | None = None


class ContactPoint(_Base):
    """A single notification contact point."""

    uid: str | None = None
    name: str | None = None
    type: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)
    disable_resolve_message: bool | None = None
    provenance: str | None = None


# --- Per-action output models ----------------------------------------------


class GetHealthOutput(_Base):
    success: bool
    error: str | None = None
    commit: str | None = None
    database: str | None = None
    version: str | None = None


class CheckDataSourceHealthOutput(_Base):
    success: bool
    error: str | None = None
    status: str | None = None
    message: str | None = None


class ListDashboardsOutput(_Base):
    success: bool
    error: str | None = None
    dashboards: list[DashboardSearchResult] = Field(default_factory=list)


class GetDashboardOutput(_Base):
    success: bool
    error: str | None = None
    dashboard: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None


class CreateDashboardOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    uid: str | None = None
    url: str | None = None
    status: str | None = None
    version: int | None = None
    slug: str | None = None


class UpdateDashboardOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    uid: str | None = None
    url: str | None = None
    status: str | None = None
    version: int | None = None
    slug: str | None = None


class DeleteDashboardOutput(_Base):
    success: bool
    error: str | None = None
    title: str | None = None
    message: str | None = None
    id: int | None = None


class ListAlertRulesOutput(_Base):
    success: bool
    error: str | None = None
    rules: list[AlertRule] = Field(default_factory=list)


class GetAlertRuleOutput(_Base):
    success: bool
    error: str | None = None
    rule: AlertRule | None = None


class CreateAlertRuleOutput(_Base):
    success: bool
    error: str | None = None
    rule: AlertRule | None = None


class UpdateAlertRuleOutput(_Base):
    success: bool
    error: str | None = None
    rule: AlertRule | None = None


class DeleteAlertRuleOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None


class ListContactPointsOutput(_Base):
    success: bool
    error: str | None = None
    contact_points: list[ContactPoint] = Field(default_factory=list)


class CreateContactPointOutput(_Base):
    success: bool
    error: str | None = None
    uid: str | None = None
    name: str | None = None
    type: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)
    disable_resolve_message: bool | None = None
    provenance: str | None = None


class CreateAnnotationOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    message: str | None = None


class ListAnnotationsOutput(_Base):
    success: bool
    error: str | None = None
    annotations: list[Annotation] = Field(default_factory=list)


class UpdateAnnotationOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    message: str | None = None


class DeleteAnnotationOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None


class ListDataSourcesOutput(_Base):
    success: bool
    error: str | None = None
    data_sources: list[DataSource] = Field(default_factory=list)


class GetDataSourceOutput(_Base):
    success: bool
    error: str | None = None
    data_source: DataSource | None = None


class ListFoldersOutput(_Base):
    success: bool
    error: str | None = None
    folders: list[Folder] = Field(default_factory=list)


class CreateFolderOutput(_Base):
    success: bool
    error: str | None = None
    folder: Folder | None = None


class GetFolderOutput(_Base):
    success: bool
    error: str | None = None
    folder: Folder | None = None


class UpdateFolderOutput(_Base):
    success: bool
    error: str | None = None
    folder: Folder | None = None


class DeleteFolderOutput(_Base):
    success: bool
    error: str | None = None
    uid: str | None = None
    message: str | None = None
