# Hunter

Find and verify professional email addresses, search domains for contacts, and manage leads using the Hunter.io API (`api.hunter.io/v2`).

## Authentication

### API Key Authentication

- Sign in at <https://hunter.io> and navigate to [API Keys](https://hunter.io/api-keys).
- Copy your API key.
- Required env var: `HUNTER_API_KEY` (format: 40-character hex string).

## Tools

| name | description | required params |
| --- | --- | --- |
| `account_information` | Get information about your Hunter account | _(none)_ |
| `combined_enrichment` | Returns all the information associated with an email address and its domain name | `email` |
| `create_lead` | Create a new lead in your Hunter account | `email` |
| `delete_lead` | Delete an existing lead from your Hunter account | `lead_id` |
| `domain_search` | Search all the email addresses corresponding to one website or company | `limit` |
| `email_count` | Get the number of email addresses Hunter has for one domain or company | _(none)_ |
| `email_finder` | Find the most likely email address from a domain name, a first name and a last name | `first_name`, `last_name` |
| `email_verifier` | Check the deliverability of a given email address | `email` |
| `get_lead` | Retrieve one of your leads by ID | `lead_id` |
| `get_leads_list` | Retrieves all the fields of a leads list, including its leads | `leads_list_id`, `limit` |
| `list_leads` | List all your leads with comprehensive filtering options | `limit` |
| `list_leads_lists` | List all your leads lists, sorted with the most recent first | `limit` |
| `update_lead` | Update an existing lead in your Hunter account | `lead_id` |

Every tool takes an additional `api_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- **Free plan**: 25 searches and 50 verifications per month.
- **Paid plans**: Limits scale with plan tier (up to 30,000+ requests/month on Enterprise).
- **Rate limit**: 10 requests/second across all endpoints.
- **Error model**: Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
