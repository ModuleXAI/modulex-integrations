# Ashby

Recruiting automation against the Ashby ATS API (`api.ashbyhq.com`):
candidates, applications, jobs, job postings, offers, notes, interview
schedules, and the organization reference data behind them.

## Authentication

One method supported — validated against `POST /apiKey.info`.

### API Key

- Sign in to Ashby as an admin and open **Settings → Integrations →
  API**.
- Create an API key and grant it the permission modules you need
  (Candidates, Jobs, Offers, Organization, Hiring Process Metadata).
  Also grant **API Keys (read)** so the credential can be validated.
- Copy the key immediately — Ashby shows it only once.
- Required env var: `ASHBY_API_KEY`.
- Ashby authenticates with HTTP Basic auth where the API key is the
  **username** and the password is **empty**, i.e.
  `Authorization: Basic <base64("<key>:")>`. Requests also send
  `Accept: application/json; version=1`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_candidates` | List candidates with cursor pagination | — |
| `get_candidate` | Fetch one candidate by ID | `candidate_id` |
| `create_candidate` | Create a candidate record | `name` |
| `update_candidate` | Update a candidate (only provided fields) | `candidate_id` |
| `search_candidates` | Search candidates by name and/or email | — |
| `list_jobs` | List jobs with status and date filters | — |
| `get_job` | Fetch one job by ID | `job_id` |
| `create_note` | Add a plain-text or HTML note to a candidate | `candidate_id`, `note` |
| `list_notes` | List a candidate's notes | `candidate_id` |
| `list_applications` | List applications with status/job/date filters | — |
| `get_application` | Fetch one application by ID | `application_id` |
| `create_application` | Apply a candidate to a job | `candidate_id`, `job_id` |
| `change_application_stage` | Move an application to another stage | `application_id`, `interview_stage_id` |
| `add_candidate_tag` | Add a tag to a candidate | `candidate_id`, `tag_id` |
| `remove_candidate_tag` | Remove a tag from a candidate | `candidate_id`, `tag_id` |
| `list_offers` | List offers with their latest version | — |
| `get_offer` | Fetch one offer by ID | `offer_id` |
| `list_sources` | List configured candidate sources | — |
| `list_candidate_tags` | List configured candidate tags | — |
| `list_archive_reasons` | List configured archive reasons | — |
| `list_custom_fields` | List custom field definitions | — |
| `list_departments` | List departments | — |
| `list_locations` | List locations | — |
| `list_job_postings` | List job postings on a job board | — |
| `get_job_posting` | Fetch one job posting by ID | `job_posting_id` |
| `list_openings` | List headcount openings | — |
| `list_users` | List organization users | — |
| `list_interviews` | List interview schedules | — |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential.

## Limits & Quotas

- **Transport**: the API is RPC-style — every action is a `POST` to
  `https://api.ashbyhq.com/<resource>.<verb>` with a JSON body, even
  for reads.
- **Response envelope**: successful calls return
  `{"success": true, "results": ...}`. Ashby answers what would
  normally be a 4XX with **HTTP 200 and `"success": false`**, so a
  failed call still returns `success=False` with the upstream API's
  `errorInfo.message`. Bad credentials return 401 and missing
  permissions return 403.
- **Permissions**: API keys are scoped per module; an action whose
  module was not granted fails with a permission error rather than an
  auth error.
- **Pagination**: list actions are cursor-based. Pass `cursor` from a
  previous response's `next_cursor` and keep going while
  `more_data_available` is true; `per_page` defaults to (and caps at)
  100. Reference-data lists also return a `sync_token` for
  incremental syncs.
- **Rate limits**: applied per API key and per endpoint family;
  exceeding them returns HTTP 429 with a `Retry-After` header. Back
  off and retry on the agent side.
- **Error model**: non-2xx responses, envelope failures and timeouts
  are caught and returned as `success=False` + `error` rather than
  raising.

## Maintainer

ModuleX core team.
