# ServiceNow

Enterprise ITSM integration for ServiceNow: Trouble Ticket API for
incidents/cases, Table API for full CRUD on any ServiceNow table.
Targets per-tenant instances at `https://{instance_name}.service-now.com`.

## Authentication

### OAuth 2.0 (Connected App) — and bearer_token Access Token

- **Paired `oauth2 + bearer_token` schemas.** Both share the same
  `instance_name` env var; OAuth uses `client_id` + `client_secret`,
  bearer uses a pre-obtained access token.
- OAuth env vars: `SERVICENOW_CLIENT_ID`, `SERVICENOW_CLIENT_SECRET`,
  `SERVICENOW_INSTANCE_NAME`.
- Bearer env vars: `SERVICENOW_ACCESS_TOKEN`, `SERVICENOW_INSTANCE_NAME`.
- OAuth endpoints use `{instance_name}` substitution:
  `https://{instance_name}.service-now.com/oauth_auth.do` and
  `/oauth_token.do`.
- Tool code reads the token from either `access_token` (oauth2) or
  `token` (bearer_token) in `auth_data` — both are accepted with one
  code path.

## Runtime convention

Token-based (like github/slack/calendly): every `@tool` accepts
`(auth_type, auth_data, ...)` as its first two arguments. The
ServiceNow `_validate` helper ensures both the token and
`instance_name` are present before any HTTP call.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_case` | Customer-service Case via Trouble Ticket API | `description`, `severity` |
| `create_incident` | ITSM Incident via Trouble Ticket API | `description`, `severity` |
| `create_table_record` | Insert into any table | `table_name`, `table_record` |
| `get_table_record` | One record by sys_id | `table_name`, `sys_id` |
| `get_table_records` | List records with filters | `table_name` |
| `update_table_record` | PATCH semantics | `table_name`, `sys_id`, `update_fields` |
| `delete_table_record` | Delete by sys_id (irreversible) | `table_name`, `sys_id` |

## Limits & Quotas

- The Trouble Ticket API hits the
  `/api/sn_ind_tsm_sdwan/ticket/troubleTicket` plugin endpoint —
  requires that plugin to be installed in the ServiceNow instance.
- Table API supports versioning via `api_version` ('v1', 'v2', or
  'latest' / unspecified for default). The tool builds the path as
  `/api/now/[v1|v2|]table/<table>`.
- `display_value` / `exclude_reference_link` / `view` / `fields` /
  pagination knobs are translated to ServiceNow's `sysparm_*` query
  string conventions.
- Default page limit is 10000 records (Table API default).
- Instance name parsing: bare name (`dev12345`), full hostname
  (`dev12345.service-now.com`), and full URL
  (`https://dev12345.service-now.com`) are all accepted.

## Maintainer

ModuleX core team.
