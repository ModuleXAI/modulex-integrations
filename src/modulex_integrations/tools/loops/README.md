# Loops

Manage contacts and send emails with Loops. Create and manage contacts,
send transactional emails, and trigger event-based automations against
the Loops REST API (`app.loops.so/api/v1`).

## Authentication

### API Key

- Log in to your Loops account at <https://app.loops.so>.
- Go to **Settings > API** and create a new API key (or copy an
  existing one).
- Required env var: `LOOPS_API_KEY`.
- The key is sent as `Authorization: Bearer <api_key>` on every
  request. The credential is validated against `GET /v1/lists`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_contact` | Create a new contact with email and optional properties | `email` |
| `update_contact` | Update (or upsert) a contact by email or user_id | one of `email`/`user_id` |
| `find_contact` | Look up contacts by email or user_id | one of `email`/`user_id` |
| `delete_contact` | Delete a contact by email or user_id | one of `email`/`user_id` |
| `send_transactional_email` | Send a templated transactional email | `email`, `transactional_id` |
| `send_event` | Fire an event to trigger automated email sequences | `event_name`, one of `email`/`user_id` |
| `list_mailing_lists` | List all mailing lists | — |
| `list_transactional_emails` | List published transactional email templates | — |
| `create_contact_property` | Create a custom contact property (camelCase name) | `name`, `type` |
| `list_contact_properties` | List contact properties (all or custom only) | — |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential (the modulex `api_key` injection
convention).

## Limits & Quotas

- Loops applies per-account API rate limits; check your plan in the
  Loops dashboard for current values.
- `list_transactional_emails` accepts `per_page` (10-50, default 20)
  and a `cursor` for pagination; the response carries a `pagination`
  block with `next_cursor`/`next_page` for fetching subsequent pages.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Mutating
  endpoints also return HTTP 200 with `{"success": false, "message":
  ...}` for business-logic failures, which is surfaced as `error`.

## Maintainer

ModuleX core team.
