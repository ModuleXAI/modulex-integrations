# Calendly

Scheduling-platform integration for Calendly: events, invitees,
event types, scheduling links, availability, organization members,
groups, and webhook subscriptions. All against `api.calendly.com`.

## Authentication

### OAuth 2.0 — and Personal Access Token

- **First post-Wave-1 integration with `oauth2 + bearer_token`** paired
  schemas (same pattern as github/slack).
- OAuth env vars: `CALENDLY_OAUTH2_CLIENT_ID`,
  `CALENDLY_OAUTH2_CLIENT_SECRET` (both `only_for_custom=True`).
- PAT env var: `CALENDLY_API_TOKEN`.
- OAuth flow:
  - `auth_url`: `https://auth.calendly.com/oauth/authorize`
  - `token_url`: `https://auth.calendly.com/oauth/token`
  - scopes: `["default"]`, body-style token auth.
- Both `test_endpoint`s hit GET `/users/me` (no quota cost).

## Runtime convention

Token-based (like github/slack): every `@tool` accepts
`(auth_type, auth_data, ...)` as its first two arguments. The modulex
runtime injects both; the local `_get_auth_headers` helper picks
`access_token` (oauth2) or `token` (bearer_token) out of `auth_data`
and builds a `Bearer …` header.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_current_user` | Authenticated user info | — |
| `list_events` | Scheduled events (filterable) | — |
| `get_event` | Single event by UUID | `event_uuid` |
| `list_event_invitees` | Invitees for one event | `event_uuid` |
| `list_event_types` | Event-type definitions | — |
| `create_scheduling_link` | Single-use booking URL | `owner` |
| `create_invitee_no_show` | Mark an invitee no-show | `invitee_uri` |
| `list_user_availability_schedules` | User availability rules | `user` |
| `list_organization_members` | Org members + roles | — |
| `list_groups` | Org groups | `organization` |
| `list_webhook_subscriptions` | Org/user webhooks | `organization`, `scope` |

## Limits & Quotas

- Auto-resolves missing `user` / `organization` filters via a side
  call to `/users/me` (same as legacy). This costs one extra request
  per call but matches Calendly's expected pattern when the operator
  doesn't pass a filter explicitly.
- Count parameters are clamped to 100 (Calendly's max page size).
- `owner` / `user` parameters accept either a bare UUID or a full
  Calendly URI; bare UUIDs are promoted to the canonical
  `https://api.calendly.com/<resource>/<uuid>` form.
- Failures (non-2xx, exceptions) surface as `success=False` + `error`.

## Maintainer

ModuleX core team.
