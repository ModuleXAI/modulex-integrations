# SendGrid

SendGrid transactional + marketing email integration via the SendGrid
v3 REST API. Pure HTTP, no SDK dep.

## Authentication

- **api_key** (Bearer header). Env var `SENDGRID_API_KEY` (sensitive).
- `test_endpoint` validates by listing marketing lists
  (`GET /marketing/lists`).

## Runtime convention

Key-based: every `@tool` accepts `(api_key, ...)`.

## Tools

| name | description |
| --- | --- |
| `send_email` | Single recipient + optional CC/BCC. |
| `send_email_multiple_recipients` | Individual delivery (per-recipient personalization). |
| `add_or_update_contact` | Marketing contacts upsert. |
| `search_contacts` | SGQL search (e.g. `email LIKE 'test%'`). |
| `create_contact_list`, `get_contact_lists`, `remove_contact_from_list`, `delete_contacts` | List + contact CRUD. |
| `add_email_to_global_suppression`, `delete_global_suppression`, `list_global_suppressions` | Global suppression management. |
| `get_all_bounces`, `delete_bounces` | Bounce management. |
| `list_blocks`, `delete_blocks` | Block management. |

## Limits & Quotas

- 30s timeout on every request.
- `get_contact_lists.page_size` is clamped at 1000 (SendGrid max).
- Mutating actions wrap everything in try/except → `success=False`
  envelope (exa-style); HTTP timeouts surface as a distinct error
  message.

## Maintainer

ModuleX core team.
