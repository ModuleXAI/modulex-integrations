# Google Tasks

Manage tasks and task lists using the Google Tasks REST API (`tasks.googleapis.com/tasks/v1`).

## Authentication

### OAuth2 Authentication

- Register an OAuth app at [Google Cloud Console](https://console.cloud.google.com/apis/credentials); enable the Google Tasks API.
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Scopes requested: `https://www.googleapis.com/auth/tasks`
- Required env vars (custom OAuth app only):
  - `GOOGLE_TASKS_OAUTH2_CLIENT_ID` (format: `xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com`)
  - `GOOGLE_TASKS_OAUTH2_CLIENT_SECRET` (format: `GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_task` | Creates a new task and adds it to the authenticated user's task lists | `task_list_id`, `title`, `completed` |
| `create_task_list` | Creates a new task list and adds it to the authenticated user's task lists | `title` |
| `delete_task` | Deletes the authenticated user's specified task | `task_list_id`, `task_id` |
| `delete_task_list` | Deletes the authenticated user's specified task list | `task_list_id` |
| `list_tasks` | Returns all tasks in the specified task list | `task_list_id` |
| `list_task_lists` | Lists the authenticated user's task lists | — |
| `update_task` | Updates the authenticated user's specified task | `task_list_id`, `task_id`, `title` |
| `update_task_list` | Updates the authenticated user's specified task list | `task_list_id`, `title` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- Default quota: 50,000 queries per day per project (Google Cloud project-level).
- Per-user rate limit: ~500 requests per 100 seconds.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
