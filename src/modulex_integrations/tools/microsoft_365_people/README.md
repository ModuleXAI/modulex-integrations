# Microsoft 365 People

Manage contacts and contact folders via the Microsoft Graph API (`graph.microsoft.com/v1.0`).

## Authentication

### OAuth2 Authentication

- Register an app in the [Azure Portal](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) under App registrations.
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required scopes: `Contacts.ReadWrite`, `User.Read`, `offline_access`
- Required env vars (custom OAuth app only):
  - `MICROSOFT_365_PEOPLE_OAUTH2_CLIENT_ID` (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
  - `MICROSOFT_365_PEOPLE_OAUTH2_CLIENT_SECRET`

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_contact` | Create a new contact in Microsoft 365 People | `email`, `first_name` |
| `create_contact_folder` | Create a new contact folder in Microsoft 365 People | `display_name` |
| `update_contact` | Update an existing contact in Microsoft 365 People | `contact_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth2 credential.

## Limits & Quotas

- Microsoft Graph API throttling: 10,000 requests per 10 minutes per app per tenant.
- Per-mailbox limits: 4 concurrent connections.
- Error model: non-2xx responses raise `httpx.HTTPStatusError` (Pattern A).

## Maintainer

ModuleX core team.
