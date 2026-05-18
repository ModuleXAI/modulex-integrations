# Microsoft Excel

Read, write, and manage Excel workbooks stored in OneDrive via the
Microsoft Graph REST API (`graph.microsoft.com/v1.0`).

## Authentication

One method supported — validates against `GET /me`, fetching the
authenticated Microsoft user profile.

### Microsoft OAuth 2.0

- Register an application in **Microsoft Entra ID** (Azure AD) at
  <https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app>.
- Add the ModuleX redirect URI to the app:
  `https://api.modulex.dev/credentials/oauth2/callback`.
- Required env vars (only needed when bringing your own OAuth app):
  - `MICROSOFT_EXCEL_OAUTH2_CLIENT_ID` (format:
    `00000000-0000-0000-0000-000000000000`)
  - `MICROSOFT_EXCEL_OAUTH2_CLIENT_SECRET`
- OAuth scopes requested:
  - `Files.ReadWrite` — read and write the user's OneDrive workbooks
  - `User.Read` — used by the credential test endpoint (`/me`)
  - `offline_access` — required for refresh tokens

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_a_worksheet_tablerow` | Adds rows to the end of a specific Excel table. Provide either tableId or tableName. | `sheet_id`, `values` |
| `add_row` | Insert a new row at the end of the used range of an Excel worksheet. | `sheet_id`, `worksheet`, `values` |
| `find_row` | Find the first row in an Excel worksheet where the given column contains the given value. | `sheet_id`, `worksheet`, `column`, `value` |
| `get_columns` | Get all values in the requested columns of an Excel worksheet's used range. | `sheet_id`, `worksheet`, `columns` |
| `get_spreadsheet` | Get the values of the specified range (or the entire used range) of an Excel worksheet. | `sheet_id`, `worksheet` |
| `get_table_rows` | Retrieve all rows from a specified table in an Excel worksheet. | `sheet_id`, `table_id` |
| `list_folder_id_options` | List OneDrive folders the user can browse to pick a workbook location. | _(none)_ |
| `update_cell` | Update the value of a specific cell in an Excel worksheet. | `sheet_id`, `worksheet`, `cell`, `value` |
| `update_worksheet_tablerow` | Update the values of an existing row in an Excel workbook table (work or school accounts only). | `sheet_id`, `table_id`, `row_id`, `values` |

Every tool takes an additional `auth_type`/`auth_data` pair that the
runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- **Microsoft Graph throttling**: Graph applies per-app and per-user
  throttling. Excessive requests return HTTP `429` with a
  `Retry-After` header. See
  <https://learn.microsoft.com/en-us/graph/throttling> for current
  limits.
- **Workbook session limits**: Excel workbook APIs apply additional
  per-workbook session throttling; consider batching writes via
  `add_a_worksheet_tablerow` rather than per-cell `update_cell` calls
  when possible.
- **Table updates** (`update_worksheet_tablerow`): work or school
  Microsoft accounts only. Personal accounts cannot enumerate or
  update workbook tables.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
