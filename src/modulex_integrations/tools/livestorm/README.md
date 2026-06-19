# Livestorm

Video engagement platform for webinars and virtual events via the Livestorm REST API (`api.livestorm.co/v1`).

## Authentication

### API Token

- As the workspace owner or an admin, generate a token under
  **Account Settings → Integrations → Public API**
  ([docs](https://developers.livestorm.co/docs/api-token-authentication)). The
  token is shown only once. If the Public API card is missing, contact
  `support@livestorm.co` to enable API access for your account.
- Env var: `LIVESTORM_API_TOKEN`.
- Sent as a **plain** `Authorization: <token>` header (no `Bearer` prefix),
  with `Accept: application/vnd.api+json`.

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

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved API-token credential.

## Limits & Quotas

- No publicly documented rate limits for the Livestorm API.
- Pagination is applied automatically for list endpoints (page-based).
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
