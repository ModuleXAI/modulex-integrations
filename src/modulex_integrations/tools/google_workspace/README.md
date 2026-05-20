# Google Workspace Admin

Retrieve admin audit activity reports from Google Workspace via the Admin SDK Reports API (`admin.googleapis.com`).

## Authentication

### OAuth2 Authentication (recommended)

- Create OAuth credentials at the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
- Enable the **Admin SDK API** in your Google Cloud project.
- Register redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`.
- Scopes requested: `https://www.googleapis.com/auth/admin.reports.audit.readonly`.
- Required env vars (custom OAuth app only):
  - `GOOGLE_WORKSPACE_OAUTH2_CLIENT_ID` (format: `xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com`)
  - `GOOGLE_WORKSPACE_OAUTH2_CLIENT_SECRET` (format: `GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_activities_by_admin` | Retrieve admin console activities for a specific administrator | `application_name`, `user_key` |
| `list_activities_by_event_and_admin` | Retrieve activities filtered by both a specific event name and administrator | `application_name`, `event_name`, `user_key` |
| `list_activities_by_event_name` | Retrieve activities for all users filtered by a specific event name | `application_name`, `event_name` |
| `list_all_activities` | Retrieve all administrative activities for the account | `application_name` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- **Admin SDK Reports API quota**: 2,400 queries per minute per Google Workspace domain (default).
- **Per-user limit**: 480 queries per minute per user.
- **Error model**: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising. Plan for retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
