# Gong

Revenue intelligence platform for recording, transcribing, and analyzing sales conversations via the Gong REST API (your per-tenant `https://<region>-<id>.api.gong.io/v2` base URL).

## Authentication

### API Key (HTTP Basic)

- A Gong technical administrator creates an **Access Key** + **Access Key Secret**
  under **Company Settings → Ecosystem → API** (<https://app.gong.io/company/api>).
  The Secret is shown only once.
- Find your per-tenant **API base URL** at <https://app.gong.io/company/api-authentication>
  (e.g. `https://us-12345.api.gong.io`) — it is region/tenant-specific.
- Env vars: `GONG_ACCESS_KEY`, `GONG_ACCESS_KEY_SECRET`, `GONG_API_BASE_URL`.
- Sent on every request as `Authorization: Basic base64(accessKey:accessKeySecret)`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_new_call` | Add a new call to Gong | `client_unique_id`, `actual_start`, `direction`, `primary_user`, `parties` |
| `get_extensive_data` | List detailed call data with content selectors for topics, trackers, transcripts, and more | (none required) |
| `list_calls` | List calls with optional date range filtering | (none required) |
| `list_workspace_id_options` | Retrieve available workspace IDs and names | (none required) |
| `retrieve_transcripts_of_calls` | Retrieve transcripts of calls with optional date range and call ID filtering | (none required) |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved API-key credential.

## Limits & Quotas

- Gong API rate limits vary by endpoint and plan tier. Consult your Gong admin for specific limits.
- The `get_extensive_data` action paginates internally up to `max_results` (default 600).
- Error model: non-2xx responses are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
