# Flint

Run background agent tasks on your Flint sites: modify a site from a
natural-language prompt, generate a batch of pages from a template page,
and read back the status and resulting page URLs — over the Flint Agent
Tasks API (`app.tryflint.com/api/v1`).

## Authentication

### API Key

- Log in at <https://app.tryflint.com> and open **team settings**
  (<https://app.tryflint.com/app/team>) to create an API key. Creating a
  key requires at least the member role, and the key is scoped to your
  organization.
- Required env var: `FLINT_API_KEY` (format: `ak_...`).
- The key is sent as `Authorization: Bearer <api_key>`. No credential
  test endpoint is configured — the published API surface only creates
  and reads agent tasks, so there is no side-effect-free probe; an
  invalid key surfaces on the first action call as a `success=False`
  result.

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential (the modulex `api_key` injection
convention, not the `auth_type`/`auth_data` pair).

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_task` | Start an agent task that modifies a site from a prompt | `site_id`, `prompt` |
| `generate_pages` | Start an agent task that generates up to 10 pages from a template page | `site_id`, `template_page_slug`, `items` |
| `get_task` | Read a task's status plus its created/modified/deleted pages | `task_id` |

Tasks run in the background. `create_task` and `generate_pages` return
as soon as Flint accepts the job — the response carries `task_id`,
`status` (`running`), and `created_at`, not the finished pages. Poll
`get_task` with that id until `status` is `completed` (page URLs in
`pages_created` / `pages_modified` / `pages_deleted`) or `failed`
(reason in `error_message`). Both creation tools also accept
`callback_url`, an HTTPS endpoint Flint POSTs the terminal result to on
its own.

## Limits & Quotas

- All calls go to `https://app.tryflint.com/api/v1` over HTTPS with a
  30s client timeout (which bounds the *request*, not the agent task).
- `generate_pages` accepts **1–10 items** per task; each item needs a
  string `targetPageSlug` and a string `context`. The array may also be
  passed as a JSON string. Violations are rejected locally before the
  request is sent.
- `publish` is only forwarded when explicitly set, so leaving it out
  preserves Flint's server-side default; setting it to `true` triggers a
  production deployment when the task completes.
- `callback_url` must be HTTPS and publicly reachable — Flint rejects
  internal/private addresses with a 400, and retries delivery up to 3
  times with exponential backoff.
- The Agent Tasks endpoints are rate limited; exceeding the limit
  returns `429 Too Many Requests`.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. The API's
  `error` payload is unwrapped into the error string, and a 2xx body
  with no `taskId` is treated as a failure as well.

## Maintainer

ModuleX core team.
