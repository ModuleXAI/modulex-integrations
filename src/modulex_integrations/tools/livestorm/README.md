# Livestorm

Video engagement platform for webinars and virtual events via the Livestorm REST API (`api.livestorm.co/v1`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth application at the [Livestorm developer portal](https://developers.livestorm.co).
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required env vars (custom app only):
  - `LIVESTORM_OAUTH2_CLIENT_ID` — OAuth App Client ID
  - `LIVESTORM_OAUTH2_CLIENT_SECRET` — OAuth App Client Secret
- Scopes: none documented; the platform grants full API access upon authorization.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_event` | Create a new event | `owner_id`, `title` |
| `get_event` | Retrieve a single event | `event_id` |
| `list_attendees_from_event` | List all the people linked to all the sessions of an event | `event_id` |
| `list_events` | List the events of your workspace | |
| `list_sessions` | List all your event sessions | |
| `register_someone_for_session` | Register a new participant for a session | `session_id` |
| `update_event` | Update an event with its full list of attributes | `event_id`, `owner_id`, `title`, `slug`, `status`, `description`, `recording_enabled`, `chat_enabled`, `everyone_can_speak`, `detailed_registration_page_enabled`, `light_registration_page_enabled`, `recording_public`, `show_in_company_page`, `polls_enabled`, `questions_enabled` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- No publicly documented rate limits for the Livestorm API.
- Pagination is applied automatically for list endpoints (page-based).
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
