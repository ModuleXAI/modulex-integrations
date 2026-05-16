# AppDrag

Cloud backend integration for AppDrag: invoke custom API functions and
run INSERT/UPDATE statements against the project's cloud database via
`api.appdrag.com/CloudBackend.aspx`.

## Authentication

### API Key + App ID

- Required env vars: `APPDRAG_API_KEY` (secret), `APPDRAG_APP_ID`.
- Find both in your AppDrag project settings —
  <https://support.appdrag.com/doc/Get-your-API-Key>.
- Sent as `APIKey` + `appID` form fields, never as headers. Functions
  go to `{app_id}.appdrag.site/api{path}`; DB queries go to the
  backend `.aspx` URL.

## Tools

| name | description | required params |
| --- | --- | --- |
| `execute_api_function` | Call a cloud function on your app | `path` |
| `insert_row` | INSERT INTO `table` | `table`, `columns`, `values` |
| `update_row` | UPDATE `table` WHERE … | `table`, `columns_to_update`, `values`, `where_condition`, `where_values` |

## Limits & Quotas

- `insert_row` / `update_row` build raw SQL strings and pass them via
  the `CloudDBExecuteRawQuery` command — quoting matches the legacy
  implementation (single-quote escaping by doubling). Pre-flight
  validation rejects length-mismatched columns/values or `?`
  placeholder counts.
- `update_row` requires a non-empty `where_condition` to avoid
  accidental full-table updates.

## Maintainer

ModuleX core team.
