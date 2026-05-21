# Hootsuite

Social media management platform for scheduling posts and managing profiles via the Hootsuite REST API (`platform.hootsuite.com/v1`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth app at <https://developer.hootsuite.com/docs/getting-started>.
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Scopes requested: `offline`
- Required env vars (only for custom OAuth apps):
  - `HOOTSUITE_OAUTH2_CLIENT_ID` — your app's Client ID
  - `HOOTSUITE_OAUTH2_CLIENT_SECRET` — your app's Client Secret

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_media_upload_job` | Creates a new media upload job on Hootsuite by uploading a file from a public URL | `size_bytes`, `mime_type`, `file_url` |
| `get_media_upload_status` | Gets the status of a media upload job on Hootsuite | `file_id` |
| `list_social_profiles` | Retrieves a list of social profiles for the authenticated Hootsuite account | (none) |
| `schedule_message` | Schedules a message to be published on one or more social profiles | `text`, `social_profile_ids` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth2 credential.

## Limits & Quotas

- Hootsuite API rate limits vary by plan tier; consult your account's developer dashboard for current limits.
- Free/Professional plans have lower API access thresholds than Enterprise plans.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
