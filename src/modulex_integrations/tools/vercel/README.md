# Vercel

Manage Vercel deployments, projects, domains, DNS records, environment
variables, aliases, edge configs, teams, webhooks, and deployment checks
through the Vercel REST API (`api.vercel.com`).

## Authentication

One method is supported: a personal Vercel Access Token, validated
against `GET /v2/user`.

### API Key (Vercel Access Token)

- Sign in at <https://vercel.com>, open **Account Settings → Tokens**.
- Click **Create Token**, give it a name and (recommended) an
  expiration, then copy the token — it is shown only once.
- Required env var: `VERCEL_API_KEY`.

The token is sent as `Authorization: Bearer <token>`. Every tool takes
an additional `api_key` parameter that the runtime fills in from the
resolved credential (the modulex `api_key` injection convention).

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_deployments` | List deployments for a project or team | — |
| `get_deployment` | Get a deployment's details | `deployment_id` |
| `create_deployment` | Create a deployment or redeploy | `name` |
| `cancel_deployment` | Cancel a running deployment | `deployment_id` |
| `delete_deployment` | Delete a deployment | `deployment_id` |
| `get_deployment_events` | Get build/runtime events | `deployment_id` |
| `list_deployment_files` | List deployment file-tree metadata | `deployment_id` |
| `promote_deployment` | Promote a deployment to production | `project_id`, `deployment_id` |
| `list_projects` | List projects | — |
| `get_project` | Get a project's details | `project_id` |
| `create_project` | Create a project | `name` |
| `update_project` | Update a project | `project_id` |
| `delete_project` | Delete a project | `project_id` |
| `pause_project` | Pause a project | `project_id` |
| `unpause_project` | Unpause a project | `project_id` |
| `list_project_domains` | List a project's domains | `project_id` |
| `add_project_domain` | Add a domain to a project | `project_id`, `domain` |
| `update_project_domain` | Update a project domain's config | `project_id`, `domain` |
| `verify_project_domain` | Verify a project domain | `project_id`, `domain` |
| `remove_project_domain` | Remove a domain from a project | `project_id`, `domain` |
| `get_env_vars` | List project environment variables | `project_id` |
| `create_env_var` | Create an environment variable | `project_id`, `key`, `value`, `target` |
| `update_env_var` | Update an environment variable | `project_id`, `env_id` |
| `delete_env_var` | Delete an environment variable | `project_id`, `env_id` |
| `list_domains` | List account/team domains | — |
| `get_domain` | Get a domain's details | `domain` |
| `add_domain` | Add a domain to the account/team | `name` |
| `delete_domain` | Delete a domain | `domain` |
| `get_domain_config` | Get a domain's DNS/TLS config | `domain` |
| `list_dns_records` | List a domain's DNS records | `domain` |
| `create_dns_record` | Create a DNS record | `domain`, `record_name`, `record_type`, `value` |
| `update_dns_record` | Update a DNS record | `record_id` |
| `delete_dns_record` | Delete a DNS record | `domain`, `record_id` |
| `list_aliases` | List aliases | — |
| `get_alias` | Get an alias by ID/hostname | `alias_id` |
| `create_alias` | Assign an alias to a deployment | `deployment_id`, `alias` |
| `delete_alias` | Delete an alias | `alias_id` |
| `list_edge_configs` | List Edge Config stores | — |
| `get_edge_config` | Get an Edge Config store | `edge_config_id` |
| `create_edge_config` | Create an Edge Config store | `slug` |
| `get_edge_config_items` | List items in an Edge Config | `edge_config_id` |
| `update_edge_config_items` | Create/update/upsert/delete items | `edge_config_id`, `items` |
| `delete_edge_config` | Delete an Edge Config store | `edge_config_id` |
| `list_webhooks` | List webhooks | — |
| `get_webhook` | Get a webhook | `webhook_id` |
| `create_webhook` | Create a webhook | `url`, `events` |
| `delete_webhook` | Delete a webhook | `webhook_id` |
| `create_check` | Create a deployment check | `deployment_id`, `name`, `blocking` |
| `get_check` | Get a deployment check | `deployment_id`, `check_id` |
| `list_checks` | List deployment checks | `deployment_id` |
| `update_check` | Update a deployment check | `deployment_id`, `check_id` |
| `rerequest_check` | Rerequest a deployment check | `deployment_id`, `check_id` |
| `list_teams` | List teams | — |
| `get_team` | Get a team | `team_id` |
| `list_team_members` | List team members | `team_id` |
| `get_user` | Get the authenticated user | — |

Most tools also accept an optional `team_id` to scope the request to a
specific Vercel team.

## Limits & Quotas

- **Rate limits**: the Vercel REST API enforces per-endpoint rate
  limits; on `429` the response carries a `Retry-After` header. Plan
  for retries on the agent side based on the error string.
- **API versioning**: each endpoint pins its own version in the path
  (e.g. `/v13/deployments`, `/v9/projects`, `/v2/teams`,
  `/v1/edge-config`); these are preserved as documented by Vercel.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
