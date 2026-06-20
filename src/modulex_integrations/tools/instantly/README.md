# Instantly

Cold-email outreach automation against the Instantly V2 REST API
(`api.instantly.ai`). Manage leads, lead lists, campaigns, and Unibox
emails.

## Authentication

### API Key

- Sign in at <https://app.instantly.ai>, open **Settings → API Keys**
  (Integrations), and create a new V2 API key with the required scopes.
- Required env var: `INSTANTLY_API_KEY`.
- Each request is sent with `Authorization: Bearer <api_key>`.

The runtime injects the resolved `api_key` into every tool as an extra
parameter (the modulex `api_key` injection convention — not the
`auth_type`/`auth_data` pair).

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_leads` | List leads with search, campaign, list, and pagination filters | — |
| `get_lead` | Retrieve a lead by ID | `lead_id` |
| `create_lead` | Create a lead in a campaign or lead list | — |
| `delete_leads` | Delete leads in bulk from a campaign or lead list | — |
| `update_lead_interest_status` | Submit a job to update a lead interest status | `lead_email` |
| `list_campaigns` | List campaigns with search, status, tag, and pagination filters | — |
| `create_campaign` | Create a campaign with a schedule schema | `name`, `campaign_schedule` |
| `patch_campaign` | Update documented campaign fields | `campaign_id` |
| `activate_campaign` | Activate, start, or resume a campaign | `campaign_id` |
| `list_emails` | List Unibox emails with search and pagination filters | — |
| `reply_to_email` | Send a reply to an existing Unibox email | `eaccount`, `reply_to_uuid`, `subject` |
| `list_lead_lists` | List lead lists with search and pagination filters | — |
| `create_lead_list` | Create a lead list | `name` |

## Limits & Quotas

- List endpoints accept `limit` (1–100) and forward-paginate via the
  `next_starting_after` cursor returned in each response — pass it back
  as `starting_after` for the next page.
- `update_lead_interest_status` submits an asynchronous background job;
  the response carries a submission `message`, not the updated lead.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan agent
  retries based on the error string.

## Maintainer

ModuleX core team.
