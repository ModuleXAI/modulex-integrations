# Microsoft Dynamics 365 Sales

CRM platform integration for managing accounts, contacts, appointments, and custom entities via the Dynamics 365 Web API (`https://{org}.crm.dynamics.com/api/data/v9.2`).

## Authentication

### OAuth2 Authentication

- Register an app in [Microsoft Entra (Azure AD)](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade).
- Add redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required scopes: `https://dynamics.microsoft.com/user_impersonation`, `offline_access`
- Required env vars:
  - `MICROSOFT_DYNAMICS_365_SALES_OAUTH2_CLIENT_ID` (format: UUID)
  - `MICROSOFT_DYNAMICS_365_SALES_OAUTH2_CLIENT_SECRET` (sensitive)
  - `MICROSOFT_DYNAMICS_365_SALES_API_URL` — your Dynamics org hostname (e.g. `org12345.crm.dynamics.com`)

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_appointment` | Create a new appointment linked to an account with a required attendee (system user) | `subject`, `scheduledstart`, `scheduledend`, `regarding_account_id`, `required_attendee_email` |
| `create_custom_entity` | Create a custom entity definition in Dynamics 365 | `solution_id`, `display_name`, `primary_attribute` |
| `find_contact` | Search for a contact by ID, name, or custom OData filter | (all optional) |
| `get_account` | Retrieve a single account by its GUID | `account_id` |
| `list_accounts` | List accounts with optional OData filter and pagination | (all optional) |
| `list_appointment_categories` | List available appointment category values from metadata or existing rows | (none) |
| `list_appointment_category_options` | Retrieve available options for the appointment Category picklist field | (none) |
| `list_appointments` | List appointments ordered by scheduled start descending | (all optional) |
| `list_solution_id_options` | Retrieve available solutions with their IDs and names | (none) |
| `search_accounts` | Search accounts by company name substring | `search_term` |
| `update_appointment` | Update an existing appointment (only supplied fields are modified) | `appointment_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth2 credential.

## Limits & Quotas

- **API limits**: Dynamics 365 enforces per-org service protection limits (typically 6,000 requests per 5-minute sliding window per user).
- **Throttling**: Returns HTTP 429 when limits are exceeded; retry after the `Retry-After` header value.
- **Error model**: Non-2xx responses are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
