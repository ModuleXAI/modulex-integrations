# Amplitude

Track events, identify users and groups, search for users, query analytics, and retrieve revenue data from Amplitude via its HTTP V2, Identify, Dashboard REST, and User Profile APIs.

## Authentication

### API Key + Secret Key (HTTP Basic / form / header)

- In Amplitude, open your project under **Settings → Projects → (project) → General**
  and copy the **API Key** and the **Secret Key**.
- Env vars: `AMPLITUDE_API_KEY` (required), `AMPLITUDE_SECRET_KEY` (required for analytics).
- The **API Key** alone authenticates event ingestion: `send_event` (HTTP V2, JSON body),
  `identify_user` and `group_identify` (form-encoded `api_key` + `identification`).
- The **API Key + Secret Key** together authenticate the Dashboard REST API
  (`user_search`, `user_activity`, `event_segmentation`, `get_active_users`,
  `realtime_active_users`, `list_events`, `get_revenue`) as
  `Authorization: Basic base64(apiKey:secretKey)`.
- The **Secret Key** alone authenticates `user_profile`
  (`Authorization: Api-Key <secretKey>`).
- Endpoints default to US data residency (`amplitude.com` / `api2.amplitude.com`
  / `profile-api.amplitude.com`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `send_event` | Track an event in Amplitude using the HTTP V2 API | `event_type` |
| `identify_user` | Set user properties via the Identify API | `user_properties` |
| `group_identify` | Set group-level properties | `group_type`, `group_value`, `group_properties` |
| `user_search` | Search for a user by User ID, Device ID, or Amplitude ID | `user` |
| `user_activity` | Get the event stream for a user by Amplitude ID | `amplitude_id` |
| `user_profile` | Get a user profile (properties, cohorts, computed properties) | (none required) |
| `event_segmentation` | Query event analytics data with segmentation | `event_type`, `start`, `end` |
| `get_active_users` | Get active or new user counts over a date range | `start`, `end` |
| `realtime_active_users` | Get real-time active user counts (5-minute granularity) | (none required) |
| `list_events` | List all event types with weekly totals | (none required) |
| `get_revenue` | Get revenue LTV data (ARPU, ARPPU, total revenue, paying users) | `start`, `end` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential.

## Limits & Quotas

- HTTP V2 ingestion: limit uploads to 100 batches/second and 1000 events/second.
- Dashboard REST API analytics endpoints are subject to per-project rate limits and cost thresholds.
- `user_activity` returns at most 1000 events per call (use `offset` to page).
- Error model: non-2xx responses (and missing credentials) are returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
