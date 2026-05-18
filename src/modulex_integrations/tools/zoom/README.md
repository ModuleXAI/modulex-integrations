# Zoom

Video conferencing, meetings, webinars, and team chat platform via the Zoom REST API (`api.zoom.us/v2`).

## Authentication

### OAuth2 Authentication

- Register an OAuth app at the [Zoom App Marketplace](https://marketplace.zoom.us/develop/create).
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required env vars (only for custom OAuth app):
  - `ZOOM_OAUTH2_CLIENT_ID` — OAuth App Client ID
  - `ZOOM_OAUTH2_CLIENT_SECRET` — OAuth App Client Secret
- Scopes requested: `meeting:write:admin`, `meeting:read:admin`, `recording:read:admin`, `chat_message:write`, `chat_channel:read`, `user:read:admin`, `user:write:admin`, `phone:read:admin`, `webinar:read:admin`, `webinar:write:admin`, `report:read:admin`

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_meeting` | Create a meeting for the authenticated user | |
| `list_meetings` | List meetings for a user | `user_id` |
| `get_meeting_details` | Retrieve the details of a meeting | `meeting_id` |
| `update_meeting` | Update an existing Zoom meeting's topic, time, or other settings | `meeting_id` |
| `delete_meeting` | Delete a meeting | `meeting_id` |
| `get_current_user` | Return the authenticated Zoom user's ID, name, email, account ID, and timezone | |
| `send_chat_message` | Send a chat message on Zoom to an individual contact or a channel | `message` |
| `list_channels` | List the authenticated user's chat channels | |
| `add_meeting_registrant` | Register a participant for a meeting | `meeting_id`, `email`, `first_name`, `last_name` |
| `get_meeting_recordings` | Get the recordings of a meeting | `meeting_id` |
| `get_meeting_transcript` | Get the transcript of a past meeting as speaker-attributed plain text | `meeting_id` |
| `get_meeting_summary` | Retrieve the AI-generated summary of a meeting or webinar | `meeting_id` |
| `list_all_recordings` | List all cloud recordings for a user | |
| `list_call_recordings` | Get your account's Zoom Phone call recordings | |
| `list_user_call_logs` | Get a user's Zoom Phone call logs | `user_id` |
| `list_past_meeting_participants` | Retrieve participants from a past meeting | `meeting_id` |
| `create_user` | Create a new user in your Zoom account | `action`, `email`, `type` |
| `delete_user` | Disassociate or permanently delete a user from the account | `user_id` |
| `get_webinar_details` | Get details of a scheduled webinar | `webinar_id` |
| `update_webinar` | Update a webinar's topic, start time, or other settings | `webinar_id` |
| `add_webinar_registrant` | Register a participant for a webinar | `webinar_id`, `email`, `first_name`, `last_name` |
| `list_webinar_participants_report` | Retrieve detailed report on each webinar attendee | `webinar_id` |
| `list_past_webinar_qa` | List Q&A from a past webinar | `webinar_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- **Rate limits**: Zoom enforces per-second and daily rate limits that vary by plan and endpoint. Typical limits are 10 requests/second for most endpoints.
- **Meeting creation**: Maximum 100 meetings per user per day.
- **Recordings**: Cloud recording storage depends on the plan tier.
- **Reports**: Webinar participant reports are available for the last 6 months only.
- **Error model**: Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
