# Google AppSheet

Manage rows in Google AppSheet tables (add, read, update, delete) via the
AppSheet REST API (`api.appsheet.com`).

## Authentication

### AppSheet API Key

- Open your app in [AppSheet](https://www.appsheet.com), go to
  **Settings > Integrations > IN: from cloud services to your app**.
- Enable the API and copy the **Application Access Key**.
- Copy the **App ID** from the URL or **Settings > App Info**.
- Required env vars:
  - `GOOGLE_APPSHEET_APP_ID` (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
  - `GOOGLE_APPSHEET_API_KEY` (format: `V2-xxxxx-xxxxx-xxxxx-xxxxx-xxxxx`)

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_row` | Add a new row to a specific table in the AppSheet app | `table_name`, `row` |
| `delete_row` | Delete a specific row from a table in the AppSheet app | `table_name` |
| `get_rows` | Read existing records from a table in the AppSheet app | `table_name` |
| `update_row` | Update an existing row in a specific table in the AppSheet app | `table_name`, `row` |

Every tool takes additional `app_id` and `api_key` parameters that the runtime
fills in from the resolved credential.

## Limits & Quotas

- AppSheet API has no publicly documented per-minute rate limits, but Google
  recommends keeping request volume moderate for shared-tenant apps.
- Each app must have the API enabled in Settings > Integrations.
- Error model: non-2xx responses and timeouts are caught and returned as
  `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
