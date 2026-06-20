# Resend

Send transactional and marketing emails, retrieve email status, manage
contacts, and view domains via the Resend REST API (`api.resend.com`).

## Authentication

One method supported — validated against `GET /domains` with the API key.

### API Key

- Sign in at <https://resend.com>, open the **API Keys** section, and
  create a new key (it starts with `re_`).
- Required env var: `RESEND_API_KEY` (format:
  `re_xxxxxxxxxxxxxxxxxxxxxxxxx`).
- The key is sent as `Authorization: Bearer <api_key>` on every request.

## Tools

| name | description | required params |
| --- | --- | --- |
| `send` | Send an email (plain text or HTML) | `from_address`, `to`, `subject`, `body` |
| `get_email` | Retrieve a previously sent email by ID | `email_id` |
| `create_contact` | Create a new contact | `email` |
| `list_contacts` | List all contacts | — |
| `get_contact` | Retrieve a contact by ID or email | `contact_id` |
| `update_contact` | Update an existing contact | `contact_id` |
| `delete_contact` | Delete a contact by ID or email | `contact_id` |
| `list_domains` | List all domains in the account | — |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential.

## Limits & Quotas

- **Rate limit**: 2 requests/second by default (Resend account level).
- **Scheduling**: emails can be scheduled up to 30 days ahead via
  `scheduled_at` (ISO 8601 timestamp).
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
