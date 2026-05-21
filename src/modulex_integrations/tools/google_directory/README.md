# Google Directory

Manage users, groups, and group memberships in Google Workspace via the
Admin SDK Directory API (`admin.googleapis.com/admin/directory/v1`).

## Authentication

### OAuth2 Authentication (recommended)

- Create OAuth credentials at <https://console.cloud.google.com/apis/credentials>.
- Enable the **Admin SDK API** in the Google Cloud project.
- Register redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required scopes:
  - `https://www.googleapis.com/auth/admin.directory.user`
  - `https://www.googleapis.com/auth/admin.directory.group`
  - `https://www.googleapis.com/auth/admin.directory.group.member`
- The authenticated user must be a Google Workspace admin with Directory API privileges.

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_member_to_group` | Adds a member to a Google Workspace group | `group_id`, `email` |
| `create_group` | Creates a new Google Workspace group | `email`, `name` |
| `create_user` | Creates a new Google Workspace user | `email`, `password`, `first_name`, `last_name` |
| `get_group` | Retrieves information about a Google Workspace group | `group_id` |
| `get_user` | Retrieves information about a Google Workspace user | `user_id` |
| `list_groups` | Retrieves a list of all groups in the Google Workspace directory | |
| `list_users` | Retrieves a list of all users in the Google Workspace directory | |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved OAuth credential.

## Limits & Quotas

- **Queries per day:** 150,000 (shared across all Admin SDK APIs per project).
- **Queries per minute per user:** 2,400.
- **Group members per group:** 200,000 (performance degrades above ~5,000).
- **Error model:** non-2xx responses raise `httpx.HTTPStatusError` (Pattern A).
  The agent should retry on 429/5xx based on the `Retry-After` header.

## Maintainer

ModuleX core team.
