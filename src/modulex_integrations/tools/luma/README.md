# Luma

Event management platform for creating, managing, and tracking events and guests via the Luma REST API (`public-api.luma.com/v1`).

## Authentication

### API Key Authentication

- Sign in at [lu.ma](https://lu.ma) and navigate to your calendar settings or developer section.
- Generate or copy your API key.
- Required env var: `LUMA_API_KEY` (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).
- The key is sent via the `x-luma-api-key` header on every request.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_event` | Create an event on the connected Luma calendar | `name`, `start_at`, `timezone` |
| `get_event` | Get admin details for a Luma event by event ID | `event_id` |
| `list_events` | List events managed by the connected Luma calendar | |
| `get_guest` | Get detailed information for a Luma event guest by ID or email | `event_id`, `guest_id` |
| `get_guests` | List guests registered for, invited to, or waitlisted for a Luma event | `event_id` |
| `add_guests` | Add guests to a Luma event with status Going | `event_id`, `guests_json` |
| `list_ticket_types` | List ticket types for a Luma event | `event_id` |
| `send_invites` | Send email invitations for a Luma event | `event_id`, `guests_json` |

Every tool takes an additional `api_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- No documented public rate limits; Luma enforces server-side pagination maximums.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
