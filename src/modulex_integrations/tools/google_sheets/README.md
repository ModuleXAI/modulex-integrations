# Google Sheets

Read, write, and manage Google Sheets spreadsheets and worksheets via the Google
Sheets API v4 (`https://sheets.googleapis.com/v4`) and the Drive API v3
(`https://www.googleapis.com/drive/v3`) for spreadsheet listing.

## Authentication

### OAuth2 Authentication

- Create an OAuth client in the [Google Cloud Console — Credentials](https://console.cloud.google.com/apis/credentials).
- Add the redirect URI `https://api.modulex.dev/credentials/oauth2/callback` to
  the OAuth client's authorized URIs.
- Enable both the **Google Sheets API** and the **Google Drive API** for the
  project (the Drive scope is required for `list_spreadsheets`).
- Required env vars:
  - `GOOGLE_SHEETS_OAUTH2_CLIENT_ID` (format: `<digits>.apps.googleusercontent.com`)
  - `GOOGLE_SHEETS_OAUTH2_CLIENT_SECRET` (format: `GOCSPX-...`)
- Scopes requested:
  - `https://www.googleapis.com/auth/spreadsheets`
  - `https://www.googleapis.com/auth/drive.file`
  - `https://www.googleapis.com/auth/drive.readonly`

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_spreadsheets` | List Google Spreadsheets accessible to the authenticated user (search by name optional). | _none_ |
| `new_spreadsheet` | Create a new spreadsheet, optionally with a first-worksheet name and header row. | `title` |
| `get_spreadsheet_info` | Inspect a spreadsheet — worksheet names, sheet IDs, row counts, and headers. | `spreadsheet_id` |
| `list_worksheets` | List all worksheets (tabs) in a spreadsheet. | `spreadsheet_id` |
| `add_worksheet` | Add a new worksheet (tab) and optionally seed headers. | `spreadsheet_id`, `title` |
| `delete_worksheet` | Delete a worksheet by its numeric sheet ID. | `spreadsheet_id`, `worksheet_id` |
| `read_rows` | Read rows from a worksheet; returns objects keyed by header row by default. | `spreadsheet_id`, `sheet_name` |
| `get_values_in_range` | Get raw cell values from a worksheet range (list of lists). | `spreadsheet_id`, `sheet_name` |
| `find_rows` | Search a column for a value (`exact`, `contains`, or `starts_with`). | `spreadsheet_id`, `sheet_name`, `column`, `search_value` |
| `add_rows` | Append rows to a worksheet. Accepts arrays of values or objects keyed by header. | `spreadsheet_id`, `sheet_name`, `rows` |
| `update_row` | Overwrite a row with a positional list of values. | `spreadsheet_id`, `sheet_name`, `row`, `values` |
| `update_cell` | Update a single cell by A1 notation. | `spreadsheet_id`, `sheet_name`, `cell`, `value` |
| `clear_rows` | Clear values in a row range (rows remain, but become blank). | `spreadsheet_id`, `sheet_name`, `start_index` |
| `delete_rows` | Permanently delete a row range from a worksheet. | `spreadsheet_id`, `worksheet_id`, `start_index` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the user's stored OAuth credential.

## Limits & Quotas

- Google Sheets API default quota: 300 read requests / minute / project and 300
  write requests / minute / project (with a 60 / minute / user cap for both).
- Google Drive API default quota: 12,000 queries / minute / user.
- Cell-value writes use `valueInputOption=USER_ENTERED`, so values are parsed as
  if a user typed them in the UI (numbers/dates/booleans get coerced).
- `add_rows` uses `insertDataOption=INSERT_ROWS`, so it never overwrites
  existing data — new rows are inserted after the last row containing data.
- Non-2xx responses are caught and returned as `success=False` + `error` with
  the API `error.message` (when present).
- Timeouts surface as `success=False` with `error="Request timed out."`.

## Maintainer

ModuleX core team.
