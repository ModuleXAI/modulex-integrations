# Google Ad Manager

Programmatic advertising platform for managing ad inventory, reporting, and campaign delivery via the Google Ad Manager REST API (`admanager.googleapis.com/v1`).

## Authentication

### OAuth2 Authentication (recommended)

- Create OAuth credentials at <https://console.cloud.google.com/apis/credentials>.
- Register redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`.
- Required scope: `https://www.googleapis.com/auth/admanager`.
- Env vars (custom OAuth app only): `GOOGLE_AD_MANAGER_OAUTH2_CLIENT_ID`, `GOOGLE_AD_MANAGER_OAUTH2_CLIENT_SECRET`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_report` | Create a report in Google Ad Manager | `parent`, `name`, `visibility`, `dimensions`, `metrics`, `report_type`, `date_range` |
| `list_network_options` | Retrieve available network options for Google Ad Manager | _(none)_ |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- Google Ad Manager API enforces per-network rate limits; consult your network's quota settings in the Ad Manager UI.
- Standard quota: 10,000 requests per day per project (default; can be increased via Google Cloud console).
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
