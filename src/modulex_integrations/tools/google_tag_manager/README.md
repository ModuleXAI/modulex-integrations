# Google Tag Manager

Manage tags, variables, and workspaces in Google Tag Manager containers via the
Tag Manager API v2 (`www.googleapis.com/tagmanager/v2`).

## Authentication

### OAuth2 Authentication (recommended)

- Create OAuth credentials at <https://console.cloud.google.com/apis/credentials>.
- Enable the **Tag Manager API** in the Google Cloud project.
- Register redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`.
- Scopes requested:
  - `https://www.googleapis.com/auth/tagmanager.edit.containers`
  - `https://www.googleapis.com/auth/tagmanager.readonly`
- Required env vars (custom OAuth app only):
  - `GOOGLE_TAG_MANAGER_OAUTH2_CLIENT_ID`
  - `GOOGLE_TAG_MANAGER_OAUTH2_CLIENT_SECRET`

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_tag` | Create a tag in a Google Tag Manager workspace | `account_id`, `container_id`, `workspace_id`, `name`, `type`, `parameter` |
| `get_tag` | Get a specific tag from a Google Tag Manager workspace | `account_id`, `container_id`, `workspace_id`, `tag_id` |
| `get_tags` | List all tags in a Google Tag Manager workspace | `account_id`, `container_id`, `workspace_id` |
| `list_account_id_options` | List available Google Tag Manager accounts | (none) |
| `update_tag` | Update a tag in a Google Tag Manager workspace | `account_id`, `container_id`, `workspace_id`, `tag_id`, `type`, `parameter` |
| `update_variable` | Update a variable in a Google Tag Manager workspace | `account_id`, `container_id`, `workspace_id`, `variable_id`, `name`, `type`, `parameter` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- Google Tag Manager API uses per-project quotas managed via the Google Cloud Console.
- Default quota: 10,000 requests per day per project (varies by endpoint).
- Rate limit: approximately 5 requests per second per user.
- Error model: non-2xx responses raise `httpx.HTTPStatusError` (Pattern A).

## Maintainer

ModuleX core team.
