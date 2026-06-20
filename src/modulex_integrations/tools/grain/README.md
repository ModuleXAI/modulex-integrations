# Grain

Access Grain meeting recordings, transcripts, highlights, and
AI-generated summaries through the Grain public REST API
(`api.grain.com/_/public-api`). List and retrieve recordings, fetch
full transcripts, browse teams, meeting types, and views, and manage
webhook subscriptions for recording events.

## Authentication

Authenticate with a Grain Personal Access Token, sent as
`Authorization: Bearer <token>`. The credential is validated against
`POST /_/public-api/v2/teams`.

### API Key

- Log in to your Grain account at <https://grain.com>.
- Open **Settings** and navigate to the API / Integrations section.
- Create a Personal Access Token (developer access may require
  approval — the Grain public API is in beta).
- Required env var: `GRAIN_API_KEY`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_recordings` | List recordings with optional filters and pagination | — |
| `get_recording` | Get details of a single recording by ID | `recording_id` |
| `get_transcript` | Get the full transcript of a recording | `recording_id` |
| `list_views` | List available views for webhook subscriptions | — |
| `list_teams` | List all teams in the workspace | — |
| `list_meeting_types` | List all meeting types in the workspace | — |
| `create_hook` | Create a webhook to receive recording events | `hook_url`, `view_id` |
| `list_hooks` | List all webhooks for the account | — |
| `delete_hook` | Delete a webhook by ID | `hook_id` |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential.

## Limits & Quotas

- The Grain public API requires the `Public-Api-Version` header
  (currently `2025-10-31`) on the recording, transcript, team, and
  meeting-type endpoints.
- Developer access to the public API is in beta and may be limited to
  approved partners.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
