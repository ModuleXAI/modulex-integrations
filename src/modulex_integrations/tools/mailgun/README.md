# Mailgun

Transactional email API integration for sending, receiving, and tracking email via the Mailgun REST API (`api.mailgun.net`).

## Authentication

### Mailgun API Key

- Log in at <https://app.mailgun.com> and go to **Settings > API Security**.
- Copy your **Private API key**.
- Required env var: `MAILGUN_API_KEY` (format: `key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).
- Optional env var: `MAILGUN_REGION` — set to `EU` if your Mailgun account is on EU infrastructure; defaults to `US`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `send_email` | Send an email via Mailgun | `domain`, `from_name`, `from_email`, `to`, `subject` |
| `verify_email` | Verify an email address for deliverability using Mailgun's validation API | `email` |
| `create_mailinglist_member` | Add a member to an existing Mailgun mailing list | `list_address`, `address` |
| `create_route` | Create a new Mailgun route for email matching and forwarding | `priority`, `description`, `expression`, `action` |
| `delete_mailinglist_member` | Delete a member from a Mailgun mailing list by email address | `list_address`, `address` |
| `list_domains` | List all domains configured in the Mailgun account | |
| `list_mailinglist_members` | List all members of a Mailgun mailing list | `list_address` |
| `retrieve_mailinglist_member` | Get details of a specific mailing list member by email address | `list_address`, `address` |
| `suppress_email` | Add an email address to a Mailgun suppression list (bounces, unsubscribes, or complaints) | `domain`, `email`, `category` |

Every tool takes additional `api_key` and `region` parameters that the runtime fills in from the resolved credential.

## Limits & Quotas

- **Free tier**: 100 emails/day for the first 30 days (sandbox domain).
- **Paid plans**: rate limits vary by plan; see <https://www.mailgun.com/pricing/>.
- **Email validation**: billed separately per validation request.
- **Error model**: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
