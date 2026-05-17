# Klaviyo

Email-marketing list and profile management against the Klaviyo REST
API (`a.klaviyo.com/api`), pinned to revision `2024-10-15`.

## Authentication

### Private API Key

- Required env var: `KLAVIYO_API_KEY`.
- Settings → API Keys at <https://www.klaviyo.com/settings/account/api-keys>.
- Sent as `Authorization: Klaviyo-API-Key <key>` with `revision: 2024-10-15`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_lists` | List all lists, paginated | — |
| `get_list` | Get a single list by ID | `list_id` |
| `create_list` | Create a new list | `name` |
| `get_profiles` | List all profiles, paginated | — |
| `add_members_to_list` | Subscribe profiles to a list | `list_id`, `profile_ids` |

## Limits & Quotas

- Pagination follows JSON:API cursor links — both `get_lists` and
  `get_profiles` page through results until `max_results` is reached
  or `links.next` is exhausted.
- Failures (any non-2xx, plus exceptions) surface as `success=False`
  with an `error` string. Empty/blank API keys short-circuit before
  the HTTP call.

## Maintainer

ModuleX core team.
