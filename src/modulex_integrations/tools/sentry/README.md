# Sentry

Error tracking and performance monitoring platform integration against the Sentry REST API (`sentry.io/api/0`).

## Authentication

### Auth Token

- Go to [Sentry Settings -> Developer Settings -> Internal Integrations](https://docs.sentry.io/api/guides/create-auth-token/) to create or manage your auth tokens.
- Required env var: `SENTRY_AUTH_TOKEN` (format: `sntrys_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
- The token must have the appropriate scopes for the actions you intend to use (e.g. `event:read`, `project:read`, `issue:write`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_issue_events` | Return a list of events bound to an issue | `issue_id` |
| `list_project_events` | Return a list of events bound to a project | `organization_slug`, `project_slug` |
| `list_project_issues` | Return a list of issues bound to a project | `organization_slug`, `project_slug` |
| `update_issue` | Update an individual issue's attributes | `issue_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential.

## Limits & Quotas

- **Rate limits**: Sentry applies per-organization rate limits. Typical limits are ~100 requests/second for the events API.
- **Pagination**: List endpoints use cursor-based pagination; the integration follows cursors up to `max_results`.
- **Error model**: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
