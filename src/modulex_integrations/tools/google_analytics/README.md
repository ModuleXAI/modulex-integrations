# Google Analytics

Manage Google Analytics 4 properties, list accounts, configure key events, and
run analytics reports against the Google Analytics Admin
(`analyticsadmin.googleapis.com`) and Data (`analyticsdata.googleapis.com`)
APIs.

## Authentication

Authentication uses Google OAuth 2.0. The credential is validated against the
Admin API `/accountSummaries` endpoint at credential-creation time.

### OAuth2 Authentication

- Create OAuth 2.0 credentials in the
  [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials).
- Enable the **Google Analytics Admin API** and **Google Analytics Data API**
  on the same Google Cloud project.
- Register the redirect URI
  `https://api.modulex.dev/credentials/oauth2/callback` on your OAuth client.
- Required env vars:
  - `GOOGLE_ANALYTICS_OAUTH2_CLIENT_ID` (format:
    `1234567890-abcdefghijklmnop.apps.googleusercontent.com`)
  - `GOOGLE_ANALYTICS_OAUTH2_CLIENT_SECRET` (format:
    `GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx`)
- Requested OAuth scopes:
  - `https://www.googleapis.com/auth/analytics.edit` — required to create
    properties and key events.
  - `https://www.googleapis.com/auth/analytics.readonly` — required to list
    accounts/properties and run reports.

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_account_options` | List Google Analytics accounts available to the authenticated user via the Admin API. | _(none)_ |
| `list_property_options` | List GA4 properties by flattening propertySummaries from /accountSummaries. | _(none)_ |
| `create_ga4_property` | Create a new GA4 property under an existing account. | `account`, `display_name`, `time_zone` |
| `create_key_event` | Create a GA4 key event (conversion) on a property. | `parent`, `event_name`, `counting_method` |
| `run_report` | Run a Universal Analytics v4 report (legacy; UA was sunset July 2024). | `view_id`, `start_date`, `end_date`, `metrics` |
| `run_report_in_ga4` | Run a GA4 Data API report against a GA4 property. | `property`, `start_date`, `end_date`, `metrics` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved OAuth credential.

## Limits & Quotas

- **Admin API** — default quota is 1,200 requests per minute per project, with
  a daily ceiling of 600,000 requests per project. See the
  [Admin API quotas docs](https://developers.google.com/analytics/devguides/config/admin/v1/quotas)
  for the per-method breakdown.
- **Data API** — quotas are tracked separately per property (core tokens,
  realtime tokens, server errors). See the
  [Data API quotas docs](https://developers.google.com/analytics/devguides/reporting/data/v1/quotas)
  for the multi-token model and per-tier limits (Standard vs. Analytics 360).
- **Universal Analytics Reporting API v4** is included for backward
  compatibility only; Universal Analytics properties stopped processing data on
  July 1, 2024. `run_report` will return `success=False` with an API error
  for any non-GA4 view.
- **Error model** — non-2xx HTTP responses and timeouts are caught and returned
  as `success=False` plus a populated `error` string rather than raised. Plan
  for agent-side retries based on the error string.

## Maintainer

ModuleX core team.
