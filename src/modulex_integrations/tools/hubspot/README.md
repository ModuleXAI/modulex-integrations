# HubSpot

HubSpot CRM integration via the **synchronous** `hubspot-api-client`
SDK. 26 actions across contacts, companies, deals, tickets, plus
engagement (note/task/meeting) and property management.

## Authentication

- **Paired `oauth2 + bearer_token` schemas.** OAuth covers
  HubSpot's standard CRM scopes (contacts/companies/deals/tickets,
  read+write). Bearer is for Private App access tokens.
- OAuth env vars: `HUBSPOT_OAUTH2_CLIENT_ID`,
  `HUBSPOT_OAUTH2_CLIENT_SECRET` (both `only_for_custom`).
- Bearer env var: `HUBSPOT_ACCESS_TOKEN`.

## Runtime convention

Token-based: every `@tool` accepts `(auth_type, auth_data, ...)`.
Token chosen from `auth_data["access_token"]` (oauth2) or
`auth_data["token"]` (bearer_token) inside the SDK client factory.

## Tools

| group | tools |
| --- | --- |
| Contacts | `get_recent_contacts`, `get_contact_by_id`, `create_contact`, `update_contact`, `search_contacts` |
| Companies | `get_recent_companies`, `get_company_by_id`, `create_company`, `update_company`, `get_company_activity`, `search_companies` |
| Deals | `get_recent_deals`, `get_deal_by_id`, `create_deal`, `update_deal`, `search_deals` |
| Tickets | `get_recent_tickets`, `get_ticket_by_id`, `create_ticket`, `update_ticket`, `search_tickets` |
| Engagements | `create_note`, `create_task`, `create_meeting` |
| Schema | `get_property`, `list_properties` |

## Notes

- **Sync SDK in async tools** — preserved verbatim from legacy.
  Calls into `hubspot-api-client` block the event loop. Improving
  to httpx is deferred to a future wave.
- **`get_company_activity` does N+1 fetches**: list engagement IDs
  via the v4 associations API, then GET each engagement detail by
  ID. Matches legacy. Per-engagement failures are silently dropped.
- All actions wrap SDK calls in `try/except` → `success=False`
  envelope (legacy raised; this migration normalizes to our
  envelope contract).
- Engagement association type IDs are hard-coded constants from
  HubSpot's documented schema (note→contact=202, note→company=190,
  etc.). Defined in `_ENGAGEMENT_ASSOC_IDS` for clarity.
- `hubspot-api-client` is lazy-imported inside `_client()` so the
  manifest can be inspected without the SDK installed.

## Maintainer

ModuleX core team.
