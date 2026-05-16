# Salesforce

Salesforce CRM integration via the REST API (`v62.0`). Pure HTTP, no
SDK dep. 16 actions: SOQL/SOSL queries, generic record CRUD, and
convenience helpers for the common SObjects.

## Authentication

- **Paired `oauth2 + bearer_token` schemas.** OAuth uses Salesforce's
  Connected App flow with `api refresh_token offline_access` scopes;
  bearer is for Session IDs / manually obtained tokens.
- **`auth_data` carries two values**: `access_token` AND
  `instance_url` (Salesforce returns the per-org instance URL with
  the OAuth token exchange — each org has its own subdomain).
- OAuth env vars: `SALESFORCE_OAUTH2_CLIENT_ID`,
  `SALESFORCE_OAUTH2_CLIENT_SECRET` (both `only_for_custom`).
- Bearer env vars: `SALESFORCE_ACCESS_TOKEN`, `SALESFORCE_INSTANCE_URL`.

## Runtime convention

Token-based: every `@tool` accepts `(auth_type, auth_data, ...)`.
`_validate` enforces both `access_token` and `instance_url`.

## Tools

| group | tools |
| --- | --- |
| Query | `soql_query`, `sosl_search` |
| Generic CRUD | `get_record`, `create_record`, `update_record`, `delete_record` |
| Convenience creators | `create_account`, `create_contact`, `create_lead`, `create_opportunity`, `create_task`, `create_case` |
| Campaigns | `add_contact_to_campaign`, `add_lead_to_campaign` |
| Schema | `describe_object`, `list_objects` |

## Notes

- 30s timeout on every request.
- All actions wrap in try/except → `success=False` envelope.
- Convenience creators map Python `snake_case` params to Salesforce
  `PascalCase` field names (`first_name` → `FirstName`,
  `account_id` → `AccountId`, etc.). Custom fields pass through
  unchanged via `additional_fields`.
- `update_record` and `delete_record` accept HTTP 200 OR 204.
- `list_objects` filters to queryable objects only (matches legacy).

## Maintainer

ModuleX core team.
