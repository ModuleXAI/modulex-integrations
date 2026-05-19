# Postman

API development and testing platform for building, monitoring, and managing
APIs against the Postman REST API (`api.getpostman.com`).

## Authentication

### API Key Authentication

- Sign in at <https://web.postman.co>, click your avatar, then go to
  **Settings > API Keys**.
- Generate a new API key or copy your existing one.
- Required env var: `POSTMAN_API_KEY` (format:
  `PMAK-xxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).
- Docs: <https://learning.postman.com/docs/developer/postman-api/authentication/>

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_environment` | Create a new environment in Postman with optional variables | `environment_name` |
| `list_workspace_id_options` | List available workspaces with their IDs and names | |
| `run_monitor` | Run a specific monitor in Postman | `monitor_id` |
| `update_variable` | Update a specific environment variable in Postman | `environment_id`, `variable`, `variable_value` |

Every tool takes an additional `api_key` parameter that the runtime fills in
from the resolved credential.

## Limits & Quotas

- **Free plan**: 25 requests/minute per API key.
- **Paid plans**: Higher limits; see
  <https://learning.postman.com/docs/developer/postman-api/postman-api-rate-limits/>.
- **Error model**: non-2xx responses and timeouts are caught and returned as
  `success=False` + `error` rather than raising. Plan for retries on the agent
  side based on the error string.

## Maintainer

ModuleX core team.
