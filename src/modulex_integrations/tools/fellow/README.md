# Fellow

Meeting productivity platform for notes, action items, and meeting management via the Fellow REST API (`https://<subdomain>.fellow.app/api/v1`).

## Authentication

### API Key Authentication

- Sign in to your Fellow workspace at `https://<subdomain>.fellow.app`
- Navigate to **Settings > Integrations > API** and generate or copy your API key
- Note your workspace subdomain (the part before `.fellow.app` in your URL)
- Required env vars:
  - `FELLOW_SUBDOMAIN` (format: `mycompany`) — your workspace subdomain
  - `FELLOW_API_KEY` (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`) — your API key
- Docs: <https://developers.fellow.ai>

## Tools

| name | description | required params |
| --- | --- | --- |
| `archive_action_item` | Archive an action item | `action_item_id` |
| `complete_action_item` | Complete an action item | `action_item_id` |
| `get_note_by_id` | Get a note by its ID | `note_id` |

Every tool takes additional `subdomain` and `api_key` parameters that the runtime fills in from the resolved credential.

## Limits & Quotas

- No documented public rate limits from Fellow's API documentation.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
