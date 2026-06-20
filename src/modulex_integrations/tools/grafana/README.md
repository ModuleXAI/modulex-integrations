# Grafana

Manage Grafana dashboards, alert rules, annotations, contact points,
data sources, and folders, and monitor instance and data source health
against the Grafana HTTP API of your own instance.

## Authentication

Grafana is self-hostable, so a token alone is not enough — every action
also needs your instance's base URL. The runtime injects both from the
credential, so the model never has to supply the URL.

### Service Account Token

- In Grafana, open **Administration → Users and access → Service
  accounts** and create a service account with the roles your workflow
  needs (e.g. Editor or Admin).
- Add a service account token and copy the generated `glsa_...` value.
- Required env vars:
  - `GRAFANA_API_KEY` — the service account token (format:
    `glsa_xxxxxxxx..._xxxxxxxx`), sent as `Authorization: Bearer`.
  - `GRAFANA_BASE_URL` — your instance base URL (e.g.
    `https://your-grafana.com`). This is injected into each tool as the
    `base_url` parameter; the model never sets it.
- The credential is validated with `GET /api/health`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_dashboards` | Search and list all dashboards | — |
| `get_dashboard` | Get a dashboard by its UID | `dashboard_uid` |
| `create_dashboard` | Create a new dashboard | `title` |
| `update_dashboard` | Update an existing dashboard (fetch + merge) | `dashboard_uid` |
| `delete_dashboard` | Delete a dashboard by its UID | `dashboard_uid` |
| `list_alert_rules` | List all alert rules | — |
| `get_alert_rule` | Get an alert rule by its UID | `alert_rule_uid` |
| `create_alert_rule` | Create a new alert rule | `title`, `folder_uid`, `rule_group`, `data` |
| `update_alert_rule` | Update an alert rule (fetch + merge) | `alert_rule_uid` |
| `delete_alert_rule` | Delete an alert rule by its UID | `alert_rule_uid` |
| `list_contact_points` | List notification contact points | — |
| `create_contact_point` | Create a contact point (Slack, email, etc.) | `name`, `type`, `settings` |
| `create_annotation` | Create a dashboard or global annotation | `text` |
| `list_annotations` | Query annotations by time/dashboard/tags | — |
| `update_annotation` | Update an existing annotation | `annotation_id` |
| `delete_annotation` | Delete an annotation by its ID | `annotation_id` |
| `list_data_sources` | List all configured data sources | — |
| `get_data_source` | Get a data source by ID or UID | `data_source_id` |
| `check_data_source_health` | Health-check a data source by UID | `data_source_uid` |
| `list_folders` | List all folders | — |
| `create_folder` | Create a new folder | `title` |
| `get_folder` | Get a folder by its UID | `folder_uid` |
| `update_folder` | Update (rename) a folder (fetch + merge) | `folder_uid`, `title` |
| `delete_folder` | Delete a folder by its UID | `folder_uid` |
| `get_health` | Check instance health (version, database) | — |

Every tool also takes `api_key` and `base_url` parameters that the
runtime fills in from the resolved credential, plus an optional
`organization_id` to target a specific org on multi-org instances (sent
as the `X-Grafana-Org-Id` header).

## Limits & Quotas

- **Rate limits** are configured per Grafana instance; self-hosted
  instances are unbounded by default, while Grafana Cloud applies tier
  limits.
- **Update semantics**: `update_dashboard`, `update_alert_rule`, and
  `update_folder` first `GET` the current resource, merge your changes,
  and write the full body back (Grafana's update endpoints require the
  complete resource and a version for conflict detection).
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
