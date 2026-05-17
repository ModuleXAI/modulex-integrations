# GitHub

Repository, issue, pull request, branch, commit, and code search actions
against the GitHub REST API (v3, `api.github.com`).

## Authentication

Two methods are supported. Both use the same `Authorization: Bearer <token>`
header against `https://api.github.com/user` for the credential test.

### OAuth2 (recommended)

- Register a GitHub OAuth App at
  <https://github.com/settings/applications/new>.
- Required env vars (only for custom OAuth Apps; the modulex-hosted
  default is filled automatically):
  - `GITHUB_OAUTH2_CLIENT_ID`
  - `GITHUB_OAUTH2_CLIENT_SECRET`
- Scopes requested: `repo`, `user`, `read:org`, `workflow`.
- Auth URL: `https://github.com/login/oauth/authorize`
- Token URL: `https://github.com/login/oauth/access_token`

### Personal Access Token

- Generate at <https://github.com/settings/tokens> (Classic or
  Fine-grained).
- Required env var: `GITHUB_PERSONAL_TOKEN` (format: `ghp_xxx` for
  classic, `github_pat_xxx` for fine-grained).
- For Classic, grant at minimum the `repo`, `user`, `read:org`, and
  `workflow` scopes.

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_repositories` | List repositories for the authenticated user | — |
| `create_repository` | Create a new repository | `name` |
| `delete_repository` | Delete a repository (irreversible, needs `delete_repo`) | `owner`, `repo` |
| `get_repository` | Get repository details | `owner`, `repo` |
| `list_issues` | List issues in a repository | `owner`, `repo` |
| `create_issue` | Create a new issue | `owner`, `repo`, `title` |
| `get_issue` | Get issue details | `owner`, `repo`, `issue_number` |
| `update_issue` | Update an existing issue | `owner`, `repo`, `issue_number` |
| `list_pull_requests` | List pull requests | `owner`, `repo` |
| `create_pull_request` | Create a new pull request | `owner`, `repo`, `title`, `head`, `base` |
| `get_pull_request` | Get pull request details | `owner`, `repo`, `pull_number` |
| `merge_pull_request` | Merge a pull request | `owner`, `repo`, `pull_number` |
| `create_branch` | Create a new branch | `owner`, `repo`, `branch_name` |
| `get_file_content` | Read a file from a repository | `owner`, `repo`, `path` |
| `create_commit` | Commit one or more file changes | `owner`, `repo`, `branch`, `message`, `files` |
| `search_code` | Search code across repositories | `query` |

All tools take an additional `auth_type` and `auth_data` parameter pair
that the runtime fills in; LLM-facing schemas list only the columns
above. See `manifest.py` for the full parameter definitions.

## Limits & Quotas

- **Authenticated REST API:** 5,000 requests per hour per token.
- **Search API** (`search_code`): 30 requests per minute, separate
  quota — and `q` must be at least one valid qualifier (e.g.
  `repo:owner/name` or `language:python`).
- **`create_commit`** makes five sequential API calls (ref, base commit,
  one blob per file, tree, commit, ref update). Budget accordingly when
  committing many files.
- **`delete_repository`** is irreversible and requires the token to
  carry the `delete_repo` scope; Fine-grained tokens additionally need
  the *Administration: write* permission.

## Maintainer

ModuleX core team.
