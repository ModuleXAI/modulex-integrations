# PostHog

Product analytics platform integration via the PostHog REST + ingest
APIs. Pure HTTP. **78 actions** — the largest single integration in
the package.

## Authentication

- **`custom` auth_type** with three credential fields:
  `POSTHOG_API_KEY` (personal API key, sensitive),
  `POSTHOG_PROJECT_ID` (project ID), `POSTHOG_BASE_URL` (instance
  URL — `https://app.posthog.com` for cloud).
- The runtime injects all three as positional args to each `@tool`
  function. Capture/ingest actions take `project_api_key` +
  `ingest_url` instead.
- `test_endpoint` GETs `/api/projects/` and asserts `results`.

## Two API surfaces

| surface | path prefix | auth |
| --- | --- | --- |
| Project REST | `{base_url}/api/projects/{project_id}/…` | `Authorization: Bearer {api_key}` |
| Ingest | `{ingest_url}/i/v0/e/`, `/batch/`, `/flags` | `project_api_key` in JSON body |

`_call_project` and `_call_ingest` helpers wrap each.

## Action surfaces (78 total)

| group | count | sample tools |
| --- | --- | --- |
| Dashboards | 5 | `get_dashboards`, `create_dashboard`, … |
| Experiments | 6 | `create_experiment`, `get_experiment_results`, … |
| Feature flags | 5 | `create_feature_flag`, `update_feature_flag`, … |
| Insights | 5 | `create_insight`, `update_insight`, … |
| Query | 1 | `run_query` |
| Error tracking | 2 | `list_error_tracking_issues`, `get_error_tracking_issue` |
| Surveys | 5 | `create_survey`, `update_survey`, … |
| Org / projects | 2 | `get_organizations`, `get_projects` |
| Definitions | 2 | `get_event_definitions`, `get_property_definitions` |
| Capture / identify | 6 | `capture_event`, `batch_capture_events`, `identify_user`, `alias_user`, `evaluate_feature_flags`, `group_identify` |
| Persons | 5 | `get_persons`, `update_person`, `bulk_delete_persons`, … |
| Groups | 3 | `get_groups`, `find_group`, `get_group_types` |
| Cohorts | 6 | `create_cohort`, `get_cohort_persons`, … |
| Session recordings | 3 | `get_session_recordings`, `delete_session_recording`, … |
| Actions | 6 | `create_action`, `delete_action`, `delete_action_by_name`, … |
| Annotations | 5 | `create_annotation`, … |
| Alerts | 5 | `create_alert`, … |
| Early-access features | 6 | `create_early_access_feature`, `delete_early_access_feature_by_name`, … |

## Quirks preserved verbatim from legacy

- **`update_feature_flag`** takes a `flag_key` (not ID); the
  function does a search lookup first to translate it to the ID
  for the PATCH.
- **`update_experiment`** uses `start_date`/`end_date`/`conclusion`/
  `archived` field names (PostHog quirks for "launch the experiment"
  / "conclude with verdict").
- **`delete_action`** falls back to renaming the action with
  `__archived_{id}_{timestamp}__` when PostHog's soft-delete PATCH
  fails (documented upstream bug).
- **`delete_action_by_name`** does a 3-step delete chain: hard
  DELETE → soft-delete PATCH → rename PATCH. Returns success even
  if the action isn't found (legacy "nothing to do" behavior).
- **`delete_early_access_feature_by_name`** does a similar
  search-then-delete dance.
- **`evaluate_feature_flags`** uses `/flags?v=2` on the ingest URL
  (not the project REST surface).
- **`get_feature_flag`** can look up by ID OR by key (search
  endpoint with client-side filter for the exact key match).
- All actions return a unified `PostHogResult(success, error,
  result)` envelope — `result` carries the raw upstream JSON shape
  verbatim (matches legacy "return raw API data" intent).

## Notes

- 60s timeout on every request.
- No new runtime deps.

## Maintainer

ModuleX core team.
