# Linear

Project-management and issue-tracking integration for Linear via the
**GraphQL API** at `api.linear.app/graphql`. Covers team discovery,
issue CRUD + search, and project list/create.

## Authentication

### API Key (raw, no Bearer prefix)

- Required env var: `LINEAR_API_KEY`.
- Settings > API > Personal API keys at <https://linear.app/settings/api>.
- Sent as `Authorization: <key>` (Linear's documented contract — no
  `Bearer ` prefix).
- `test_endpoint` runs `query { viewer { id name } }` against the
  GraphQL endpoint.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_teams` | List teams in the workspace | — |
| `get_issue` | Single issue by id | `issue_id` |
| `search_issues` | Issues by team/project/assignee/state/label/query | — |
| `create_issue` | New issue | `team_id`, `title` |
| `update_issue` | Mutate an existing issue | `issue_id` |
| `list_projects` | Projects with optional team filter | — |
| `create_project` | New project | `team_id`, `name` |

## Limits & Quotas

- All tools share a single GraphQL endpoint; failures (HTTP non-200,
  GraphQL `errors`, exceptions) surface as `success=False` + `error`.
- The `search_issues` and `list_projects` actions interpolate filter
  values into the GraphQL string verbatim (matching legacy). Inputs
  are scoped to internal IDs / label names — not user prose — and
  treated as opaque tokens.
- Output objects keep their nested GraphQL shape unchanged (state,
  team, assignee, creator, labels.nodes for issues; lead, status for
  projects).

## Maintainer

ModuleX core team.
