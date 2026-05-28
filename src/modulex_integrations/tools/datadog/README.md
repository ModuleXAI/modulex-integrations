# Datadog

Infrastructure monitoring, log management, and application performance platform via the Datadog REST API (`api.{region}/api`).

## Authentication

### API Key Authentication

- Go to [Organization Settings > API Keys](https://app.datadoghq.com/organization-settings/api-keys) and create or copy an API key.
- Go to [Organization Settings > Application Keys](https://app.datadoghq.com/organization-settings/application-keys) and create or copy an Application key.
- Required env vars: `DATADOG_API_KEY` (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`) and `DATADOG_APPLICATION_KEY` (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).
- Both keys are required for all API calls except region detection (`get_account_info` only needs the API key).

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_account_info` | Detect the Datadog region for the connected account by validating the API key across all regions | (none) |
| `get_metric_data` | Query time-series metric data for analyzing trends and system performance | `region`, `query`, `from_ts`, `to_ts` |
| `post_metric_data` | Post custom time-series metric data points to Datadog | `region`, `metric`, `points` |
| `search_dashboards` | List and search Datadog dashboards with their IDs, titles, and URLs | `region` |
| `search_events` | Search Datadog events including monitor state changes, deployment markers, and error spikes | `region` |
| `search_hosts` | Search monitored infrastructure hosts with filtering by tag, name, or partial match | `region` |
| `search_incidents` | Search Datadog incidents by state, severity, and metadata | `region` |
| `search_logs` | Search Datadog logs matching a query with support for facets and time ranges | `region`, `query` |
| `search_metrics` | List available Datadog metric names, optionally filtered by host | `region` |
| `search_monitors` | Search Datadog monitors (alerting rules) including status, thresholds, and conditions | `region` |
| `search_services` | List services from Datadog Service Catalog with ownership, metadata, and team info | `region` |

Every tool takes additional `api_key` and `application_key` parameters that the runtime fills in from the resolved credential.

## Limits & Quotas

- **Rate limits**: Datadog enforces per-endpoint rate limits; default is 300 requests/minute for most endpoints, 60/min for logs search, and 120/hour for metric submission.
- **Pagination**: Most list endpoints support pagination via `count`/`start` or `page`/`page_size` parameters.
- **Regions**: The API base URL varies by account region. Use `get_account_info` to auto-detect the correct region before calling other tools.
- **Error model**: Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
