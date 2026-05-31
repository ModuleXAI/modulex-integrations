# Motion

AI-powered task and project management platform with automatic scheduling, accessed via the Motion REST API (`api.usemotion.com/v1`).

## Authentication

### API Key Authentication

- Sign in at <https://app.usemotion.com>, navigate to **Settings > API**, and generate or copy your API key.
- Required env var: `MOTION_API_KEY` (format: `xxxxxxxxxxxxxxxxxxxxx`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_task` | Create a new task in a Motion workspace | `workspace_id`, `name` |
| `delete_task` | Delete a specific task by ID | `task_id` |
| `get_schedules` | Get a list of schedules for the authenticated user | — |
| `get_task` | Retrieve a specific task by ID | `task_id` |
| `move_workspace` | Move a task to another workspace. Resets the task's project, status, labels, and assignee | `task_id`, `workspace_id` |
| `update_task` | Update a specific task's properties | `task_id` |

Every tool takes an additional `api_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- **Rate limit**: 12 requests per minute per API key (Motion API documentation).
- **Pricing**: API access requires a Motion Individual or Team plan.
- **Error model**: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
