# Gamma

Generate presentations, documents, webpages, and social posts with AI
from text, create from templates, check generation status, and browse
workspace themes and folders against the Gamma REST API
(`public-api.gamma.app`).

## Authentication

### API Key

- Requires a Gamma Pro, Ultra, Teams, or Business plan.
- Open **Account Settings > API Keys**, then create or copy a key
  (format: `sk-gamma-xxxxxxxx`).
- Required env var: `GAMMA_API_KEY`.
- The key is sent on every request as the `X-API-KEY` header. The
  runtime fills the `api_key` parameter from the resolved credential.

## Tools

| name | description | required params |
| --- | --- | --- |
| `generate` | Generate a presentation, document, webpage, or social post from text | `input_text`, `text_mode` |
| `generate_from_template` | Adapt an existing template gamma with a prompt | `gamma_id`, `prompt` |
| `check_status` | Poll a generation job and retrieve the final gamma URL | `generation_id` |
| `list_themes` | List workspace themes with IDs, names, and keywords | — |
| `list_folders` | List workspace folders with IDs and names | — |

Generation is asynchronous: `generate` and `generate_from_template`
return a `generation_id`; poll `check_status` with it until `status`
is `completed` (which yields `gamma_url` and, if requested, `export_url`)
or `failed`.

## Limits & Quotas

- API key access requires a paid plan (Pro, Ultra, Teams, or Business).
- Generation cost is metered in credits; `check_status` reports
  `credits.deducted` and `credits.remaining` on completion.
- `list_themes` and `list_folders` cap `limit` at 50 per page and use a
  `next_cursor` cursor (pass it as `after`) for further pages.
- Every response carries rate-limit headers
  (`x-ratelimit-remaining`, `x-ratelimit-remaining-daily`).
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
