"""Jira integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="jira",
    display_name="Jira",
    description="Atlassian Jira Cloud project tracking and issue management platform",
    version="1.0.0",
    author="ModuleX",
    logo="logos:jira",
    app_url="https://www.atlassian.com/software/jira",
    categories=["Project Management", "Developer Tools & Infrastructure", "Productivity & Collaboration"],
    actions=[
        ActionDefinition(
            name="add_attachment_to_issue",
            description="Adds an attachment to an issue",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "issue_id_or_key": ParameterDef(
                    type="string",
                    description="The ID or key of the issue",
                    required=True,
                ),
                "file": ParameterDef(
                    type="string",
                    description="A file URL to attach to the issue",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="add_comment_to_issue",
            description="Adds a new comment to an issue",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "issue_id_or_key": ParameterDef(
                    type="string",
                    description="The ID or key of the issue",
                    required=True,
                ),
                "comment": ParameterDef(
                    type="string",
                    description="The comment text in plain text (converted to Atlassian Document Format)",
                ),
                "body": ParameterDef(
                    type="object",
                    description="The comment text in Atlassian Document Format (JSON object). Overrides comment if both provided",
                ),
                "visibility": ParameterDef(
                    type="object",
                    description="The group or role to which this comment is visible",
                ),
                "properties": ParameterDef(
                    type="string",
                    description="A JSON array of comment properties",
                ),
                "additional_properties": ParameterDef(
                    type="object",
                    description="Extra properties of any type to include",
                ),
                "expand": ParameterDef(
                    type="string",
                    description="Use 'renderedBody' to get comment body rendered in HTML",
                ),
            },
        ),
        ActionDefinition(
            name="add_multiple_attachments_to_issue",
            description="Adds multiple attachments to an issue",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "issue_id_or_key": ParameterDef(
                    type="string",
                    description="The ID or key of the issue",
                    required=True,
                ),
                "files": ParameterDef(
                    type="array",
                    description="An array of file URLs to attach to the issue. Each element is a string URL",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="add_watcher_to_issue",
            description="Adds a user as a watcher of an issue by passing the account ID of the user",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "issue_id_or_key": ParameterDef(
                    type="string",
                    description="The ID or key of the issue",
                    required=True,
                ),
                "account_id": ParameterDef(
                    type="string",
                    description="The account ID of the user to add as watcher",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="assign_issue",
            description="Assigns an issue to a user",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "issue_id_or_key": ParameterDef(
                    type="string",
                    description="The ID or key of the issue",
                    required=True,
                ),
                "account_id": ParameterDef(
                    type="string",
                    description="The account ID of the user to assign",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="check_issues_against_jql",
            description="Checks whether one or more issues would be returned by one or more JQL queries",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "issue_ids": ParameterDef(
                    type="array",
                    description="A list of issue IDs to check against the JQL queries. Elements are integers",
                    required=True,
                ),
                "jqls": ParameterDef(
                    type="array",
                    description="A list of JQL query strings to check the issues against",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="count_issues_using_jql",
            description="Provides an estimated count of the issues that match a JQL query",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "jql": ParameterDef(
                    type="string",
                    description="The JQL query to count issues. Must be bounded (e.g. project = ABC)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_custom_field_options_context",
            description="Creates a context for custom field options",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "field_id": ParameterDef(
                    type="string",
                    description="The ID of the custom field",
                    required=True,
                ),
                "context_id": ParameterDef(
                    type="string",
                    description="The ID of the field context",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_future_sprint",
            description="Creates a future sprint",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board the sprint will be created on",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="The name of the sprint",
                    required=True,
                ),
                "goal": ParameterDef(
                    type="string",
                    description="The goal of the sprint",
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="The start date in ISO 8601 format (e.g. 2024-01-01T00:00:00.000Z)",
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="The end date in ISO 8601 format (e.g. 2024-01-15T00:00:00.000Z)",
                ),
            },
        ),
        ActionDefinition(
            name="create_issue",
            description="Creates an issue or, where the option to create subtasks is enabled in Jira, a subtask",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "project_id": ParameterDef(
                    type="string",
                    description="The project ID",
                    required=True,
                ),
                "issue_type_id": ParameterDef(
                    type="string",
                    description="The issue type ID",
                    required=True,
                ),
                "update_history": ParameterDef(
                    type="boolean",
                    description="Whether the project is added to the user's Recently viewed project list",
                ),
                "history_metadata": ParameterDef(
                    type="object",
                    description="Additional issue history details",
                ),
                "properties": ParameterDef(
                    type="string",
                    description="Details of issue properties to add or update (JSON array)",
                ),
                "update": ParameterDef(
                    type="object",
                    description="A map of field name to operations list for issue screen fields",
                ),
                "additional_properties": ParameterDef(
                    type="object",
                    description="Extra fields to include in the issue body (e.g. summary, description, labels, priority)",
                ),
            },
        ),
        ActionDefinition(
            name="create_version",
            description="Creates a project version",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "project_id": ParameterDef(
                    type="string",
                    description="The project ID",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="The unique name of the version. Max 255 characters",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="The description of the version",
                ),
                "archived": ParameterDef(
                    type="boolean",
                    description="Indicates that the version is archived",
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="The start date (yyyy-mm-dd)",
                ),
                "release_date": ParameterDef(
                    type="string",
                    description="The release date (yyyy-mm-dd)",
                ),
                "expand": ParameterDef(
                    type="string",
                    description="Expand options: operations, issuesstatus",
                ),
            },
        ),
        ActionDefinition(
            name="delete_project",
            description="Deletes a project",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "project_id": ParameterDef(
                    type="string",
                    description="The project ID or key",
                    required=True,
                ),
                "enable_undo": ParameterDef(
                    type="boolean",
                    description="Whether this project is placed in the Jira recycle bin for recovery",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_all_projects",
            description="Gets metadata on all projects",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "recent": ParameterDef(
                    type="integer",
                    description="Returns the user's most recently accessed projects (max 20)",
                ),
                "properties": ParameterDef(
                    type="string",
                    description="Issue properties to include (JSON array)",
                ),
                "expand": ParameterDef(
                    type="string",
                    description="Expand options: description, issueTypes, lead, projectKeys",
                ),
            },
        ),
        ActionDefinition(
            name="get_board",
            description="Returns the board for the given board ID",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_cloud_id",
            description="Gets the cloud ID and details of all accessible Jira Cloud sites",
            parameters={},
        ),
        ActionDefinition(
            name="get_current_user",
            description="Returns the authenticated Jira user's account ID, display name, email, and active status",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_issue",
            description="Gets the details for an issue",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "issue_id_or_key": ParameterDef(
                    type="string",
                    description="The ID or key of the issue",
                    required=True,
                ),
                "fields": ParameterDef(
                    type="string",
                    description="Comma-separated list of fields to return. *all or *navigable for all or navigable fields",
                ),
                "fields_by_keys": ParameterDef(
                    type="boolean",
                    description="Whether fields are referenced by keys rather than IDs",
                ),
                "properties": ParameterDef(
                    type="string",
                    description="Issue properties to include (comma-separated or *all)",
                ),
                "update_history": ParameterDef(
                    type="boolean",
                    description="Whether project is added to Recently viewed",
                ),
                "expand": ParameterDef(
                    type="string",
                    description="Expand options: renderedFields, names, schema, transitions, editmeta, changelog, versionedRepresentations",
                ),
            },
        ),
        ActionDefinition(
            name="get_issue_picker_suggestions",
            description="Returns lists of issues matching a query string",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="A string to match against issue text fields",
                ),
                "current_jql": ParameterDef(
                    type="string",
                    description="A JQL query defining a list of issues to search within",
                ),
                "current_issue_key": ParameterDef(
                    type="string",
                    description="The key of an issue to exclude from results",
                ),
                "current_project_id": ParameterDef(
                    type="string",
                    description="The ID of a project that results must belong to",
                ),
                "show_sub_tasks": ParameterDef(
                    type="boolean",
                    description="Whether to include subtasks in suggestions",
                ),
                "show_sub_task_parent": ParameterDef(
                    type="boolean",
                    description="Whether to include the parent issue when currentIssueKey is a subtask",
                ),
            },
        ),
        ActionDefinition(
            name="get_issue_types",
            description="Gets the available issue types, optionally filtered by project",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "project_id": ParameterDef(
                    type="string",
                    description="The project ID to filter issue types",
                ),
            },
        ),
        ActionDefinition(
            name="get_sprint",
            description="Returns the sprint for a given sprint ID",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "sprint_id": ParameterDef(
                    type="string",
                    description="The ID of the sprint",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_task",
            description="Gets the status of a long-running asynchronous task",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "task_id": ParameterDef(
                    type="string",
                    description="The ID of the long-running async task",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_transitions",
            description="Gets either all transitions or a transition that can be performed by the user on an issue",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "issue_id_or_key": ParameterDef(
                    type="string",
                    description="The ID or key of the issue",
                    required=True,
                ),
                "transition_id": ParameterDef(
                    type="string",
                    description="The ID of a specific transition to retrieve",
                ),
                "skip_remote_only_condition": ParameterDef(
                    type="boolean",
                    description="Whether transitions with Hide From User Condition are included",
                ),
                "include_unavailable_transitions": ParameterDef(
                    type="boolean",
                    description="Whether details of failing-condition transitions are included",
                ),
                "sort_by_ops_bar_and_status": ParameterDef(
                    type="boolean",
                    description="Whether transitions are sorted by ops-bar sequence then category",
                ),
                "expand": ParameterDef(
                    type="string",
                    description="Expand options: transitions.fields",
                ),
            },
        ),
        ActionDefinition(
            name="get_user",
            description="Gets details of a user",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "account_id": ParameterDef(
                    type="string",
                    description="The account ID of the user",
                    required=True,
                ),
                "expand": ParameterDef(
                    type="string",
                    description="Expand options: groups, applicationRoles",
                ),
            },
        ),
        ActionDefinition(
            name="get_users",
            description="Gets the details for a list of users",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="Filter for a name or term",
                ),
            },
        ),
        ActionDefinition(
            name="list_board_issues",
            description="Returns all issues from a board, for the given board ID",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board",
                    required=True,
                ),
                "start_at": ParameterDef(
                    type="integer",
                    description="The starting index of the returned issues. Base index: 0",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="The maximum number of issues to return",
                ),
                "jql": ParameterDef(
                    type="string",
                    description="Filters results using a JQL query",
                ),
                "fields": ParameterDef(
                    type="string",
                    description="Comma-separated list of fields to return per issue",
                ),
                "expand": ParameterDef(
                    type="string",
                    description="Expand options for additional information",
                ),
            },
        ),
        ActionDefinition(
            name="list_boards",
            description="Returns all boards",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "start_at": ParameterDef(
                    type="integer",
                    description="The starting index of the returned boards. Base index: 0",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="The maximum number of boards to return",
                ),
                "type": ParameterDef(
                    type="string",
                    description="Filters by board type: scrum, kanban, simple",
                ),
                "name": ParameterDef(
                    type="string",
                    description="Filters results to boards matching this name",
                ),
                "project_key_or_id": ParameterDef(
                    type="string",
                    description="Filters results to boards relevant to a project",
                ),
            },
        ),
        ActionDefinition(
            name="list_epic_issues",
            description="Returns all issues that belong to an epic on the given board",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board",
                    required=True,
                ),
                "epic_id": ParameterDef(
                    type="string",
                    description="The ID of the epic",
                    required=True,
                ),
                "start_at": ParameterDef(
                    type="integer",
                    description="The starting index of the returned issues. Base index: 0",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="The maximum number of issues to return",
                ),
                "jql": ParameterDef(
                    type="string",
                    description="Filters results using a JQL query",
                ),
                "fields": ParameterDef(
                    type="string",
                    description="Comma-separated list of fields to return per issue",
                ),
                "expand": ParameterDef(
                    type="string",
                    description="Expand options for additional information",
                ),
            },
        ),
        ActionDefinition(
            name="list_epics",
            description="Returns all epics from a board, for the given board ID",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board",
                    required=True,
                ),
                "start_at": ParameterDef(
                    type="integer",
                    description="The starting index of the returned epics. Base index: 0",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="The maximum number of epics to return",
                ),
                "done": ParameterDef(
                    type="boolean",
                    description="Filter to epics that are done or not done",
                ),
            },
        ),
        ActionDefinition(
            name="list_issue_comments",
            description="Lists all comments for an issue",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "issue_id_or_key": ParameterDef(
                    type="string",
                    description="The ID or key of the issue",
                    required=True,
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Order results by a field. Valid: created, +created, -created",
                ),
                "expand": ParameterDef(
                    type="string",
                    description="Expand options: renderedBody",
                ),
            },
        ),
        ActionDefinition(
            name="list_labels_options",
            description="Retrieves available options for the Labels field",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_sprint_issues",
            description="Returns all issues in a sprint",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "sprint_id": ParameterDef(
                    type="string",
                    description="The ID of the sprint",
                    required=True,
                ),
                "start_at": ParameterDef(
                    type="integer",
                    description="The starting index of the returned issues. Base index: 0",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="The maximum number of issues to return",
                ),
                "jql": ParameterDef(
                    type="string",
                    description="Filters results using a JQL query",
                ),
                "fields": ParameterDef(
                    type="string",
                    description="Comma-separated list of fields to return per issue",
                ),
                "expand": ParameterDef(
                    type="string",
                    description="Expand options for additional information",
                ),
            },
        ),
        ActionDefinition(
            name="list_sprints",
            description="Returns all sprints from a board, for the given board ID",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board",
                    required=True,
                ),
                "start_at": ParameterDef(
                    type="integer",
                    description="The starting index of the returned sprints. Base index: 0",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="The maximum number of sprints to return",
                ),
                "state": ParameterDef(
                    type="string",
                    description="Filter by sprint states: future, active, closed (comma-separated)",
                ),
            },
        ),
        ActionDefinition(
            name="move_issues_to_sprint",
            description="Moves issues to a sprint, for a given sprint ID",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "sprint_id": ParameterDef(
                    type="string",
                    description="The ID of the sprint",
                    required=True,
                ),
                "issues": ParameterDef(
                    type="array",
                    description="The IDs or keys of the issues to move to the sprint. Each element is a string",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_issues_with_jql",
            description="Search for issues using JQL (Jira Query Language) via GET",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "jql": ParameterDef(
                    type="string",
                    description="The JQL query to search for issues",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of issues to return (default 50, max 5000)",
                ),
                "fields": ParameterDef(
                    type="string",
                    description="Comma-separated list of fields to return",
                ),
                "expand": ParameterDef(
                    type="array",
                    description="Expand options: renderedFields, names, schema, transitions, editmeta, changelog, versionedRepresentations",
                ),
                "properties": ParameterDef(
                    type="string",
                    description="Comma-separated list of issue properties to include (max 5)",
                ),
                "fields_by_keys": ParameterDef(
                    type="boolean",
                    description="Reference fields by key rather than ID",
                ),
                "fail_fast": ParameterDef(
                    type="boolean",
                    description="Fail early if not all field data can be retrieved",
                ),
            },
        ),
        ActionDefinition(
            name="search_issues_with_jql_post",
            description="Searches for issues using JQL with enhanced search capabilities via POST",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "jql": ParameterDef(
                    type="string",
                    description="The JQL query to search for issues",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of items per page",
                ),
                "next_page_token": ParameterDef(
                    type="string",
                    description="Token for pagination from a previous response",
                ),
                "fields": ParameterDef(
                    type="array",
                    description="Fields to return per issue. Elements are strings. Example: ['summary', 'status']",
                ),
                "expand": ParameterDef(
                    type="array",
                    description="Expand options: renderedFields, names, schema, transitions, editmeta, changelog, versionedRepresentations",
                ),
                "properties": ParameterDef(
                    type="array",
                    description="Issue property keys to include (max 5). Elements are strings",
                ),
                "fields_by_keys": ParameterDef(
                    type="boolean",
                    description="Reference fields by key rather than ID",
                ),
                "reconcile_issues": ParameterDef(
                    type="array",
                    description="Issue IDs/keys for read-after-write consistency. Elements are strings",
                ),
            },
        ),
        ActionDefinition(
            name="transition_issue",
            description="Performs an issue transition and optionally updates the fields of the screen",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "issue_id_or_key": ParameterDef(
                    type="string",
                    description="The ID or key of the issue",
                    required=True,
                ),
                "transition": ParameterDef(
                    type="string",
                    description="The transition ID to perform",
                    required=True,
                ),
                "fields": ParameterDef(
                    type="object",
                    description="List of issue screen fields to update during transition",
                ),
                "update": ParameterDef(
                    type="object",
                    description="Operations to perform on issue screen fields",
                ),
                "history_metadata": ParameterDef(
                    type="object",
                    description="Additional issue history details",
                ),
                "properties": ParameterDef(
                    type="string",
                    description="Issue properties to add or update (JSON)",
                ),
                "additional_properties": ParameterDef(
                    type="object",
                    description="Extra properties of any type",
                ),
            },
        ),
        ActionDefinition(
            name="update_comment",
            description="Updates a comment",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "issue_id_or_key": ParameterDef(
                    type="string",
                    description="The ID or key of the issue",
                    required=True,
                ),
                "comment_id": ParameterDef(
                    type="string",
                    description="The ID of the comment to update",
                    required=True,
                ),
                "body": ParameterDef(
                    type="object",
                    description="The comment text in Atlassian Document Format (JSON). Overrides comment if both provided",
                ),
                "comment": ParameterDef(
                    type="string",
                    description="The comment text (plain text)",
                ),
                "visibility": ParameterDef(
                    type="object",
                    description="The group or role to which this comment is visible",
                ),
                "properties": ParameterDef(
                    type="string",
                    description="Comment properties (JSON array)",
                ),
                "additional_properties": ParameterDef(
                    type="object",
                    description="Extra properties of any type",
                ),
                "notify_users": ParameterDef(
                    type="boolean",
                    description="Whether users are notified when comment is updated",
                ),
                "expand": ParameterDef(
                    type="string",
                    description="Expand options: renderedBody",
                ),
            },
        ),
        ActionDefinition(
            name="update_issue",
            description="Updates an issue. A transition may be applied and issue properties updated as part of the update",
            parameters={
                "cloud_id": ParameterDef(
                    type="string",
                    description="The cloud ID of the Jira site",
                    required=True,
                ),
                "project_id": ParameterDef(
                    type="string",
                    description="The project ID",
                    required=True,
                ),
                "issue_id_or_key": ParameterDef(
                    type="string",
                    description="The ID or key of the issue",
                    required=True,
                ),
                "issue_type_id": ParameterDef(
                    type="string",
                    description="The issue type ID",
                ),
                "notify_users": ParameterDef(
                    type="boolean",
                    description="Whether a notification email is sent to watchers",
                ),
                "override_screen_security": ParameterDef(
                    type="boolean",
                    description="Override screen security to enable hidden fields",
                ),
                "override_editable_flag": ParameterDef(
                    type="boolean",
                    description="Override editable flag to enable uneditable fields",
                ),
                "transition_id": ParameterDef(
                    type="string",
                    description="The ID of the transition to undertake",
                ),
                "transition_looped": ParameterDef(
                    type="boolean",
                    description="Whether the transition is looped",
                ),
                "history_metadata": ParameterDef(
                    type="object",
                    description="Additional issue history details",
                ),
                "properties": ParameterDef(
                    type="string",
                    description="Issue properties to add or update (JSON array)",
                ),
                "update": ParameterDef(
                    type="object",
                    description="A map of field name to operations list",
                ),
                "additional_properties": ParameterDef(
                    type="object",
                    description="Extra fields to update (e.g. summary, description)",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Atlassian OAuth2 (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="JIRA_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Atlassian OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://developer.atlassian.com/console/myapps/",
                ),
                EnvVar(
                    name="JIRA_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Atlassian OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://developer.atlassian.com/console/myapps/",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://auth.atlassian.com/authorize",
                token_url="https://auth.atlassian.com/oauth/token",
                scopes=[
                    "read:jira-work",
                    "write:jira-work",
                    "read:jira-user",
                    "manage:jira-project",
                    "manage:jira-configuration",
                    "offline_access",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.atlassian.com/oauth/token/accessible-resources",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="free",
                description="Validates OAuth token by listing accessible Jira sites",
            ),
        ),
    ],
)
