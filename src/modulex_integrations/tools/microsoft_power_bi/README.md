# Microsoft Power BI

Business intelligence and analytics platform integration against the Power BI REST API (`api.powerbi.com/v1.0/myorg`).

## Authentication

### OAuth2 (Microsoft Entra ID)

- Register an app at [Microsoft Entra ID App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade).
- Add redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required env vars: `MICROSOFT_POWER_BI_OAUTH2_CLIENT_ID`, `MICROSOFT_POWER_BI_OAUTH2_CLIENT_SECRET`
- Scopes requested: `https://analysis.windows.net/powerbi/api/.default`, `offline_access`

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_rows_to_push_dataset` | Append rows to a table in a Power BI Push Dataset | `dataset_id`, `table_name`, `rows` |
| `execute_dax_query` | Execute a DAX query against a Power BI dataset | `dataset_id`, `query` |
| `export_report` | Export a Power BI report to PDF, PPTX, PNG, or other file format (Premium only) | `report_id` |
| `get_refresh_history` | Get the refresh history for a Power BI dataset | `dataset_id` |
| `get_reports_by_id` | Retrieve metadata for a single Power BI report by ID | `report_id` |
| `list_dashboards` | List Power BI dashboards in a workspace | |
| `list_datasets` | List Power BI datasets (semantic models) in a workspace | |
| `list_reports` | List Power BI reports in a workspace | |
| `list_workspaces` | List Power BI workspaces accessible to the authenticated user | |
| `refresh_dataset` | Trigger a refresh of a Power BI dataset | `dataset_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth2 credential.

## Limits & Quotas

- Power BI REST API is rate-limited per user/app; exact limits depend on capacity (shared vs Premium).
- Dataset refreshes: Pro allows up to 8/day; Premium allows up to 48/day.
- DAX query execution timeout: 5 minutes server-side.
- Export API: Premium-only; exports may take minutes for large reports.
- Error model: non-2xx responses are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
