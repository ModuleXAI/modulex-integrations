# Mixpanel

Product analytics platform for tracking user events and behaviors via the Mixpanel Track API (`api.mixpanel.com`).

## Authentication

### Project Token

- Sign in at [mixpanel.com](https://mixpanel.com), go to **Settings > Project Settings**, and copy your Project Token.
- Required env var: `MIXPANEL_API_KEY` (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
- The project token is used as a data field in the Track API request body (not as an HTTP auth header).

## Tools

| name | description | required params |
| --- | --- | --- |
| `emit_event_to` | Send an event to Mixpanel | `event_name`, `distinct_id` |

Every tool takes an additional `api_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- No documented per-token rate limits for the Track API ingestion endpoint.
- Mixpanel recommends batching events (up to 2000 per request) for high-volume use cases; this integration sends one event per call.
- Error model: non-2xx responses and Mixpanel rejections (response body `0`) are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
