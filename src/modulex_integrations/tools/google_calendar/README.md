# Google Calendar

Manage Google Calendar events, calendars, attendees, recurring series, and free/busy availability via the Google Calendar v3 REST API (`https://www.googleapis.com/calendar/v3`).

## Authentication

### OAuth2 Authentication

- Create an OAuth client in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials). The OAuth consent screen must list Google Calendar API as an enabled service.
- Add `https://api.modulex.dev/credentials/oauth2/callback` as an authorized redirect URI on the OAuth client.
- Required env vars (custom-app deployments only):
  - `GOOGLE_CALENDAR_OAUTH2_CLIENT_ID` (format: `xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com`)
  - `GOOGLE_CALENDAR_OAUTH2_CLIENT_SECRET` (format: `GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx`)
- Requested scopes:
  - `https://www.googleapis.com/auth/calendar` — full read/write access to calendars and events.
  - `https://www.googleapis.com/auth/calendar.events` — fine-grained event management.

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_attendees_to_event` | Add attendees to an existing Google Calendar event. | `event_id`, `attendees` |
| `create_event` | Create a new event in a Google Calendar. | `summary`, `event_start_date`, `event_end_date` |
| `delete_event` | Delete an event from a Google Calendar. | `event_id` |
| `get_calendar` | Retrieve metadata for a Google Calendar. |  |
| `get_current_user` | Retrieve the authenticated user's primary calendar, calendar list, settings, and color palette. |  |
| `get_date_time` | Return the current date/time, IANA timezone, UTC offset, ISO string, and RFC3339 timestamp. |  |
| `get_event` | Retrieve a single event from a Google Calendar. | `event_id` |
| `list_calendars` | List calendars the authenticated user can access. |  |
| `list_color_id_options` | List available color ID options for events, with hex backgrounds. |  |
| `list_event_instances` | List individual instances of a recurring event. | `event_id` |
| `list_events` | List events on a Google Calendar, with optional filters and pagination. |  |
| `query_free_busy_calendars` | Query free/busy time blocks across one or more calendars over a date range. | `calendar_ids`, `time_min`, `time_max` |
| `quick_add_event` | Create an event from a natural-language string (Google parses date/time/title). | `text` |
| `update_event` | Update an existing event on a Google Calendar. | `event_id` |
| `update_event_instance` | Update a single instance of a recurring event (changes apply only to that instance). | `instance_id` |
| `update_following_instances` | Update all instances of a recurring event from a given instance forward by splitting the series. | `recurring_event_id`, `instance_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth2 credential.

## Limits & Quotas

- Per-user default quota: ~1,000,000 queries/day; per-user per-100-seconds quota also applies (see [Google Calendar API quotas](https://developers.google.com/calendar/api/guides/quota)).
- Quotas are shared across all Google Calendar API methods for the authenticated user.
- `list_events` and `list_event_instances` page through results internally and honor `max_results` as a soft cap across pages.
- `update_following_instances` performs four sequential API calls (get original, get instance, delete instance, trim recurrence, create new event); on partial failure the deleted instance is restored automatically when possible. Network or quota errors mid-flow can leave the series in a manually-recoverable state.
- Error model: non-2xx responses raise (Pattern A). The runtime surfaces them as failed tool calls; the agent decides whether to retry.

## Maintainer

ModuleX core team.
