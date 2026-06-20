# incident.io

Incident management and on-call response against the incident.io REST API
(`api.incident.io`). Manage incidents, actions, follow-ups, workflows,
schedules, escalations, escalation paths, custom fields, incident roles,
and reference data.

## Authentication

incident.io uses a single bring-your-own API key, sent as
`Authorization: Bearer <key>`. The credential is validated with a cheap
`GET /v1/severities` probe.

### API Key

- Log in to your incident.io dashboard and go to **Settings -> API keys**.
- Create a key, choosing the permissions (account-level and/or
  team-scoped) it should have — these can only be set at creation time.
- Copy the key (it is shown only once) and configure it as
  `INCIDENTIO_API_KEY`.

Every tool takes an additional `api_key` parameter that the runtime fills
in from the resolved credential (the modulex `api_key` injection
convention).

## Tools

| name | description | required params |
| --- | --- | --- |
| `incidents_list` | List incidents with severity/status/timestamps | — |
| `incidents_create` | Create a new incident | `idempotency_key`, `severity_id`, `visibility` |
| `incidents_show` | Get a specific incident with custom fields and roles | `id` |
| `incidents_update` | Update an incident's name/summary/severity/status/type | `id`, `notify_incident_channel` |
| `actions_list` | List actions, optionally by incident | — |
| `actions_show` | Get a specific action | `id` |
| `follow_ups_list` | List follow-ups, optionally by incident | — |
| `follow_ups_show` | Get a specific follow-up | `id` |
| `users_list` | List workspace users | — |
| `users_show` | Get a specific user | `id` |
| `workflows_list` | List workflows | — |
| `workflows_create` | Create a workflow | `name` |
| `workflows_show` | Get a specific workflow | `id` |
| `workflows_update` | Update a workflow | `id`, `name`, `steps`, `condition_groups`, `runs_on_incidents`, `runs_on_incident_modes`, `include_private_incidents`, `continue_on_step_error`, `once_for`, `expressions` |
| `workflows_delete` | Delete a workflow | `id` |
| `schedules_list` | List schedules | — |
| `schedules_create` | Create a schedule | `name`, `timezone`, `rotations_config` |
| `schedules_show` | Get a specific schedule | `id` |
| `schedules_update` | Update a schedule | `id` |
| `schedules_delete` | Delete a schedule | `id` |
| `escalations_list` | List escalations | — |
| `escalations_create` | Create an escalation | `idempotency_key`, `title` |
| `escalations_show` | Get a specific escalation | `id` |
| `custom_fields_list` | List custom fields | — |
| `custom_fields_create` | Create a custom field | `name`, `description`, `field_type` |
| `custom_fields_show` | Get a specific custom field | `id` |
| `custom_fields_update` | Update a custom field | `id`, `name`, `description` |
| `custom_fields_delete` | Delete a custom field | `id` |
| `severities_list` | List severity levels | — |
| `incident_statuses_list` | List incident statuses | — |
| `incident_types_list` | List incident types | — |
| `incident_roles_list` | List incident roles | — |
| `incident_roles_create` | Create an incident role | `name`, `description`, `instructions`, `shortform` |
| `incident_roles_show` | Get a specific incident role | `id` |
| `incident_roles_update` | Update an incident role | `id`, `name`, `description`, `instructions`, `shortform` |
| `incident_roles_delete` | Delete an incident role | `id` |
| `incident_timestamps_list` | List incident timestamp definitions | — |
| `incident_timestamps_show` | Get a specific incident timestamp | `id` |
| `incident_updates_list` | List incident updates | — |
| `schedule_entries_list` | List entries for a schedule | `schedule_id` |
| `schedule_overrides_create` | Create a schedule override | `rotation_id`, `layer_id`, `schedule_id`, `start_at`, `end_at` |
| `escalation_paths_list` | List escalation paths | — |
| `escalation_paths_create` | Create an escalation path | `name`, `path` |
| `escalation_paths_show` | Get a specific escalation path | `id` |
| `escalation_paths_update` | Update an escalation path | `id`, `name`, `path` |
| `escalation_paths_delete` | Delete an escalation path | `id` |

## Limits & Quotas

- **Rate limit**: 1200 requests/minute per API key (default).
- **Endpoints**: most resources live under `/v2`; severities, incident
  statuses, and incident types are served under `/v1`.
- **Pagination**: list endpoints accept `page_size` plus an `after`
  cursor; the tools expose both as optional parameters and do not
  auto-loop — pass the returned cursor to fetch the next page.
- **Error model**: non-2xx responses and timeouts are caught and returned
  as `success=False` + `error` rather than raising. Plan retries on the
  agent side based on the error string.

## Maintainer

ModuleX core team.
