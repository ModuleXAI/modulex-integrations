# Google Meet

Schedule Google Meet video conferences by creating Google Calendar events with
an attached Meet link, via the Google Calendar REST API
(`https://www.googleapis.com/calendar/v3`).

## Authentication

OAuth 2.0 is the only supported authentication method — Google Calendar does not
issue long-lived personal access tokens for the events API.

### OAuth2 Authentication

- Create an OAuth 2.0 Client ID in the
  [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials).
- Enable the **Google Calendar API** for your project under **APIs & Services
  → Library**.
- Required env vars:
  - `GOOGLE_MEET_OAUTH2_CLIENT_ID`
    (format: `xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com`)
  - `GOOGLE_MEET_OAUTH2_CLIENT_SECRET` (format: `GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx`)
- Scopes requested:
  - `https://www.googleapis.com/auth/calendar`
  - `https://www.googleapis.com/auth/calendar.events`
- Authorized redirect URI to register on the Google OAuth app:
  `https://api.modulex.dev/credentials/oauth2/callback`
- Token validation uses
  `GET /calendar/v3/users/me/calendarList?maxResults=1`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `schedule_meeting` | Creates a new Google Calendar event with a Google Meet link attached. | `event_start_date`, `event_end_date` |
| `list_color_id_options` | Retrieves available event color options (id, background, foreground). | — |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved OAuth credential.

## Limits & Quotas

- Google Calendar API default quota: **1,000,000 queries/day** per project, with
  per-user limits of **600 queries/minute**. See the
  [Google Calendar API quotas page](https://developers.google.com/calendar/api/guides/quota)
  for details.
- `schedule_meeting` sends `conferenceDataVersion=1` so Google provisions a Meet
  link in the same call (counts as a single event-insert quota unit).
- **Error model**: non-2xx responses and timeouts are caught and returned as
  `success=False` + `error` rather than raising. Plan for retries on the agent
  side based on the error string. 401/403 typically means the OAuth token has
  expired or lacks the calendar scope.

## Maintainer

ModuleX core team.
