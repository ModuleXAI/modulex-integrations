# Netlify

Web hosting and automation platform for modern web projects, interfacing with the Netlify REST API (`api.netlify.com/api/v1`).

## Authentication

### OAuth2 Authentication

- Register an OAuth application at <https://app.netlify.com/user/applications>.
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required env vars (only when using your own OAuth app):
  - `NETLIFY_OAUTH2_CLIENT_ID` — your OAuth App Client ID
  - `NETLIFY_OAUTH2_CLIENT_SECRET` — your OAuth App Client Secret
- Netlify OAuth does not use granular scopes; the access token grants full account access.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_site` | Get a specified site by its ID | `site_id` |
| `list_files` | Returns a list of all the files in the current deploy for a site | `site_id` |
| `list_site_deploys` | Returns a list of all deploys for a specific site | `site_id` |
| `rollback_deploy` | Restores an old deploy and makes it the live version of the site | `site_id`, `deploy_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- Netlify API rate limit: 500 requests per minute per access token (as documented by Netlify).
- Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.
- Deploy operations (rollback) may take a few seconds to propagate.

## Maintainer

ModuleX core team.
