# Revolt

Open-source chat platform for group management and social features via the Revolt REST API (`revolt.chat/api`).

## Authentication

### Session Token

- Obtain your session token from the Revolt client (inspect network requests or use the bot token from your Revolt bot settings).
- Required env var: `REVOLT_SESSION_TOKEN` (format: session token string).
- The token is sent as the `x-session-token` header on every request.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_group` | Create a new group channel | `name` |
| `add_group_member` | Add another user to a group channel | `target`, `member` |
| `send_friend_request` | Send a friend request to another user | `username` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential.

## Limits & Quotas

- No officially documented rate limits for the Revolt API.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
