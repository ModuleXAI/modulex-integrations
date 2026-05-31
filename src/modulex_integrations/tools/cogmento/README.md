# Cogmento

CRM platform for managing contacts, deals, and tasks via the Cogmento REST API (`api.cogmento.com/api/1`).

## Authentication

### OAuth2 Authentication

- Connect via Cogmento's OAuth 2.0 flow (recommended).
- Register an OAuth app at Cogmento's developer portal; redirect URI must be `https://api.modulex.dev/credentials/oauth2/callback`.
- Required env vars (custom OAuth app only): `COGMENTO_OAUTH2_CLIENT_ID`, `COGMENTO_OAUTH2_CLIENT_SECRET`.
- Note: Cogmento uses a `Token` prefix (not `Bearer`) for the Authorization header.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_contact` | Create a new contact in Cogmento CRM | `first_name`, `last_name` |
| `create_deal` | Create a new deal in Cogmento CRM | `title` |
| `create_task` | Create a new task in Cogmento CRM | `title` |
| `list_user_ids_options` | Retrieve available user options for assignment fields | (none) |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- No documented rate limits from Cogmento's public API documentation.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
