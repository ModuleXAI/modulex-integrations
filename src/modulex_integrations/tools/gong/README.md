# Gong

Revenue intelligence platform for recording, transcribing, and analyzing sales conversations via the Gong REST API (`us-66463.api.gong.io/v2`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth app at <https://app.gong.io/company/api>.
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required scopes: `api:calls:read:basic`, `api:calls:read:extensive`, `api:calls:create`, `api:workspaces:read`, `api:calls:read:transcript`
- Env vars (custom app only): `GONG_OAUTH2_CLIENT_ID`, `GONG_OAUTH2_CLIENT_SECRET`

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_new_call` | Add a new call to Gong | `client_unique_id`, `actual_start`, `direction`, `primary_user`, `parties` |
| `get_extensive_data` | List detailed call data with content selectors for topics, trackers, transcripts, and more | (none required) |
| `list_calls` | List calls with optional date range filtering | (none required) |
| `list_workspace_id_options` | Retrieve available workspace IDs and names | (none required) |
| `retrieve_transcripts_of_calls` | Retrieve transcripts of calls with optional date range and call ID filtering | (none required) |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- Gong API rate limits vary by endpoint and plan tier. Consult your Gong admin for specific limits.
- The `get_extensive_data` action paginates internally up to `max_results` (default 600).
- Error model: non-2xx responses are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
