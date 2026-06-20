# Findymail

Find and verify B2B emails, phones, employees, and company data against
the Findymail REST API (`app.findymail.com`).

## Authentication

### API Key

- Sign in at <https://app.findymail.com>, open the **API** page in your
  dashboard, and copy your API key.
- Required env var: `FINDYMAIL_API_KEY`.
- Requests authenticate with `Authorization: Bearer <api_key>`. The key is
  validated against `GET /api/credits`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `find_email_from_name` | Find a verified email from a name + company domain/name | `name`, `domain` |
| `find_email_from_linkedin` | Find a verified email from a LinkedIn URL/username | `linkedin_url` |
| `find_emails_by_domain` | Find verified contacts at a domain matching target roles (max 3) | `domain`, `roles` |
| `verify_email` | Verify the deliverability of an email address | `email` |
| `reverse_email_lookup` | Find a business profile from an email address | `email` |
| `get_company` | Enrich company data from LinkedIn URL, domain, or name | one of `linkedin_url`/`domain`/`name` |
| `find_employees` | Find employees by company website and job titles (no emails) | `website`, `job_titles` |
| `find_phone` | Find a phone number from a LinkedIn profile (US only) | `linkedin_url` |
| `search_technologies` | Search the technology catalog by name (free) | `q` |
| `lookup_technologies` | Get the technology stack for a company domain | `domain` |
| `get_credits` | Read remaining finder and verifier credits | — |

Every tool takes an additional `api_key` parameter that the runtime fills in
from the resolved credential.

## Limits & Quotas

- **Credits**: finder and verifier credits are consumed per successful
  lookup (e.g. verify = 1 verifier credit, find email = 1 finder credit on a
  match, find phone = 10 finder credits on a match). Use `get_credits` to
  check the remaining balance.
- **Rate limits**: `find_emails_by_domain` is limited to 5 concurrent
  synchronous requests; `search_technologies` is limited to ~10 requests per
  minute.
- **Error model**: non-2xx responses and timeouts are caught and returned as
  `success=False` + `error` rather than raising. Plan retries on the agent
  side based on the error string.

## Maintainer

ModuleX core team.
