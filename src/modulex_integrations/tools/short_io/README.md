# Short.io

URL shortening, link management, and analytics against the Short.io
REST API (`api.short.io` for CRUD, `api-v2.short.cm` for statistics).

## Authentication

### API Key (raw, no Bearer prefix)

- Required env var: `SHORT_IO_API_KEY`.
- Settings & Integrations → Integrations & API at <https://short.io>.
- Sent as `Authorization: <key>` (no `Bearer ` prefix — Short.io
  doesn't expect one).

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_link` | Shorten a URL with full customization | `domain`, `original_url` |
| `update_link` | Mutate an existing short link | `link_id` |
| `delete_link` | Permanently delete a short link | `link_id` |
| `expire_link` | Set expiration + fallback URL | `link_id`, `expires_at`, `expired_url` |
| `get_link_info` | Lookup a link by domain + path | `domain`, `path` |
| `list_links` | List links for a domain id | `domain_id` |
| `list_domains` | List all configured domains | — |
| `get_domain_statistics` | Clicks + analytics for a domain | `domain_id` |

## Limits & Quotas

- `list_links` is capped at 150 entries per call (Short.io's max).
- Date strings (`expires_at`) are parsed from `yyyy-mm-dd` and sent
  as Unix-millisecond timestamps; invalid dates silently drop the
  field rather than fail the call (preserves legacy behavior).
- `get_domain_statistics` calls the separate
  `api-v2.short.cm` analytics host; everything else hits `api.short.io`.
- Failure paths surface as `success=False` + `error` (HTTP non-2xx,
  exceptions, empty API keys).

## Maintainer

ModuleX core team.
