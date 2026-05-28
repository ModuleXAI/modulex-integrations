# Figma

Design collaboration platform for creating, sharing, and commenting on design files via the Figma REST API (`api.figma.com`).

## Authentication

### OAuth2 Authentication

- Register an OAuth app at <https://www.figma.com/developers/apps>.
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Scopes requested: `files:read`, `file_comments:write`
- Required env vars (only when bringing your own OAuth app):
  - `FIGMA_OAUTH2_CLIENT_ID` — your Figma OAuth App Client ID
  - `FIGMA_OAUTH2_CLIENT_SECRET` — your Figma OAuth App Client Secret

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_comments` | List all comments left on a Figma file | `file_id` |
| `delete_comment` | Delete a comment from a Figma file | `file_id`, `comment_id` |
| `post_a_comment` | Post a comment to a Figma file | `file_id`, `message` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth2 credential.

## Limits & Quotas

- Figma REST API rate limit: 30 requests per minute per OAuth token (may vary by endpoint and plan).
- No per-request billing; API access is included with Figma Professional and above.
- Error model: non-2xx responses are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
