# Apollo.io

B2B sales intelligence integration: full CRM CRUD + enrichment +
prospecting + sequences + tasks against `api.apollo.io/api/v1`.
**Largest integration in the package by action count** (27 actions).

## Authentication

### API Key (X-Api-Key header)

- Required env var: `APOLLO_IO_API_KEY`.
- Sent as `X-Api-Key: <key>` header on every request.
- Some endpoints (e.g. `create_account`, `create_deal`) require a
  **master API key** — preserved from the legacy implementation as
  a runtime concern (the credential test endpoint just needs the
  basic key).

## Tools

27 actions split across 8 capability groups:

| group | actions |
| --- | --- |
| Enrichment | `people_enrichment`, `bulk_people_enrichment`, `organization_enrichment`, `bulk_organization_enrichment` |
| Search | `people_search`, `organization_search`, `organization_job_postings` |
| Contacts | `create_contact`, `update_contact`, `search_contacts`, `view_contact` |
| Accounts | `create_account`, `update_account`, `search_accounts`, `view_account` |
| Deals | `create_deal`, `update_deal`, `list_deals`, `view_deal` |
| Sequences | `search_sequences`, `add_contacts_to_sequence` |
| Tasks | `create_task`, `search_tasks` |
| Utility | `get_api_usage`, `list_users`, `list_contact_stages`, `list_account_stages`, `list_deal_stages` |

## Limits & Quotas

- `per_page` clamped at 100 (Apollo's cap on most search endpoints).
- Bulk-enrichment actions clamp input to 10 items per request
  (Apollo's cap).
- Enrichment-class actions consume Apollo credits; CRUD on
  contacts/accounts/deals does NOT.
- Domain helpers strip `https://` / `www.` / paths so callers can
  pass full URLs or bare hostnames interchangeably.

## Maintainer

ModuleX core team.
