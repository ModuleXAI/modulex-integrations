# Segment

Customer data platform for collecting, cleaning, and controlling customer data
via the Segment Tracking API (`api.segment.io/v1`).

## Authentication

### Write Key

- Obtain your Write Key from your Segment source settings at
  <https://app.segment.com> under Connections > Sources > [Your Source] > Settings.
- Required env var: `SEGMENT_WRITE_KEY` (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).
- The Write Key is used as HTTP Basic Auth (username = write key, password empty).

## Tools

| name | description | required params |
| --- | --- | --- |
| `alias` | Associate one user identity with another in Segment | `previous_id` |
| `group` | Associate an identified user with a group in Segment | `group_id` |
| `identify` | Identify a user and record traits about them in Segment | (none — at least one of `user_id` or `anonymous_id` should be provided) |
| `page` | Record a page view on your website in Segment | (none — at least one of `user_id` or `anonymous_id` should be provided) |
| `screen` | Record a screen view in your mobile app in Segment | (none — at least one of `user_id` or `anonymous_id` should be provided) |
| `track` | Track an event that a user has performed in Segment | `event` |

Every tool takes an additional `write_key` parameter that the runtime fills in
from the resolved credential.

## Limits & Quotas

- **Rate limits**: Segment does not publish hard per-source rate limits for the
  Tracking API but recommends keeping requests under 500/second per source for
  optimal throughput.
- **Batch size**: Individual calls (`/track`, `/identify`, etc.) accept one
  event per request. Use the `/batch` endpoint for bulk sends (not exposed here).
- **Error model**: Non-2xx responses are caught and returned as
  `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
