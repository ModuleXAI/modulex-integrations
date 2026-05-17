# Cloudflare

Cloudflare v4 API integration: DNS, WAF lists, zones, firewall
rules, load balancer monitors & pools, account discovery. All
against `api.cloudflare.com/client/v4`.

## Authentication

### API Token (Bearer)

- Required env var: `CLOUDFLARE_API_TOKEN`.
- Created in Dashboard → My Profile → API Tokens.
- Sent as `Authorization: Bearer <token>`.
- `test_endpoint` hits `/user/tokens/verify` — free, no API cost.

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_zones` | List zones with filters | — |
| `create_dns_record` | Add a DNS record | `zone_id`, `type`, `name`, `content` |
| `update_dns_record` | Mutate an existing record | `zone_id`, `record_id` |
| `delete_dns_record` | Remove a DNS record | `zone_id`, `record_id` |
| `list_waf_lists` | All WAF lists (no items) | `account_id` |
| `create_waf_list` | New empty WAF list | `account_id`, `name`, `kind` |
| `update_waf_list` | Update WAF list description | `account_id`, `list_id`, `description` |
| `delete_waf_list` | Delete a WAF list | `account_id`, `list_id` |
| `list_accounts` | All accessible accounts | — |
| `list_account_members` | Members of an account | `account_id` |
| `list_firewall_rules` | Firewall rules for a zone | `zone_id` |
| `list_monitors` | Load-balancer monitors | `account_id` |
| `list_pools` | Load balancer pools | `account_id` |

## Limits & Quotas

- Cloudflare wraps every response in
  `{"success", "errors", "messages", "result", "result_info"}`. The
  shared `_call` helper checks the envelope's `success` flag (not just
  HTTP status), pulls `errors[0].message` on failure, and lifts
  `result_info` pagination (`total_count`, `page`, `per_page`) onto
  the output's top-level `total`/`page`/`per_page` fields for list
  actions.
- Most list endpoints cap `per_page` at 50; firewall rules cap at 100.
- `result` is open: list endpoints return a JSON array; CRUD
  endpoints return the object directly. Mirrors the upstream shape.

## Maintainer

ModuleX core team.
