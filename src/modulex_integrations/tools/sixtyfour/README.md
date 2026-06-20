# Sixtyfour AI

AI-powered contact discovery and lead/company enrichment against the
Sixtyfour AI REST API (`api.sixtyfour.ai`). Find verified emails and
phone numbers for a prospect, and turn thin lead or company records
into researched profiles with structured data, source references, and a
confidence score.

## Authentication

### API Key

- Sign up or log in at <https://app.sixtyfour.ai>, open your account
  settings, and create or copy an API key.
- Required env var: `SIXTYFOUR_API_KEY`.
- The key is sent on every request in the `x-api-key` header. The
  runtime fills in the `api_key` parameter from the resolved credential
  (the `api_key` injection convention, **not** the `auth_type`/`auth_data`
  pair used by github and slack).
- Credential validation hits `POST /find-email` with a minimal probe
  request.

## Tools

| name | description | required params |
| --- | --- | --- |
| `find_phone` | Find phone number(s) for a lead | `name` |
| `find_email` | Find professional/personal email addresses for a lead | `name` |
| `enrich_lead` | Enrich a lead into a researched profile from a JSON struct | `lead_info`, `struct` |
| `enrich_company` | Enrich a company and optionally discover associated people | `target_company`, `struct` |

For `enrich_lead` and `enrich_company`, `lead_info`/`target_company` and
`struct` accept either a JSON object or a JSON string; `struct` maps each
output field name to a natural-language description of what to collect.

## Limits & Quotas

- **Enrichment is long-running.** `enrich_lead` and `enrich_company`
  perform deep research — typical P95 runtime is ~5 minutes and can reach
  ~10 minutes for complex records. The client timeout for these tools is
  set to 15 minutes; `find_email`/`find_phone` use a 2-minute timeout.
- **Credit usage scales with the requested struct.** Request only the
  fields you need to keep credit consumption down.
- **Error model**: non-2xx responses and timeouts are caught and returned
  as `success=False` + `error` rather than raising. Plan retries on the
  agent side based on the error string.

## Maintainer

ModuleX core team.
