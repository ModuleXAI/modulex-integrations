# Pinterest

Manage boards, board sections, and pins via the Pinterest REST API v5.

## Authentication

Two auth methods both produce a Bearer access token.

### Access Token (`api_key`)

- Env var: `PINTEREST_API_KEY` (your Pinterest OAuth access token).
- Useful when you already hold a long-lived token outside the OAuth
  dance.

### OAuth 2.0

- Env vars: `PINTEREST_OAUTH2_CLIENT_ID`, `PINTEREST_OAUTH2_CLIENT_SECRET`.
- Scopes: `boards:read`, `boards:write`, `pins:read`, `pins:write`,
  `user_accounts:read`.
- Auth URL: `https://www.pinterest.com/oauth/`
- Token URL: `https://api.pinterest.com/v5/oauth/token`

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_boards` | List user's boards | — |
| `get_board_sections` | List sections within a board | `board_id` |
| `create_pin` | Create a pin from an image URL | `board_id`, `title`, `media_url` |
| `list_pins` | List pins on a board or section | `board_id` |

## Limits & Quotas

- `page_size` is clamped to [1, 250].
- 401 → auth error; 404 → resource-not-found; 400 on create → likely
  invalid `media_url` or board id.

## Maintainer

ModuleX core team.
