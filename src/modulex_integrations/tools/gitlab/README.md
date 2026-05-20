# GitLab

Repository and project management platform for the GitLab REST API (`gitlab.com/api/v4`).

## Authentication

### OAuth2 Authentication

- Register an OAuth application at <https://gitlab.com/-/user_settings/applications>.
- Required redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Scopes requested: `api` (full API access including read/write on repositories, issues, epics, groups, and members).
- Env vars (only when bringing your own OAuth app):
  - `GITLAB_OAUTH2_CLIENT_ID` — OAuth App Client ID
  - `GITLAB_OAUTH2_CLIENT_SECRET` — OAuth App Client Secret

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_branch` | Create a new branch in a GitLab repository | `project_id`, `ref`, `branch_name` |
| `create_epic` | Create a new epic in a GitLab group (requires GitLab Premium or Ultimate) | `group_id`, `title` |
| `create_issue` | Create a new issue in a GitLab project | `project_id`, `title` |
| `get_issue` | Get a single issue from a GitLab project | `project_id`, `issue_iid` |
| `get_repo_branch` | Get a single repository branch from a GitLab project | `project_id`, `branch` |
| `list_commits` | List commits in a GitLab repository branch | `project_id` |
| `list_groups` | List all groups accessible to the authenticated user | _(none)_ |
| `list_project_members` | List all members of a GitLab project | `project_id` |
| `list_repo_branches` | Get a list of repository branches from a GitLab project | `project_id` |
| `search_issues` | Search for issues in a GitLab project | `project_id` |
| `update_epic` | Update an existing epic in a GitLab group (requires GitLab Premium or Ultimate) | `group_id`, `epic_iid` |
| `update_issue` | Update an existing issue in a GitLab project | `project_id`, `issue_iid` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- **Authenticated requests**: 2,000 requests per minute per user (GitLab.com).
- **Unauthenticated**: 500 requests per minute.
- **Epics API**: restricted to GitLab Premium and Ultimate tiers.
- **Error model**: non-2xx responses raise `httpx.HTTPStatusError` (Pattern A). The agent or runtime catches the exception at a higher layer.

## Maintainer

ModuleX core team.
