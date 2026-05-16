# ClickUp

ClickUp project management integration via the v2 REST API. Pure HTTP.
23 actions across workspaces, spaces, folders, lists, tasks,
comments, tags, and team members.

## Authentication

- **`api_key` auth_type.** Personal API Token from
  Settings > Apps.
- Env var: `CLICKUP_API_KEY` (sensitive,
  `pk_xxxxxxxx_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).
- **Authorization header is the raw key — no `Bearer ` prefix.**
- `test_endpoint` hits `GET /team`.

## Runtime convention

Key-based: every `@tool` accepts `(api_key, ...)`.

## Tools

| group | tools |
| --- | --- |
| Teams / spaces | `get_teams`, `get_spaces`, `get_space`, `create_space` |
| Folders | `get_folders`, `get_folder`, `create_folder`, `delete_folder` |
| Lists | `get_lists`, `get_list`, `create_list` |
| Tasks | `get_tasks`, `get_task`, `create_task`, `update_task`, `delete_task` |
| Comments | `get_task_comments`, `create_task_comment` |
| Search | `search_tasks` |
| Tags | `get_space_tags`, `add_tag_to_task`, `remove_tag_from_task` |
| Members | `get_team_members` |

## Notes

- **`custom_task_ids=true&team_id=…` query string** lets you address
  tasks by their workspace-prefixed display ID (e.g. "ABC-123") on
  every task action.
- **`add_tag_to_task` / `remove_tag_from_task`** use path-style tag
  attachment (`POST /task/{id}/tag/{name}` — no body).
- **`search_tasks`** filters by `query` client-side because ClickUp's
  search endpoint has no full-text search; the API call only filters
  by structured fields.
- **`get_team_members`** is implemented as `GET /team` + a client-
  side filter — the team-list endpoint already includes the member
  roster per team. Matches legacy.
- **`get_lists` / `create_list`** require exactly one of `folder_id`
  or `space_id` (folderless lists live directly under a space).
- 30s timeout on every request.

## Maintainer

ModuleX core team.
