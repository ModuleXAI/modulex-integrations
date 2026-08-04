# Greenhouse

Read access to the Greenhouse applicant tracking system through its
Harvest API (`harvest.greenhouse.io/v1`): candidates, jobs,
applications, users, and the organization structure behind them —
departments, offices, and per-job interview stages.

## Authentication

One method supported — validated against `GET /v1/candidates?per_page=1`.

### API Key

- Sign in to Greenhouse as a user holding *Can manage ALL organization's
  API credentials* and open **Configure → Dev Center → API Credential
  Management**.
- Click **Create New API Key**, choose API type **Harvest**, name the
  key, and copy it right away — Greenhouse shows the full key only once.
- Click **Manage permissions** on the key and grant `GET` access to
  **Candidates**, **Jobs**, **Applications**, **Users**,
  **Departments**, **Offices** and **Job Stages**. Permissions are per
  endpoint: a key missing one of them answers `403` for that action
  only.
- Required env var: `GREENHOUSE_API_KEY`.
- Harvest authenticates with HTTP Basic auth where the API key is the
  **username** and the password is **empty**, i.e.
  `Authorization: Basic <base64("<key>:")>`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_candidates` | List candidates with date/job/email/id filters | — |
| `get_candidate` | Fetch one candidate with contact, education and employment history | `candidate_id` |
| `list_jobs` | List jobs with status, department, office and date filters | — |
| `get_job` | Fetch one job with hiring team, openings and custom fields | `job_id` |
| `list_applications` | List applications with job, status and date filters | — |
| `get_application` | Fetch one application with source, stage, answers and attachments | `application_id` |
| `list_users` | List users (recruiters, coordinators, hiring managers, admins) | — |
| `get_user` | Fetch one user by id | `user_id` |
| `list_departments` | List the organization's departments | — |
| `list_offices` | List the organization's offices | — |
| `list_job_stages` | List the interview stages configured on a job | `job_id` |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential.

## Limits & Quotas

- **Scope**: Greenhouse runs several separate APIs (Harvest, Job Board,
  Onboarding, Ingestion) on different hosts with different credentials.
  Every action here targets **Harvest** and needs a Harvest key; a Job
  Board or Onboarding key will not authenticate.
- **Transport**: all eleven actions are `GET` requests. The
  `On-Behalf-Of` header that Harvest requires on `POST`, `PATCH` and
  `DELETE` is therefore never needed.
- **Pagination**: list endpoints return a top-level JSON array and
  paginate through the RFC 5988 `Link` response header rather than a
  body cursor. `per_page` accepts 1–500 (default 100) and `page`
  selects the chunk; each response reports `next_page`, which is the
  page number of the `Link` header's `rel="next"` entry and is `null`
  on the last page. One call is always one request — pass `next_page`
  back in to advance.
- **Rate limits**: Harvest allows the number of requests in the
  `X-RateLimit-Limit` header per 10-second window and answers `429`
  with `Retry-After` when exceeded. Back off and retry on the agent
  side.
- **Attachments**: candidate and application attachment URLs are
  pre-signed and expire seven days after they are generated.
- **Error model**: non-2xx responses (`401` for a bad key, `403` for a
  missing endpoint permission), unexpected response shapes, timeouts
  and unexpected exceptions are caught and returned as `success=False`
  plus `error` rather than raising.

## Maintainer

ModuleX core team.
