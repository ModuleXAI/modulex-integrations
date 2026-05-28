# PagerDuty

Incident management, on-call scheduling, and alerting via the PagerDuty REST API (`api.pagerduty.com`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth app at the [PagerDuty Developer Console](https://developer.pagerduty.com/docs/app-integration-development/).
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Scopes requested: `read`, `write`
- Env vars (only for custom OAuth app):
  - `PAGERDUTY_OAUTH2_CLIENT_ID` — your OAuth App Client ID
  - `PAGERDUTY_OAUTH2_CLIENT_SECRET` — your OAuth App Client Secret

## Tools

| name | description | required params |
| --- | --- | --- |
| `trigger_incident` | Trigger a new incident on a PagerDuty service | `title`, `service_id` |
| `acknowledge_incident` | Acknowledge a triggered incident in PagerDuty | `incident_id` |
| `resolve_incident` | Resolve a triggered or acknowledged incident in PagerDuty | `incident_id` |
| `find_oncall_user` | Find the user on call for a specific PagerDuty schedule | `schedule_id`, `user_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- **Rate limits**: PagerDuty REST API allows up to 960 requests per minute (varies by account tier).
- **Throttling**: Requests exceeding the rate limit receive HTTP 429; implement client-side backoff.
- **Error model**: non-2xx responses raise `httpx.HTTPStatusError` (Pattern A). The caller should handle retries.

## Maintainer

ModuleX core team.
