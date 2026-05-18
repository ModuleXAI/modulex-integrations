# Jira

Atlassian Jira Cloud project tracking and issue management integration
against the Jira REST API v3 (`api.atlassian.com/ex/jira/{cloudId}/rest/api/3`)
and Jira Agile API (`api.atlassian.com/ex/jira/{cloudId}/rest/agile/1.0`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth 2.0 app at <https://developer.atlassian.com/console/myapps/>.
- Required scopes: `read:jira-work`, `write:jira-work`, `read:jira-user`, `manage:jira-project`, `manage:jira-configuration`, `offline_access`.
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`.
- Required env vars (custom OAuth app only):
  - `JIRA_OAUTH2_CLIENT_ID` — Atlassian OAuth App Client ID
  - `JIRA_OAUTH2_CLIENT_SECRET` — Atlassian OAuth App Client Secret

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_attachment_to_issue` | Adds an attachment to an issue | `cloud_id`, `issue_id_or_key`, `file` |
| `add_comment_to_issue` | Adds a new comment to an issue | `cloud_id`, `issue_id_or_key` |
| `add_multiple_attachments_to_issue` | Adds multiple attachments to an issue | `cloud_id`, `issue_id_or_key`, `files` |
| `add_watcher_to_issue` | Adds a user as a watcher of an issue | `cloud_id`, `issue_id_or_key`, `account_id` |
| `assign_issue` | Assigns an issue to a user | `cloud_id`, `issue_id_or_key`, `account_id` |
| `check_issues_against_jql` | Checks whether issues match JQL queries | `cloud_id`, `issue_ids`, `jqls` |
| `count_issues_using_jql` | Estimated count of issues matching a JQL query | `cloud_id`, `jql` |
| `create_custom_field_options_context` | Creates a context for custom field options | `cloud_id`, `field_id`, `context_id` |
| `create_future_sprint` | Creates a future sprint | `cloud_id`, `board_id`, `name` |
| `create_issue` | Creates an issue or subtask | `cloud_id`, `project_id`, `issue_type_id` |
| `create_version` | Creates a project version | `cloud_id`, `project_id`, `name` |
| `delete_project` | Deletes a project | `cloud_id`, `project_id`, `enable_undo` |
| `get_all_projects` | Gets metadata on all projects | `cloud_id` |
| `get_board` | Returns a board by ID | `cloud_id`, `board_id` |
| `get_cloud_id` | Gets accessible Jira Cloud sites | _(none)_ |
| `get_current_user` | Returns the authenticated user | `cloud_id` |
| `get_issue` | Gets details for an issue | `cloud_id`, `issue_id_or_key` |
| `get_issue_picker_suggestions` | Returns issues matching a query string | `cloud_id` |
| `get_issue_types` | Gets available issue types | `cloud_id` |
| `get_sprint` | Returns a sprint by ID | `cloud_id`, `sprint_id` |
| `get_task` | Gets status of a long-running task | `cloud_id`, `task_id` |
| `get_transitions` | Gets transitions for an issue | `cloud_id`, `issue_id_or_key` |
| `get_user` | Gets details of a user | `cloud_id`, `account_id` |
| `get_users` | Searches for users | `cloud_id` |
| `list_board_issues` | Returns issues from a board | `cloud_id`, `board_id` |
| `list_boards` | Returns all boards | `cloud_id` |
| `list_epic_issues` | Returns issues in an epic on a board | `cloud_id`, `board_id`, `epic_id` |
| `list_epics` | Returns epics from a board | `cloud_id`, `board_id` |
| `list_issue_comments` | Lists comments for an issue | `cloud_id`, `issue_id_or_key` |
| `list_labels_options` | Retrieves available label options | `cloud_id` |
| `list_sprint_issues` | Returns issues in a sprint | `cloud_id`, `sprint_id` |
| `list_sprints` | Returns sprints from a board | `cloud_id`, `board_id` |
| `move_issues_to_sprint` | Moves issues to a sprint | `cloud_id`, `sprint_id`, `issues` |
| `search_issues_with_jql` | Search issues using JQL via GET | `cloud_id`, `jql` |
| `search_issues_with_jql_post` | Search issues using JQL via POST | `cloud_id`, `jql` |
| `transition_issue` | Performs an issue transition | `cloud_id`, `issue_id_or_key`, `transition` |
| `update_comment` | Updates a comment | `cloud_id`, `issue_id_or_key`, `comment_id` |
| `update_issue` | Updates an issue | `cloud_id`, `project_id`, `issue_id_or_key` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved OAuth2 credential.

## Limits & Quotas

- **Standard rate limit**: Jira Cloud REST API allows approximately 100 requests per 10 seconds per user per app.
- **Concurrent requests**: Maximum 10 concurrent requests per user per app.
- **Search (JQL)**: Maximum 5000 results per search request.
- **Attachments**: Maximum 10 MB per file (default; configurable by site admin).
- **Error model**: non-2xx responses raise `httpx.HTTPStatusError` (Pattern A). The error includes the status code and response body for debugging.

## Maintainer

ModuleX core team.
