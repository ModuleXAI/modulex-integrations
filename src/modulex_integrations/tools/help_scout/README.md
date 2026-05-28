# Help Scout

Customer support helpdesk platform integration against the Help Scout Mailbox API v2 (`api.helpscout.net/v2`).

## Authentication

### OAuth2 Authentication

- Register an OAuth app at the [Help Scout developer console](https://developer.helpscout.com/mailbox-api/overview/authentication/).
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required env vars (custom app only):
  - `HELP_SCOUT_OAUTH2_CLIENT_ID` — OAuth App Client ID
  - `HELP_SCOUT_OAUTH2_CLIENT_SECRET` — OAuth App Client Secret
- Help Scout does not use granular OAuth scopes; access is controlled at the app level.

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_note` | Adds a note to an existing conversation in Help Scout | `conversation_id`, `text` |
| `create_customer` | Creates a new customer record in Help Scout | _(all optional)_ |
| `get_conversation_details` | Retrieves the details of a specific conversation | `conversation_id` |
| `get_conversation_threads` | Retrieves the threads of a specific conversation | `conversation_id` |
| `get_tag_by_id` | Gets a tag by its ID | `tag_id` |
| `list_tags` | Lists all tags in Help Scout | _(none)_ |
| `send_reply` | Sends a reply to a conversation (sends an actual email to the customer) | `conversation_id`, `customer_id`, `text`, `draft` |
| `update_conversation` | Updates a conversation using a specified operation | `conversation_id`, `operation`, `value` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth2 credential.

## Limits & Quotas

- Help Scout API rate limit: 400 requests per minute per OAuth app.
- Rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Retry-After`) are returned on every response.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
