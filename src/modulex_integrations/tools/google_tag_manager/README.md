# Google Tag Manager

Read tags and accounts from Google Tag Manager containers via the
Tag Manager API v2 (`www.googleapis.com/tagmanager/v2`).

This integration is read-only: it requests the `tagmanager.readonly` scope and
exposes no tag, variable, or workspace mutations.

## Authentication

### OAuth2 Authentication (recommended)

- Create OAuth credentials at <https://console.cloud.google.com/apis/credentials>.
- Enable the **Tag Manager API** in the Google Cloud project.
- Register redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`.
- Scopes requested:
  - `https://www.googleapis.com/auth/tagmanager.readonly`
- Required env vars (custom OAuth app only):
  - `GOOGLE_TAG_MANAGER_OAUTH2_CLIENT_ID`
  - `GOOGLE_TAG_MANAGER_OAUTH2_CLIENT_SECRET`

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_tag` | Get a specific tag from a Google Tag Manager workspace | `account_id`, `container_id`, `workspace_id`, `tag_id` |
| `get_tags` | List all tags in a Google Tag Manager workspace | `account_id`, `container_id`, `workspace_id` |
| `list_account_id_options` | List available Google Tag Manager accounts | (none) |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- Google Tag Manager API uses per-project quotas managed via the Google Cloud Console.
- Default quota: 10,000 requests per day per project (varies by endpoint).
- Rate limit: approximately 5 requests per second per user.
- Error model: non-2xx responses raise `httpx.HTTPStatusError` (Pattern A).

## Maintainer

ModuleX core team.
