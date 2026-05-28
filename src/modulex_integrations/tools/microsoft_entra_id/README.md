# Microsoft Entra ID

Identity and access management via the Microsoft Graph API (`graph.microsoft.com/v1.0`) for managing users, groups, and directory objects in Microsoft Entra ID (formerly Azure Active Directory).

## Authentication

### OAuth2 Authentication

- Register an app at the [Azure Portal App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade).
- Add redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required env vars (only when bringing your own OAuth app):
  - `MICROSOFT_ENTRA_ID_OAUTH2_CLIENT_ID` (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
  - `MICROSOFT_ENTRA_ID_OAUTH2_CLIENT_SECRET`
- Scopes requested: `User.Read`, `User.ReadWrite.All`, `Group.ReadWrite.All`, `GroupMember.ReadWrite.All`, `Directory.ReadWrite.All`

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_member_to_group` | Add a user as a member to a Microsoft Entra ID group. | `group_id`, `user_id` |
| `create_group` | Create a new group in Microsoft Entra ID. | `display_name`, `mail_enabled`, `mail_nickname`, `security_enabled` |
| `delete_group` | Delete a group in Microsoft Entra ID. | `group_id` |
| `get_manager` | Get the user's manager information. | — |
| `get_ms365_groups` | Get the user's Microsoft 365 groups (unified groups). | — |
| `get_organization_groups` | List all groups in the organization. | — |
| `get_organization_users` | List all users in the organization. | — |
| `get_profile` | Get the user's profile information from Microsoft Entra ID. | — |
| `remove_member_from_group` | Remove a member from a Microsoft Entra ID group. | `group_id`, `user_id` |
| `search_groups` | Search for groups by name or description. | `query` |
| `update_group` | Update an existing group in Microsoft Entra ID. | `group_id` |
| `update_user` | Update an existing user in Microsoft Entra ID. | `user_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth2 credential.

## Limits & Quotas

- **Microsoft Graph throttling**: Varies by resource and tenant; typically 10,000 requests per 10 minutes per app per tenant for most directory endpoints.
- **Pagination**: List endpoints may return paginated results; the integration follows `@odata.nextLink` automatically.
- **Error model**: Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
