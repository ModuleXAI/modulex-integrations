# Reflect

Note-taking and knowledge management via the Reflect API (`reflect.app/api`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth app at the [Reflect developer console](https://reflect.app/developer).
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Required env vars (only for custom OAuth app):
  - `REFLECT_OAUTH2_CLIENT_ID` (Client ID)
  - `REFLECT_OAUTH2_CLIENT_SECRET` (Client Secret, sensitive)
- No specific scopes documented by the provider.

## Tools

| name | description | required params |
| --- | --- | --- |
| `append_daily_note` | Append to a daily note | `graph_id`, `text` |
| `create_link` | Create a new link | `graph_id`, `url` |
| `get_user` | Retrieves information about the authenticated user | |
| `list_graph_id_options` | Retrieves available options for the GraphId field | |
| `list_links` | Retrieve all links for a graph | `graph_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- No documented rate limits from the Reflect API.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
