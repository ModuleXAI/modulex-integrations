# Medium

Publish posts to Medium via the Medium REST API (`api.medium.com/v1`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth application at <https://medium.com/me/applications>.
- Set the callback URL to `https://api.modulex.dev/credentials/oauth2/callback`.
- Required env vars (only when bringing your own OAuth app):
  - `MEDIUM_OAUTH2_CLIENT_ID` — your Medium OAuth App Client ID.
  - `MEDIUM_OAUTH2_CLIENT_SECRET` — your Medium OAuth App Client Secret.
- Scopes requested: `basicProfile`, `publishPost`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_post` | Create a new Medium post. | `title`, `content_format`, `content` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential. The `auth_data` includes `oauth_uid` (the authenticated user's Medium ID) which is required to construct the API endpoint.

## Limits & Quotas

- Medium's public API has no officially documented rate limits.
- The API has been in a limited/deprecated state since approximately 2023; some endpoints may have restricted functionality.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
