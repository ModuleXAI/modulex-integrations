# Railway

Manage Railway projects, services, environments, deployments, and
environment variables against Railway's public GraphQL API
(`backboard.railway.com/graphql/v2`).

## Authentication

Authenticate with a Railway API token. The `token_type` parameter on
every action selects how the token is sent: `account` (the default —
covers account, workspace, and OAuth tokens, sent as
`Authorization: Bearer`) or `project` (a project-scoped token, sent as
`Project-Access-Token`).

### API Token

- Sign in at <https://railway.com>, open **Account Settings → Tokens**,
  and create a token (account, workspace, or project scope).
- Required env var: `RAILWAY_API_TOKEN`.
- The credential is validated with a minimal viewer query
  (`{ me { name email } }`) against the GraphQL endpoint.

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_projects` | List projects visible to the token | — |
| `get_project` | Get a project with its services and environments | `project_id` |
| `create_project` | Create a project | `name` |
| `update_project` | Update a project's name or description | `project_id` |
| `delete_project` | Delete a project | `project_id` |
| `transfer_project` | Transfer a project to another workspace | `project_id`, `workspace_id` |
| `list_project_members` | List members of a project | `project_id` |
| `create_environment` | Create a project environment | `project_id`, `name` |
| `delete_environment` | Delete a project environment | `environment_id` |
| `create_service` | Create a service from a repo or Docker image | `project_id`, `name` |
| `delete_service` | Delete a service and its deployments | `service_id` |
| `list_deployments` | List deployments for a service in an environment | `project_id`, `service_id`, `environment_id` |
| `get_deployment` | Get a single deployment's details | `deployment_id` |
| `deploy_service` | Trigger a deployment for a service | `service_id`, `environment_id` |
| `restart_deployment` | Restart a running deployment | `deployment_id` |
| `rollback_deployment` | Roll a service back to a previous deployment | `deployment_id` |
| `get_deployment_logs` | Retrieve runtime logs for a deployment | `deployment_id` |
| `list_variables` | List environment variables for a service or shared env | `project_id`, `environment_id` |
| `upsert_variable` | Create or update an environment variable | `project_id`, `environment_id`, `name`, `value` |
| `delete_variable` | Delete an environment variable | `project_id`, `environment_id`, `name` |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential, plus an optional `token_type`
(`account` default, or `project`).

## Limits & Quotas

- **Transport**: every action is a single POST to the GraphQL endpoint
  `https://backboard.railway.com/graphql/v2`.
- **Rate limits**: Railway applies request-rate and complexity limits to
  the public API; see the official API docs for current values.
- **Error model**: the GraphQL endpoint answers HTTP 200 even for
  logical errors, returning them in a top-level `errors` array. These,
  along with non-2xx responses and timeouts, are caught and returned as
  `success=False` + `error` rather than raising. Plan for retries on the
  agent side based on the error string.

## Maintainer

ModuleX core team.
