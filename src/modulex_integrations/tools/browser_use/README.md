# Browser Use

AI-powered cloud browser automation via the Browser Use REST API
(`api.browser-use.com/api/v3`). Create agent sessions to perform web
tasks, manage standalone browser sessions via CDP, and organize
persistent profiles and workspaces.

## Authentication

### API Key (recommended)

- Sign in at <https://cloud.browser-use.com>, navigate to your project
  settings or API Keys section.
- Create or copy your API key.
- Required env var: `BROWSER_USE_API_KEY` (format: `bu_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_session` | Create an agent session, dispatch a task, or dispatch a follow-up task to an existing idle session | — |
| `get_session` | Get the current state, output, live URL, screenshot URL, and cost details for an agent session | `session_id` |
| `list_sessions` | List Browser Use agent sessions for the authenticated project | — |
| `delete_session` | Delete an agent session | `session_id` |
| `stop_session` | Stop the current task or stop the entire Browser Use agent session | `session_id` |
| `list_session_messages` | List messages from a Browser Use agent session | `session_id` |
| `create_browser_session` | Create a standalone browser session for direct browser control through CDP | — |
| `get_browser_session` | Get details for a standalone browser session | `browser_session_id` |
| `list_browser_sessions` | List standalone browser sessions for direct browser control via CDP | — |
| `update_browser_session` | Update a standalone browser session (currently supports stop) | `browser_session_id`, `action` |
| `create_profile` | Create a profile to preserve cookies, local storage, and login state | — |
| `get_profile` | Get a Browser Use profile by ID | `profile_id` |
| `list_profiles` | List Browser Use profiles | — |
| `delete_profile` | Delete a Browser Use profile and its persisted browser state | `profile_id` |
| `update_profile` | Update a Browser Use profile name or user ID | `profile_id` |
| `create_workspace` | Create a workspace for persistent shared file storage | — |
| `get_workspace` | Get a Browser Use workspace by ID | `workspace_id` |
| `list_workspaces` | List Browser Use workspaces | — |
| `delete_workspace` | Delete a workspace and its stored files (irreversible) | `workspace_id` |
| `update_workspace` | Update a Browser Use workspace name | `workspace_id`, `name` |
| `get_workspace_size` | Get storage usage for a workspace | `workspace_id` |
| `list_workspace_files` | List files and folders in a workspace | `workspace_id` |
| `delete_workspace_file` | Delete a file from a workspace | `workspace_id`, `path` |
| `upload_workspace_files` | Create presigned upload URLs for workspace files | `workspace_id`, `files_json` |
| `get_account_billing` | Get account billing details for the authenticated project | — |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential.

## Limits & Quotas

- No publicly documented request rate limits at the time of writing.
- Agent sessions are billed by runtime and model usage; `max_cost_usd`
  parameter available to cap spend per session.
- Browser sessions are billed by runtime and can run up to 4 hours.
- Error model: non-2xx responses and timeouts are caught and returned
  as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
