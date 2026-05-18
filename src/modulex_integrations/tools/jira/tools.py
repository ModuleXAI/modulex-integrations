"""Jira LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.jira.outputs import (
    AddAttachmentToIssueOutput,
    AddCommentToIssueOutput,
    AddMultipleAttachmentsToIssueOutput,
    AddWatcherToIssueOutput,
    AssignIssueOutput,
    BoardSummary,
    CheckIssuesAgainstJqlOutput,
    CloudSite,
    CommentSummary,
    CountIssuesUsingJqlOutput,
    CreateCustomFieldOptionsContextOutput,
    CreateFutureSprintOutput,
    CreateIssueOutput,
    CreateVersionOutput,
    DeleteProjectOutput,
    EpicSummary,
    GetAllProjectsOutput,
    GetBoardOutput,
    GetCloudIdOutput,
    GetCurrentUserOutput,
    GetIssueOutput,
    GetIssuePickerSuggestionsOutput,
    GetIssueTypesOutput,
    GetSprintOutput,
    GetTaskOutput,
    GetTransitionsOutput,
    GetUserOutput,
    GetUsersOutput,
    IssueSummary,
    IssueTypeSummary,
    JqlMatchResult,
    ListBoardIssuesOutput,
    ListBoardsOutput,
    ListEpicIssuesOutput,
    ListEpicsOutput,
    ListIssueCommentsOutput,
    ListLabelsOptionsOutput,
    ListSprintIssuesOutput,
    ListSprintsOutput,
    MoveIssuesToSprintOutput,
    ProjectSummary,
    SearchIssuesWithJqlOutput,
    SearchIssuesWithJqlPostOutput,
    SprintSummary,
    SuggestionSection,
    TransitionIssueOutput,
    TransitionSummary,
    UpdateCommentOutput,
    UpdateIssueOutput,
    UserSummary,
    VersionSummary,
)

__all__ = [
    "add_attachment_to_issue",
    "add_comment_to_issue",
    "add_multiple_attachments_to_issue",
    "add_watcher_to_issue",
    "assign_issue",
    "check_issues_against_jql",
    "count_issues_using_jql",
    "create_custom_field_options_context",
    "create_future_sprint",
    "create_issue",
    "create_version",
    "delete_project",
    "get_all_projects",
    "get_board",
    "get_cloud_id",
    "get_current_user",
    "get_issue",
    "get_issue_picker_suggestions",
    "get_issue_types",
    "get_sprint",
    "get_task",
    "get_transitions",
    "get_user",
    "get_users",
    "list_board_issues",
    "list_boards",
    "list_epic_issues",
    "list_epics",
    "list_issue_comments",
    "list_labels_options",
    "list_sprint_issues",
    "list_sprints",
    "move_issues_to_sprint",
    "search_issues_with_jql",
    "search_issues_with_jql_post",
    "transition_issue",
    "update_comment",
    "update_issue",
]

_CLOUD_API = "https://api.atlassian.com"


def _rest_url(cloud_id: str, path: str) -> str:
    return f"{_CLOUD_API}/ex/jira/{cloud_id}/rest/api/3{path}"


def _agile_url(cloud_id: str, path: str) -> str:
    return f"{_CLOUD_API}/ex/jira/{cloud_id}/rest/agile/1.0{path}"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _to_adf(text: str) -> dict[str, Any]:
    return {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


def _parse_issue(i: dict[str, Any]) -> IssueSummary:
    fields = i.get("fields") or {}
    status_obj = fields.get("status") or {}
    issue_type_obj = fields.get("issuetype") or {}
    priority_obj = fields.get("priority") or {}
    assignee_obj = fields.get("assignee") or {}
    reporter_obj = fields.get("reporter") or {}
    return IssueSummary(
        id=i.get("id"),
        key=i.get("key"),
        self_url=i.get("self"),
        summary=fields.get("summary"),
        status=status_obj.get("name"),
        issue_type=issue_type_obj.get("name"),
        priority=priority_obj.get("name"),
        assignee=assignee_obj.get("displayName"),
        reporter=reporter_obj.get("displayName"),
        created=fields.get("created"),
        updated=fields.get("updated"),
        fields=fields,
    )


# --- Input schemas --------------------------------------------------------


class AddAttachmentToIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    issue_id_or_key: str = Field(description="The ID or key of the issue")
    file: str = Field(description="A file URL to attach to the issue")


class AddCommentToIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    issue_id_or_key: str = Field(description="The ID or key of the issue")
    comment: str | None = Field(default=None, description="The comment text in plain text (converted to Atlassian Document Format)")
    body: dict[str, Any] | None = Field(default=None, description="The comment text in Atlassian Document Format (JSON object)")
    visibility: dict[str, Any] | None = Field(default=None, description="The group or role to which this comment is visible")
    properties: str | None = Field(default=None, description="A JSON array of comment properties")
    additional_properties: dict[str, Any] | None = Field(default=None, description="Extra properties of any type to include")
    expand: str | None = Field(default=None, description="Use 'renderedBody' to get comment body rendered in HTML")


class AddMultipleAttachmentsToIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    issue_id_or_key: str = Field(description="The ID or key of the issue")
    files: list[str] = Field(description="An array of file URLs to attach to the issue")


class AddWatcherToIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    issue_id_or_key: str = Field(description="The ID or key of the issue")
    account_id: str = Field(description="The account ID of the user to add as watcher")


class AssignIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    issue_id_or_key: str = Field(description="The ID or key of the issue")
    account_id: str = Field(description="The account ID of the user to assign")


class CheckIssuesAgainstJqlInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    issue_ids: list[int] = Field(description="A list of issue IDs to check against the JQL queries")
    jqls: list[str] = Field(description="A list of JQL query strings to check the issues against")


class CountIssuesUsingJqlInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    jql: str = Field(description="The JQL query to count issues")


class CreateCustomFieldOptionsContextInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    field_id: str = Field(description="The ID of the custom field")
    context_id: str = Field(description="The ID of the field context")


class CreateFutureSprintInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    board_id: str = Field(description="The ID of the board the sprint will be created on")
    name: str = Field(description="The name of the sprint")
    goal: str | None = Field(default=None, description="The goal of the sprint")
    start_date: str | None = Field(default=None, description="The start date in ISO 8601 format")
    end_date: str | None = Field(default=None, description="The end date in ISO 8601 format")


class CreateIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    project_id: str = Field(description="The project ID")
    issue_type_id: str = Field(description="The issue type ID")
    update_history: bool | None = Field(default=None, description="Whether the project is added to the user's Recently viewed project list")
    history_metadata: dict[str, Any] | None = Field(default=None, description="Additional issue history details")
    properties: str | None = Field(default=None, description="Details of issue properties to add or update (JSON array)")
    update: dict[str, Any] | None = Field(default=None, description="A map of field name to operations list for issue screen fields")
    additional_properties: dict[str, Any] | None = Field(default=None, description="Extra fields to include in the issue body (e.g. summary, description, labels, priority)")


class CreateVersionInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    project_id: str = Field(description="The project ID")
    name: str = Field(description="The unique name of the version. Max 255 characters")
    description: str | None = Field(default=None, description="The description of the version")
    archived: bool | None = Field(default=None, description="Indicates that the version is archived")
    start_date: str | None = Field(default=None, description="The start date (yyyy-mm-dd)")
    release_date: str | None = Field(default=None, description="The release date (yyyy-mm-dd)")
    expand: str | None = Field(default=None, description="Expand options: operations, issuesstatus")


class DeleteProjectInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    project_id: str = Field(description="The project ID or key")
    enable_undo: bool = Field(description="Whether this project is placed in the Jira recycle bin for recovery")


class GetAllProjectsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    recent: int | None = Field(default=None, description="Returns the user's most recently accessed projects (max 20)")
    properties: str | None = Field(default=None, description="Issue properties to include (JSON array)")
    expand: str | None = Field(default=None, description="Expand options: description, issueTypes, lead, projectKeys")


class GetBoardInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    board_id: str = Field(description="The ID of the board")


class GetCloudIdInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class GetCurrentUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")


class GetIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    issue_id_or_key: str = Field(description="The ID or key of the issue")
    fields: str | None = Field(default=None, description="Comma-separated list of fields to return")
    fields_by_keys: bool | None = Field(default=None, description="Whether fields are referenced by keys rather than IDs")
    properties: str | None = Field(default=None, description="Issue properties to include (comma-separated or *all)")
    update_history: bool | None = Field(default=None, description="Whether project is added to Recently viewed")
    expand: str | None = Field(default=None, description="Expand options: renderedFields, names, schema, transitions, editmeta, changelog, versionedRepresentations")


class GetIssuePickerSuggestionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    query: str | None = Field(default=None, description="A string to match against issue text fields")
    current_jql: str | None = Field(default=None, description="A JQL query defining a list of issues to search within")
    current_issue_key: str | None = Field(default=None, description="The key of an issue to exclude from results")
    current_project_id: str | None = Field(default=None, description="The ID of a project that results must belong to")
    show_sub_tasks: bool | None = Field(default=None, description="Whether to include subtasks in suggestions")
    show_sub_task_parent: bool | None = Field(default=None, description="Whether to include the parent issue when currentIssueKey is a subtask")


class GetIssueTypesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    project_id: str | None = Field(default=None, description="The project ID to filter issue types")


class GetSprintInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    sprint_id: str = Field(description="The ID of the sprint")


class GetTaskInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    task_id: str = Field(description="The ID of the long-running async task")


class GetTransitionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    issue_id_or_key: str = Field(description="The ID or key of the issue")
    transition_id: str | None = Field(default=None, description="The ID of a specific transition to retrieve")
    skip_remote_only_condition: bool | None = Field(default=None, description="Whether transitions with Hide From User Condition are included")
    include_unavailable_transitions: bool | None = Field(default=None, description="Whether details of failing-condition transitions are included")
    sort_by_ops_bar_and_status: bool | None = Field(default=None, description="Whether transitions are sorted by ops-bar sequence then category")
    expand: str | None = Field(default=None, description="Expand options: transitions.fields")


class GetUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    account_id: str = Field(description="The account ID of the user")
    expand: str | None = Field(default=None, description="Expand options: groups, applicationRoles")


class GetUsersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    query: str | None = Field(default=None, description="Filter for a name or term")


class ListBoardIssuesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    board_id: str = Field(description="The ID of the board")
    start_at: int | None = Field(default=None, description="The starting index of the returned issues. Base index: 0")
    max_results: int | None = Field(default=None, description="The maximum number of issues to return")
    jql: str | None = Field(default=None, description="Filters results using a JQL query")
    fields: str | None = Field(default=None, description="Comma-separated list of fields to return per issue")
    expand: str | None = Field(default=None, description="Expand options for additional information")


class ListBoardsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    start_at: int | None = Field(default=None, description="The starting index of the returned boards. Base index: 0")
    max_results: int | None = Field(default=None, description="The maximum number of boards to return")
    type: str | None = Field(default=None, description="Filters by board type: scrum, kanban, simple")
    name: str | None = Field(default=None, description="Filters results to boards matching this name")
    project_key_or_id: str | None = Field(default=None, description="Filters results to boards relevant to a project")


class ListEpicIssuesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    board_id: str = Field(description="The ID of the board")
    epic_id: str = Field(description="The ID of the epic")
    start_at: int | None = Field(default=None, description="The starting index of the returned issues. Base index: 0")
    max_results: int | None = Field(default=None, description="The maximum number of issues to return")
    jql: str | None = Field(default=None, description="Filters results using a JQL query")
    fields: str | None = Field(default=None, description="Comma-separated list of fields to return per issue")
    expand: str | None = Field(default=None, description="Expand options for additional information")


class ListEpicsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    board_id: str = Field(description="The ID of the board")
    start_at: int | None = Field(default=None, description="The starting index of the returned epics. Base index: 0")
    max_results: int | None = Field(default=None, description="The maximum number of epics to return")
    done: bool | None = Field(default=None, description="Filter to epics that are done or not done")


class ListIssueCommentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    issue_id_or_key: str = Field(description="The ID or key of the issue")
    order_by: str | None = Field(default=None, description="Order results by a field. Valid: created, +created, -created")
    expand: str | None = Field(default=None, description="Expand options: renderedBody")


class ListLabelsOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")


class ListSprintIssuesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    sprint_id: str = Field(description="The ID of the sprint")
    start_at: int | None = Field(default=None, description="The starting index of the returned issues. Base index: 0")
    max_results: int | None = Field(default=None, description="The maximum number of issues to return")
    jql: str | None = Field(default=None, description="Filters results using a JQL query")
    fields: str | None = Field(default=None, description="Comma-separated list of fields to return per issue")
    expand: str | None = Field(default=None, description="Expand options for additional information")


class ListSprintsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    board_id: str = Field(description="The ID of the board")
    start_at: int | None = Field(default=None, description="The starting index of the returned sprints. Base index: 0")
    max_results: int | None = Field(default=None, description="The maximum number of sprints to return")
    state: str | None = Field(default=None, description="Filter by sprint states: future, active, closed (comma-separated)")


class MoveIssuesToSprintInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    sprint_id: str = Field(description="The ID of the sprint")
    issues: list[str] = Field(description="The IDs or keys of the issues to move to the sprint")


class SearchIssuesWithJqlInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    jql: str = Field(description="The JQL query to search for issues")
    max_results: int | None = Field(default=None, description="Maximum number of issues to return (default 50, max 5000)")
    fields: str | None = Field(default=None, description="Comma-separated list of fields to return")
    expand: list[str] | None = Field(default=None, description="Expand options: renderedFields, names, schema, transitions, editmeta, changelog, versionedRepresentations")
    properties: str | None = Field(default=None, description="Comma-separated list of issue properties to include (max 5)")
    fields_by_keys: bool | None = Field(default=None, description="Reference fields by key rather than ID")
    fail_fast: bool | None = Field(default=None, description="Fail early if not all field data can be retrieved")


class SearchIssuesWithJqlPostInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    jql: str = Field(description="The JQL query to search for issues")
    max_results: int | None = Field(default=None, description="Maximum number of items per page")
    next_page_token: str | None = Field(default=None, description="Token for pagination from a previous response")
    fields: list[str] | None = Field(default=None, description="Fields to return per issue. Example: ['summary', 'status']")
    expand: list[str] | None = Field(default=None, description="Expand options: renderedFields, names, schema, transitions, editmeta, changelog, versionedRepresentations")
    properties: list[str] | None = Field(default=None, description="Issue property keys to include (max 5)")
    fields_by_keys: bool | None = Field(default=None, description="Reference fields by key rather than ID")
    reconcile_issues: list[str] | None = Field(default=None, description="Issue IDs/keys for read-after-write consistency")


class TransitionIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    issue_id_or_key: str = Field(description="The ID or key of the issue")
    transition: str = Field(description="The transition ID to perform")
    fields: dict[str, Any] | None = Field(default=None, description="List of issue screen fields to update during transition")
    update: dict[str, Any] | None = Field(default=None, description="Operations to perform on issue screen fields")
    history_metadata: dict[str, Any] | None = Field(default=None, description="Additional issue history details")
    properties: str | None = Field(default=None, description="Issue properties to add or update (JSON)")
    additional_properties: dict[str, Any] | None = Field(default=None, description="Extra properties of any type")


class UpdateCommentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    issue_id_or_key: str = Field(description="The ID or key of the issue")
    comment_id: str = Field(description="The ID of the comment to update")
    body: dict[str, Any] | None = Field(default=None, description="The comment text in Atlassian Document Format (JSON)")
    comment: str | None = Field(default=None, description="The comment text (plain text)")
    visibility: dict[str, Any] | None = Field(default=None, description="The group or role to which this comment is visible")
    properties: str | None = Field(default=None, description="Comment properties (JSON array)")
    additional_properties: dict[str, Any] | None = Field(default=None, description="Extra properties of any type")
    notify_users: bool | None = Field(default=None, description="Whether users are notified when comment is updated")
    expand: str | None = Field(default=None, description="Expand options: renderedBody")


class UpdateIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    cloud_id: str = Field(description="The cloud ID of the Jira site")
    project_id: str = Field(description="The project ID")
    issue_id_or_key: str = Field(description="The ID or key of the issue")
    issue_type_id: str | None = Field(default=None, description="The issue type ID")
    notify_users: bool | None = Field(default=None, description="Whether a notification email is sent to watchers")
    override_screen_security: bool | None = Field(default=None, description="Override screen security to enable hidden fields")
    override_editable_flag: bool | None = Field(default=None, description="Override editable flag to enable uneditable fields")
    transition_id: str | None = Field(default=None, description="The ID of the transition to undertake")
    transition_looped: bool | None = Field(default=None, description="Whether the transition is looped")
    history_metadata: dict[str, Any] | None = Field(default=None, description="Additional issue history details")
    properties: str | None = Field(default=None, description="Issue properties to add or update (JSON array)")
    update: dict[str, Any] | None = Field(default=None, description="A map of field name to operations list")
    additional_properties: dict[str, Any] | None = Field(default=None, description="Extra fields to update (e.g. summary, description)")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AddAttachmentToIssueInput)
@serialize_pydantic_return
async def add_attachment_to_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    issue_id_or_key: str,
    file: str,
) -> AddAttachmentToIssueOutput:
    """Adds an attachment to an issue."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["X-Atlassian-Token"] = "no-check"
    del headers["Accept"]
    async with httpx.AsyncClient() as client:
        file_resp = await client.get(file)
        file_resp.raise_for_status()
        filename = file.rsplit("/", 1)[-1] or "attachment"
        content_type = file_resp.headers.get("content-type", "application/octet-stream")
        response = await client.post(
            _rest_url(cloud_id, f"/issue/{issue_id_or_key}/attachments"),
            headers=headers,
            files={"file": (filename, file_resp.content, content_type)},
        )
        response.raise_for_status()
        data = response.json()
    att = data[0] if isinstance(data, list) and data else {}
    return AddAttachmentToIssueOutput(
        success=True,
        id=att.get("id"),
        filename=att.get("filename"),
        mime_type=att.get("mimeType"),
        size=att.get("size"),
        self_url=att.get("self"),
    )


@tool(args_schema=AddCommentToIssueInput)
@serialize_pydantic_return
async def add_comment_to_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    issue_id_or_key: str,
    comment: str | None = None,
    body: dict[str, Any] | None = None,
    visibility: dict[str, Any] | None = None,
    properties: str | None = None,
    additional_properties: dict[str, Any] | None = None,
    expand: str | None = None,
) -> AddCommentToIssueOutput:
    """Adds a new comment to an issue."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    payload: dict[str, Any] = {}
    if body is not None:
        payload["body"] = body
    elif comment is not None:
        payload["body"] = _to_adf(comment)
    if visibility is not None:
        payload["visibility"] = visibility
    if additional_properties:
        payload.update(additional_properties)
    params: dict[str, str] = {}
    if expand:
        params["expand"] = expand
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _rest_url(cloud_id, f"/issue/{issue_id_or_key}/comment"),
            headers=headers,
            json=payload,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    author_obj = data.get("author") or {}
    return AddCommentToIssueOutput(
        success=True,
        comment=CommentSummary(
            id=data.get("id"),
            self_url=data.get("self"),
            body=data.get("body"),
            author=author_obj.get("displayName"),
            created=data.get("created"),
            updated=data.get("updated"),
        ),
    )


@tool(args_schema=AddMultipleAttachmentsToIssueInput)
@serialize_pydantic_return
async def add_multiple_attachments_to_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    issue_id_or_key: str,
    files: list[str],
) -> AddMultipleAttachmentsToIssueOutput:
    """Adds multiple attachments to an issue."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["X-Atlassian-Token"] = "no-check"
    del headers["Accept"]
    all_attachments: list[dict[str, Any]] = []
    async with httpx.AsyncClient() as client:
        for file_url in files:
            file_resp = await client.get(file_url)
            file_resp.raise_for_status()
            filename = file_url.rsplit("/", 1)[-1] or "attachment"
            content_type = file_resp.headers.get("content-type", "application/octet-stream")
            response = await client.post(
                _rest_url(cloud_id, f"/issue/{issue_id_or_key}/attachments"),
                headers=headers,
                files={"file": (filename, file_resp.content, content_type)},
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                all_attachments.extend(data)
    return AddMultipleAttachmentsToIssueOutput(success=True, attachments=all_attachments)


@tool(args_schema=AddWatcherToIssueInput)
@serialize_pydantic_return
async def add_watcher_to_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    issue_id_or_key: str,
    account_id: str,
) -> AddWatcherToIssueOutput:
    """Adds a user as a watcher of an issue by passing the account ID of the user."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _rest_url(cloud_id, f"/issue/{issue_id_or_key}/watchers"),
            headers=headers,
            json=account_id,
        )
        response.raise_for_status()
    return AddWatcherToIssueOutput(success=True)


@tool(args_schema=AssignIssueInput)
@serialize_pydantic_return
async def assign_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    issue_id_or_key: str,
    account_id: str,
) -> AssignIssueOutput:
    """Assigns an issue to a user."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    async with httpx.AsyncClient() as client:
        response = await client.put(
            _rest_url(cloud_id, f"/issue/{issue_id_or_key}/assignee"),
            headers=headers,
            json={"accountId": account_id},
        )
        response.raise_for_status()
    return AssignIssueOutput(success=True)


@tool(args_schema=CheckIssuesAgainstJqlInput)
@serialize_pydantic_return
async def check_issues_against_jql(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    issue_ids: list[int],
    jqls: list[str],
) -> CheckIssuesAgainstJqlOutput:
    """Checks whether one or more issues would be returned by one or more JQL queries."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _rest_url(cloud_id, "/jql/match"),
            headers=headers,
            json={"issueIds": issue_ids, "jqls": jqls},
        )
        response.raise_for_status()
        data = response.json()
    matches = []
    for m in data.get("matches", []):
        matches.append(JqlMatchResult(
            issue_id=str(m.get("issueId", "")),
            matched_jqls=m.get("matchedJqls", []),
        ))
    return CheckIssuesAgainstJqlOutput(success=True, matches=matches)


@tool(args_schema=CountIssuesUsingJqlInput)
@serialize_pydantic_return
async def count_issues_using_jql(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    jql: str,
) -> CountIssuesUsingJqlOutput:
    """Provides an estimated count of the issues that match a JQL query."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _rest_url(cloud_id, "/search/approximate-count"),
            headers=headers,
            json={"jql": jql},
        )
        response.raise_for_status()
        data = response.json()
    return CountIssuesUsingJqlOutput(success=True, count=data.get("count"))


@tool(args_schema=CreateCustomFieldOptionsContextInput)
@serialize_pydantic_return
async def create_custom_field_options_context(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    field_id: str,
    context_id: str,
) -> CreateCustomFieldOptionsContextOutput:
    """Creates a context for custom field options."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _rest_url(cloud_id, f"/field/{field_id}/context/{context_id}/option"),
            headers=headers,
            json={},
        )
        response.raise_for_status()
        data = response.json()
    return CreateCustomFieldOptionsContextOutput(
        success=True,
        options=data.get("options", []),
    )


@tool(args_schema=CreateFutureSprintInput)
@serialize_pydantic_return
async def create_future_sprint(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    board_id: str,
    name: str,
    goal: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> CreateFutureSprintOutput:
    """Creates a future sprint."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    payload: dict[str, Any] = {"name": name, "originBoardId": int(board_id)}
    if goal is not None:
        payload["goal"] = goal
    if start_date is not None:
        payload["startDate"] = start_date
    if end_date is not None:
        payload["endDate"] = end_date
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _agile_url(cloud_id, "/sprint"),
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    return CreateFutureSprintOutput(
        success=True,
        sprint=SprintSummary(
            id=data.get("id"),
            name=data.get("name"),
            state=data.get("state"),
            start_date=data.get("startDate"),
            end_date=data.get("endDate"),
            complete_date=data.get("completeDate"),
            goal=data.get("goal"),
            self_url=data.get("self"),
        ),
    )


@tool(args_schema=CreateIssueInput)
@serialize_pydantic_return
async def create_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    project_id: str,
    issue_type_id: str,
    update_history: bool | None = None,
    history_metadata: dict[str, Any] | None = None,
    properties: str | None = None,
    update: dict[str, Any] | None = None,
    additional_properties: dict[str, Any] | None = None,
) -> CreateIssueOutput:
    """Creates an issue or, where the option to create subtasks is enabled in Jira, a subtask."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    fields_payload: dict[str, Any] = {
        "project": {"id": project_id},
        "issuetype": {"id": issue_type_id},
    }
    if additional_properties:
        for k, v in additional_properties.items():
            if isinstance(v, str) and k in ("summary",):
                fields_payload[k] = v
            elif isinstance(v, str) and k in ("description",):
                fields_payload[k] = _to_adf(v)
            else:
                fields_payload[k] = v
    payload: dict[str, Any] = {"fields": fields_payload}
    if update is not None:
        payload["update"] = update
    if history_metadata is not None:
        payload["historyMetadata"] = history_metadata
    params: dict[str, str] = {}
    if update_history is not None:
        params["updateHistory"] = str(update_history).lower()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _rest_url(cloud_id, "/issue"),
            headers=headers,
            json=payload,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    return CreateIssueOutput(
        success=True,
        id=data.get("id"),
        key=data.get("key"),
        self_url=data.get("self"),
    )


@tool(args_schema=CreateVersionInput)
@serialize_pydantic_return
async def create_version(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    project_id: str,
    name: str,
    description: str | None = None,
    archived: bool | None = None,
    start_date: str | None = None,
    release_date: str | None = None,
    expand: str | None = None,
) -> CreateVersionOutput:
    """Creates a project version."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    payload: dict[str, Any] = {"name": name, "projectId": int(project_id)}
    if description is not None:
        payload["description"] = description
    if archived is not None:
        payload["archived"] = archived
    if start_date is not None:
        payload["startDate"] = start_date
    if release_date is not None:
        payload["releaseDate"] = release_date
    params: dict[str, str] = {}
    if expand:
        params["expand"] = expand
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _rest_url(cloud_id, "/version"),
            headers=headers,
            json=payload,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    return CreateVersionOutput(
        success=True,
        version=VersionSummary(
            id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            archived=data.get("archived"),
            released=data.get("released"),
            start_date=data.get("startDate"),
            release_date=data.get("releaseDate"),
            self_url=data.get("self"),
        ),
    )


@tool(args_schema=DeleteProjectInput)
@serialize_pydantic_return
async def delete_project(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    project_id: str,
    enable_undo: bool,
) -> DeleteProjectOutput:
    """Deletes a project."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            _rest_url(cloud_id, f"/project/{project_id}"),
            headers=headers,
            params={"enableUndo": str(enable_undo).lower()},
        )
        response.raise_for_status()
    return DeleteProjectOutput(success=True)


@tool(args_schema=GetAllProjectsInput)
@serialize_pydantic_return
async def get_all_projects(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    recent: int | None = None,
    properties: str | None = None,
    expand: str | None = None,
) -> GetAllProjectsOutput:
    """Gets metadata on all projects."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if recent is not None:
        params["recent"] = recent
    if properties:
        params["properties"] = properties
    if expand:
        params["expand"] = expand
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _rest_url(cloud_id, "/project/search"),
            headers=headers,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    projects = [
        ProjectSummary(
            id=p.get("id"),
            key=p.get("key"),
            name=p.get("name"),
            project_type_key=p.get("projectTypeKey"),
            self_url=p.get("self"),
        )
        for p in data.get("values", [])
    ]
    return GetAllProjectsOutput(success=True, projects=projects, total=data.get("total"))


@tool(args_schema=GetBoardInput)
@serialize_pydantic_return
async def get_board(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    board_id: str,
) -> GetBoardOutput:
    """Returns the board for the given board ID."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _agile_url(cloud_id, f"/board/{board_id}"),
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    return GetBoardOutput(
        success=True,
        board=BoardSummary(
            id=data.get("id"),
            name=data.get("name"),
            board_type=data.get("type"),
            self_url=data.get("self"),
        ),
    )


@tool(args_schema=GetCloudIdInput)
@serialize_pydantic_return
async def get_cloud_id(
    auth_type: str,
    auth_data: dict[str, Any],
) -> GetCloudIdOutput:
    """Gets the cloud ID and details of all accessible Jira Cloud sites."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_CLOUD_API}/oauth/token/accessible-resources",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    sites = [
        CloudSite(
            id=s.get("id"),
            url=s.get("url"),
            name=s.get("name"),
            scopes=s.get("scopes", []),
            avatar_url=s.get("avatarUrl"),
        )
        for s in (data if isinstance(data, list) else [])
    ]
    return GetCloudIdOutput(success=True, sites=sites)


@tool(args_schema=GetCurrentUserInput)
@serialize_pydantic_return
async def get_current_user(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
) -> GetCurrentUserOutput:
    """Returns the authenticated Jira user's account ID, display name, email, and active status."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _rest_url(cloud_id, "/myself"),
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    return GetCurrentUserOutput(
        success=True,
        user=UserSummary(
            account_id=data.get("accountId"),
            display_name=data.get("displayName"),
            email_address=data.get("emailAddress"),
            active=data.get("active"),
            avatar_url=(data.get("avatarUrls") or {}).get("48x48"),
            account_type=data.get("accountType"),
        ),
    )


@tool(args_schema=GetIssueInput)
@serialize_pydantic_return
async def get_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    issue_id_or_key: str,
    fields: str | None = None,
    fields_by_keys: bool | None = None,
    properties: str | None = None,
    update_history: bool | None = None,
    expand: str | None = None,
) -> GetIssueOutput:
    """Gets the details for an issue."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if fields:
        params["fields"] = fields
    if fields_by_keys is not None:
        params["fieldsByKeys"] = str(fields_by_keys).lower()
    if properties:
        params["properties"] = properties
    if update_history is not None:
        params["updateHistory"] = str(update_history).lower()
    if expand:
        params["expand"] = expand
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _rest_url(cloud_id, f"/issue/{issue_id_or_key}"),
            headers=headers,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    return GetIssueOutput(success=True, issue=_parse_issue(data))


@tool(args_schema=GetIssuePickerSuggestionsInput)
@serialize_pydantic_return
async def get_issue_picker_suggestions(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    query: str | None = None,
    current_jql: str | None = None,
    current_issue_key: str | None = None,
    current_project_id: str | None = None,
    show_sub_tasks: bool | None = None,
    show_sub_task_parent: bool | None = None,
) -> GetIssuePickerSuggestionsOutput:
    """Returns lists of issues matching a query string."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if query:
        params["query"] = query
    if current_jql:
        params["currentJQL"] = current_jql
    if current_issue_key:
        params["currentIssueKey"] = current_issue_key
    if current_project_id:
        params["currentProjectId"] = current_project_id
    if show_sub_tasks is not None:
        params["showSubTasks"] = str(show_sub_tasks).lower()
    if show_sub_task_parent is not None:
        params["showSubTaskParent"] = str(show_sub_task_parent).lower()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _rest_url(cloud_id, "/issue/picker"),
            headers=headers,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    sections = []
    for section in data.get("sections", []):
        issues = [
            IssueSummary(id=str(iss.get("id", "")), key=iss.get("key"), summary=iss.get("summaryText"))
            for iss in section.get("issues", [])
        ]
        sections.append(SuggestionSection(label=section.get("label"), issues=issues))
    return GetIssuePickerSuggestionsOutput(success=True, sections=sections)


@tool(args_schema=GetIssueTypesInput)
@serialize_pydantic_return
async def get_issue_types(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    project_id: str | None = None,
) -> GetIssueTypesOutput:
    """Gets the available issue types, optionally filtered by project."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, str] = {}
    if project_id:
        params["projectId"] = project_id
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _rest_url(cloud_id, "/issuetype/project" if project_id else "/issuetype"),
            headers=headers,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    items = data if isinstance(data, list) else []
    issue_types = [
        IssueTypeSummary(
            id=it.get("id"),
            name=it.get("name"),
            description=it.get("description"),
            subtask=it.get("subtask"),
            self_url=it.get("self"),
        )
        for it in items
    ]
    return GetIssueTypesOutput(success=True, issue_types=issue_types)


@tool(args_schema=GetSprintInput)
@serialize_pydantic_return
async def get_sprint(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    sprint_id: str,
) -> GetSprintOutput:
    """Returns the sprint for a given sprint ID."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _agile_url(cloud_id, f"/sprint/{sprint_id}"),
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    return GetSprintOutput(
        success=True,
        sprint=SprintSummary(
            id=data.get("id"),
            name=data.get("name"),
            state=data.get("state"),
            start_date=data.get("startDate"),
            end_date=data.get("endDate"),
            complete_date=data.get("completeDate"),
            goal=data.get("goal"),
            self_url=data.get("self"),
        ),
    )


@tool(args_schema=GetTaskInput)
@serialize_pydantic_return
async def get_task(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    task_id: str,
) -> GetTaskOutput:
    """Gets the status of a long-running asynchronous task."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _rest_url(cloud_id, f"/task/{task_id}"),
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    return GetTaskOutput(
        success=True,
        status=data.get("status"),
        progress=data.get("progress"),
        result=data.get("result"),
        task_id=data.get("taskId"),
    )


@tool(args_schema=GetTransitionsInput)
@serialize_pydantic_return
async def get_transitions(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    issue_id_or_key: str,
    transition_id: str | None = None,
    skip_remote_only_condition: bool | None = None,
    include_unavailable_transitions: bool | None = None,
    sort_by_ops_bar_and_status: bool | None = None,
    expand: str | None = None,
) -> GetTransitionsOutput:
    """Gets either all transitions or a transition that can be performed by the user on an issue."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if transition_id:
        params["transitionId"] = transition_id
    if skip_remote_only_condition is not None:
        params["skipRemoteOnlyCondition"] = str(skip_remote_only_condition).lower()
    if include_unavailable_transitions is not None:
        params["includeUnavailableTransitions"] = str(include_unavailable_transitions).lower()
    if sort_by_ops_bar_and_status is not None:
        params["sortByOpsBarAndStatus"] = str(sort_by_ops_bar_and_status).lower()
    if expand:
        params["expand"] = expand
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _rest_url(cloud_id, f"/issue/{issue_id_or_key}/transitions"),
            headers=headers,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    transitions = [
        TransitionSummary(
            id=t.get("id"),
            name=t.get("name"),
            to_status=(t.get("to") or {}).get("name"),
            has_screen=t.get("hasScreen"),
        )
        for t in data.get("transitions", [])
    ]
    return GetTransitionsOutput(success=True, transitions=transitions)


@tool(args_schema=GetUserInput)
@serialize_pydantic_return
async def get_user(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    account_id: str,
    expand: str | None = None,
) -> GetUserOutput:
    """Gets details of a user."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"accountId": account_id}
    if expand:
        params["expand"] = expand
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _rest_url(cloud_id, "/user"),
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
    return GetUserOutput(
        success=True,
        user=UserSummary(
            account_id=data.get("accountId"),
            display_name=data.get("displayName"),
            email_address=data.get("emailAddress"),
            active=data.get("active"),
            avatar_url=(data.get("avatarUrls") or {}).get("48x48"),
            account_type=data.get("accountType"),
        ),
    )


@tool(args_schema=GetUsersInput)
@serialize_pydantic_return
async def get_users(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    query: str | None = None,
) -> GetUsersOutput:
    """Gets the details for a list of users."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, str] = {}
    if query:
        params["query"] = query
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _rest_url(cloud_id, "/user/search"),
            headers=headers,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    users = [
        UserSummary(
            account_id=u.get("accountId"),
            display_name=u.get("displayName"),
            email_address=u.get("emailAddress"),
            active=u.get("active"),
            avatar_url=(u.get("avatarUrls") or {}).get("48x48"),
            account_type=u.get("accountType"),
        )
        for u in (data if isinstance(data, list) else [])
    ]
    return GetUsersOutput(success=True, users=users)


@tool(args_schema=ListBoardIssuesInput)
@serialize_pydantic_return
async def list_board_issues(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    board_id: str,
    start_at: int | None = None,
    max_results: int | None = None,
    jql: str | None = None,
    fields: str | None = None,
    expand: str | None = None,
) -> ListBoardIssuesOutput:
    """Returns all issues from a board, for the given board ID."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if start_at is not None:
        params["startAt"] = start_at
    if max_results is not None:
        params["maxResults"] = max_results
    if jql:
        params["jql"] = jql
    if fields:
        params["fields"] = fields
    if expand:
        params["expand"] = expand
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _agile_url(cloud_id, f"/board/{board_id}/issue"),
            headers=headers,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    issues = [_parse_issue(i) for i in data.get("issues", [])]
    return ListBoardIssuesOutput(
        success=True,
        issues=issues,
        total=data.get("total"),
        start_at=data.get("startAt"),
        max_results=data.get("maxResults"),
    )


@tool(args_schema=ListBoardsInput)
@serialize_pydantic_return
async def list_boards(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    start_at: int | None = None,
    max_results: int | None = None,
    type: str | None = None,
    name: str | None = None,
    project_key_or_id: str | None = None,
) -> ListBoardsOutput:
    """Returns all boards."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if start_at is not None:
        params["startAt"] = start_at
    if max_results is not None:
        params["maxResults"] = max_results
    if type:
        params["type"] = type
    if name:
        params["name"] = name
    if project_key_or_id:
        params["projectKeyOrId"] = project_key_or_id
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _agile_url(cloud_id, "/board"),
            headers=headers,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    boards = [
        BoardSummary(
            id=b.get("id"),
            name=b.get("name"),
            board_type=b.get("type"),
            self_url=b.get("self"),
        )
        for b in data.get("values", [])
    ]
    return ListBoardsOutput(
        success=True,
        boards=boards,
        total=data.get("total"),
        start_at=data.get("startAt"),
        max_results=data.get("maxResults"),
    )


@tool(args_schema=ListEpicIssuesInput)
@serialize_pydantic_return
async def list_epic_issues(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    board_id: str,
    epic_id: str,
    start_at: int | None = None,
    max_results: int | None = None,
    jql: str | None = None,
    fields: str | None = None,
    expand: str | None = None,
) -> ListEpicIssuesOutput:
    """Returns all issues that belong to an epic on the given board."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if start_at is not None:
        params["startAt"] = start_at
    if max_results is not None:
        params["maxResults"] = max_results
    if jql:
        params["jql"] = jql
    if fields:
        params["fields"] = fields
    if expand:
        params["expand"] = expand
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _agile_url(cloud_id, f"/board/{board_id}/epic/{epic_id}/issue"),
            headers=headers,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    issues = [_parse_issue(i) for i in data.get("issues", [])]
    return ListEpicIssuesOutput(
        success=True,
        issues=issues,
        total=data.get("total"),
        start_at=data.get("startAt"),
        max_results=data.get("maxResults"),
    )


@tool(args_schema=ListEpicsInput)
@serialize_pydantic_return
async def list_epics(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    board_id: str,
    start_at: int | None = None,
    max_results: int | None = None,
    done: bool | None = None,
) -> ListEpicsOutput:
    """Returns all epics from a board, for the given board ID."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if start_at is not None:
        params["startAt"] = start_at
    if max_results is not None:
        params["maxResults"] = max_results
    if done is not None:
        params["done"] = str(done).lower()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _agile_url(cloud_id, f"/board/{board_id}/epic"),
            headers=headers,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    epics = [
        EpicSummary(
            id=e.get("id"),
            key=e.get("key"),
            name=e.get("name"),
            summary=e.get("summary"),
            done=e.get("done"),
            self_url=e.get("self"),
        )
        for e in data.get("values", [])
    ]
    return ListEpicsOutput(
        success=True,
        epics=epics,
        total=data.get("total"),
        start_at=data.get("startAt"),
        max_results=data.get("maxResults"),
    )


@tool(args_schema=ListIssueCommentsInput)
@serialize_pydantic_return
async def list_issue_comments(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    issue_id_or_key: str,
    order_by: str | None = None,
    expand: str | None = None,
) -> ListIssueCommentsOutput:
    """Lists all comments for an issue."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, str] = {}
    if order_by:
        params["orderBy"] = order_by
    if expand:
        params["expand"] = expand
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _rest_url(cloud_id, f"/issue/{issue_id_or_key}/comment"),
            headers=headers,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    comments = [
        CommentSummary(
            id=c.get("id"),
            self_url=c.get("self"),
            body=c.get("body"),
            author=(c.get("author") or {}).get("displayName"),
            created=c.get("created"),
            updated=c.get("updated"),
        )
        for c in data.get("comments", [])
    ]
    return ListIssueCommentsOutput(
        success=True,
        comments=comments,
        total=data.get("total"),
        start_at=data.get("startAt"),
        max_results=data.get("maxResults"),
    )


@tool(args_schema=ListLabelsOptionsInput)
@serialize_pydantic_return
async def list_labels_options(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
) -> ListLabelsOptionsOutput:
    """Retrieves available options for the Labels field."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _rest_url(cloud_id, "/label"),
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    labels = data.get("values", []) if isinstance(data, dict) else data if isinstance(data, list) else []
    return ListLabelsOptionsOutput(
        success=True,
        labels=labels,
        total=data.get("total") if isinstance(data, dict) else len(labels),
    )


@tool(args_schema=ListSprintIssuesInput)
@serialize_pydantic_return
async def list_sprint_issues(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    sprint_id: str,
    start_at: int | None = None,
    max_results: int | None = None,
    jql: str | None = None,
    fields: str | None = None,
    expand: str | None = None,
) -> ListSprintIssuesOutput:
    """Returns all issues in a sprint."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if start_at is not None:
        params["startAt"] = start_at
    if max_results is not None:
        params["maxResults"] = max_results
    if jql:
        params["jql"] = jql
    if fields:
        params["fields"] = fields
    if expand:
        params["expand"] = expand
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _agile_url(cloud_id, f"/sprint/{sprint_id}/issue"),
            headers=headers,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    issues = [_parse_issue(i) for i in data.get("issues", [])]
    return ListSprintIssuesOutput(
        success=True,
        issues=issues,
        total=data.get("total"),
        start_at=data.get("startAt"),
        max_results=data.get("maxResults"),
    )


@tool(args_schema=ListSprintsInput)
@serialize_pydantic_return
async def list_sprints(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    board_id: str,
    start_at: int | None = None,
    max_results: int | None = None,
    state: str | None = None,
) -> ListSprintsOutput:
    """Returns all sprints from a board, for the given board ID."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if start_at is not None:
        params["startAt"] = start_at
    if max_results is not None:
        params["maxResults"] = max_results
    if state:
        params["state"] = state
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _agile_url(cloud_id, f"/board/{board_id}/sprint"),
            headers=headers,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    sprints = [
        SprintSummary(
            id=s.get("id"),
            name=s.get("name"),
            state=s.get("state"),
            start_date=s.get("startDate"),
            end_date=s.get("endDate"),
            complete_date=s.get("completeDate"),
            goal=s.get("goal"),
            self_url=s.get("self"),
        )
        for s in data.get("values", [])
    ]
    return ListSprintsOutput(
        success=True,
        sprints=sprints,
        total=data.get("total"),
        start_at=data.get("startAt"),
        max_results=data.get("maxResults"),
    )


@tool(args_schema=MoveIssuesToSprintInput)
@serialize_pydantic_return
async def move_issues_to_sprint(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    sprint_id: str,
    issues: list[str],
) -> MoveIssuesToSprintOutput:
    """Moves issues to a sprint, for a given sprint ID."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _agile_url(cloud_id, f"/sprint/{sprint_id}/issue"),
            headers=headers,
            json={"issues": issues},
        )
        response.raise_for_status()
    return MoveIssuesToSprintOutput(success=True)


@tool(args_schema=SearchIssuesWithJqlInput)
@serialize_pydantic_return
async def search_issues_with_jql(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    jql: str,
    max_results: int | None = None,
    fields: str | None = None,
    expand: list[str] | None = None,
    properties: str | None = None,
    fields_by_keys: bool | None = None,
    fail_fast: bool | None = None,
) -> SearchIssuesWithJqlOutput:
    """Search for issues using JQL (Jira Query Language) via GET."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"jql": jql}
    if max_results is not None:
        params["maxResults"] = max_results
    if fields:
        params["fields"] = fields
    if expand:
        params["expand"] = ",".join(expand)
    if properties:
        params["properties"] = properties
    if fields_by_keys is not None:
        params["fieldsByKeys"] = str(fields_by_keys).lower()
    if fail_fast is not None:
        params["failFast"] = str(fail_fast).lower()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _rest_url(cloud_id, "/search/jql"),
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
    issues = [_parse_issue(i) for i in data.get("issues", [])]
    return SearchIssuesWithJqlOutput(
        success=True,
        issues=issues,
        total=data.get("total"),
        start_at=data.get("startAt"),
        max_results=data.get("maxResults"),
    )


@tool(args_schema=SearchIssuesWithJqlPostInput)
@serialize_pydantic_return
async def search_issues_with_jql_post(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    jql: str,
    max_results: int | None = None,
    next_page_token: str | None = None,
    fields: list[str] | None = None,
    expand: list[str] | None = None,
    properties: list[str] | None = None,
    fields_by_keys: bool | None = None,
    reconcile_issues: list[str] | None = None,
) -> SearchIssuesWithJqlPostOutput:
    """Searches for issues using JQL with enhanced search capabilities via POST."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    payload: dict[str, Any] = {"jql": jql}
    if max_results is not None:
        payload["maxResults"] = max_results
    if next_page_token:
        payload["nextPageToken"] = next_page_token
    if fields:
        payload["fields"] = fields
    if expand:
        payload["expand"] = expand
    if properties:
        payload["properties"] = properties
    if fields_by_keys is not None:
        payload["fieldsByKeys"] = fields_by_keys
    if reconcile_issues:
        payload["reconcileIssues"] = reconcile_issues
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _rest_url(cloud_id, "/search/jql"),
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    issues = [_parse_issue(i) for i in data.get("issues", [])]
    return SearchIssuesWithJqlPostOutput(
        success=True,
        issues=issues,
        total=data.get("total"),
        next_page_token=data.get("nextPageToken"),
    )


@tool(args_schema=TransitionIssueInput)
@serialize_pydantic_return
async def transition_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    issue_id_or_key: str,
    transition: str,
    fields: dict[str, Any] | None = None,
    update: dict[str, Any] | None = None,
    history_metadata: dict[str, Any] | None = None,
    properties: str | None = None,
    additional_properties: dict[str, Any] | None = None,
) -> TransitionIssueOutput:
    """Performs an issue transition and optionally updates the fields of the screen."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    payload: dict[str, Any] = {"transition": {"id": transition}}
    if fields is not None:
        payload["fields"] = fields
    if update is not None:
        payload["update"] = update
    if history_metadata is not None:
        payload["historyMetadata"] = history_metadata
    if additional_properties:
        payload.update(additional_properties)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _rest_url(cloud_id, f"/issue/{issue_id_or_key}/transitions"),
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
    return TransitionIssueOutput(success=True)


@tool(args_schema=UpdateCommentInput)
@serialize_pydantic_return
async def update_comment(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    issue_id_or_key: str,
    comment_id: str,
    body: dict[str, Any] | None = None,
    comment: str | None = None,
    visibility: dict[str, Any] | None = None,
    properties: str | None = None,
    additional_properties: dict[str, Any] | None = None,
    notify_users: bool | None = None,
    expand: str | None = None,
) -> UpdateCommentOutput:
    """Updates a comment."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    payload: dict[str, Any] = {}
    if body is not None:
        payload["body"] = body
    elif comment is not None:
        payload["body"] = _to_adf(comment)
    if visibility is not None:
        payload["visibility"] = visibility
    if additional_properties:
        payload.update(additional_properties)
    params: dict[str, str] = {}
    if notify_users is not None:
        params["notifyUsers"] = str(notify_users).lower()
    if expand:
        params["expand"] = expand
    async with httpx.AsyncClient() as client:
        response = await client.put(
            _rest_url(cloud_id, f"/issue/{issue_id_or_key}/comment/{comment_id}"),
            headers=headers,
            json=payload,
            params=params or None,
        )
        response.raise_for_status()
        data = response.json()
    author_obj = data.get("author") or {}
    return UpdateCommentOutput(
        success=True,
        comment=CommentSummary(
            id=data.get("id"),
            self_url=data.get("self"),
            body=data.get("body"),
            author=author_obj.get("displayName"),
            created=data.get("created"),
            updated=data.get("updated"),
        ),
    )


@tool(args_schema=UpdateIssueInput)
@serialize_pydantic_return
async def update_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    cloud_id: str,
    project_id: str,
    issue_id_or_key: str,
    issue_type_id: str | None = None,
    notify_users: bool | None = None,
    override_screen_security: bool | None = None,
    override_editable_flag: bool | None = None,
    transition_id: str | None = None,
    transition_looped: bool | None = None,
    history_metadata: dict[str, Any] | None = None,
    properties: str | None = None,
    update: dict[str, Any] | None = None,
    additional_properties: dict[str, Any] | None = None,
) -> UpdateIssueOutput:
    """Updates an issue. A transition may be applied and issue properties updated as part of the update."""
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    fields_payload: dict[str, Any] = {
        "project": {"id": project_id},
    }
    if issue_type_id is not None:
        fields_payload["issuetype"] = {"id": issue_type_id}
    if additional_properties:
        for k, v in additional_properties.items():
            if isinstance(v, str) and k in ("description",):
                fields_payload[k] = _to_adf(v)
            else:
                fields_payload[k] = v
    payload: dict[str, Any] = {"fields": fields_payload}
    if update is not None:
        payload["update"] = update
    if history_metadata is not None:
        payload["historyMetadata"] = history_metadata
    if transition_id is not None:
        transition_obj: dict[str, Any] = {"id": transition_id}
        if transition_looped is not None:
            transition_obj["looped"] = transition_looped
        payload["transition"] = transition_obj
    params: dict[str, str] = {}
    if notify_users is not None:
        params["notifyUsers"] = str(notify_users).lower()
    if override_screen_security is not None:
        params["overrideScreenSecurity"] = str(override_screen_security).lower()
    if override_editable_flag is not None:
        params["overrideEditableFlag"] = str(override_editable_flag).lower()
    async with httpx.AsyncClient() as client:
        response = await client.put(
            _rest_url(cloud_id, f"/issue/{issue_id_or_key}"),
            headers=headers,
            json=payload,
            params=params or None,
        )
        response.raise_for_status()
    return UpdateIssueOutput(success=True)
