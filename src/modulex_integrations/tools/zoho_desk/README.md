# Zoho Desk

Customer support help desk for reading and updating tickets, working with conversation threads and internal comments, and looking up contacts via the Zoho Desk REST API (`desk.zoho.<tld>/api/v1`).

## Authentication

### Zoho Self Client

A Self Client is Zoho's server-to-server credential: two static secrets, no browser redirect and no user consent step.

- Sign in at <https://api-console.zoho.com> and click **Add Client**.
- Choose **Self Client**, create it, then open the **Client Secret** tab and copy the **Client ID** and **Client Secret**.
- Grant the client these scopes — they are exactly what the nine tools exercise:
  `Desk.tickets.READ`, `Desk.tickets.UPDATE`, `Desk.contacts.READ`, `Desk.basic.READ`.
  (`Desk.tickets.READ`/`UPDATE` rather than `Desk.tickets.ALL`: no tool creates or deletes a ticket, and threads, comments and attachment metadata all live under the tickets module.)
- Find your Zoho Desk organization (portal) ID under **Setup > Developer Space > API**.
- Required credential settings:
  - `ZOHO_DESK_CLIENT_ID` — Client ID from Self Client > Client Secret
  - `ZOHO_DESK_CLIENT_SECRET` — Client Secret from the same tab
  - `ZOHO_DESK_ORG_ID` — organization (portal) ID; sent as the `orgId` header and used to scope the minted token
- Optional credential setting:
  - `ZOHO_DESK_DATA_CENTER` — the data-center suffix of `desk.zoho.<tld>`: `com` (default), `eu`, `in`, `com.au`, `jp`, `ca`, `sa`, `uk`, `com.cn`

Each call first exchanges the credential pair for a one-hour access token (`POST {accounts server}/oauth/v2/token` with `grant_type=client_credentials`), then calls the Desk API with `Authorization: Zoho-oauthtoken <access_token>` plus the `orgId` header. Nothing is cached between invocations, so every action is stateless: expect two HTTP round trips per call.

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_tickets` | List tickets from an organization with optional filters (department, status, priority, sort, include) | |
| `get_ticket` | Retrieve a single ticket by ID | `ticket_id` |
| `update_ticket` | Update fields on an existing ticket (subject, status, priority, assignee, category, due date, custom fields) | `ticket_id` |
| `list_comments` | List comments (internal agent notes) on a ticket | `ticket_id` |
| `add_comment` | Add a public or private comment to a ticket | `ticket_id`, `content` |
| `list_threads` | List conversation threads on a ticket, newest first | `ticket_id` |
| `get_thread` | Retrieve the full content of a single ticket thread | `ticket_id`, `thread_id` |
| `get_contact` | Retrieve a contact by ID | `contact_id` |
| `list_organizations` | List the organizations (portals) the credential can access | |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential. Every tool except `list_organizations` also takes an optional `org_id` that overrides the organization configured on the credential — useful when one Self Client can reach several portals.

Comment and thread bodies come back with a derived plain-text `content_text` alongside the raw `content`; tickets get `description_text` alongside `description`, so an agent can read a message without HTML markup. `get_ticket`, `update_ticket`, `add_comment`, `get_thread` and `get_contact` also return `raw` — the complete object exactly as the API returned it — so related records requested through `include` and any portal-specific keys are never dropped.

## Limits & Quotas

- **Rate limits**: Zoho Desk applies per-organization API credit limits that vary by edition (Standard through Enterprise); sustained polling can exhaust the daily credit pool. Budget two calls per action (token mint + API call).
- **Token lifetime**: minted access tokens are valid for one hour; Zoho also caps how many tokens a client may mint in a short window.
- **Pagination**: `list_tickets` accepts `from_index`/`limit` (max 100 per page, `from` capped at 4999); `list_threads` allows up to 200 per page.
- **Projections**: list endpoints omit heavy fields — ticket `description`/`resolution`/`status_type`/`classification` and thread bodies are only returned by the single-record tools.
- **Data residency**: tokens are minted at the accounts server for the configured data center, and the REST host follows the `api_domain` the token response carries (`desk.zoho.com`, `desk.zoho.eu`, `desk.zoho.in`, ...). Hosts are validated against Zoho's own domains before the access token is sent.
- **Error model**: non-2xx responses are caught and returned as `success=False` + `error` rather than raising; the message is taken from the API's `message`/`errorCode` when present. A rejected credential is reported from the token step, before any Desk call is made.

## Maintainer

ModuleX core team.
