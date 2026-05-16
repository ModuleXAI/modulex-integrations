# Zendesk

Zendesk customer-support integration via the v2 REST API. Pure HTTP.
17 actions across ticket CRUD + tags + comments, custom fields,
users, locales, macros, and help-center articles.

## Authentication

- **`api_key` auth_type** with a **triple-credential pattern**:
  `subdomain` + `email` + `api_key`. These three together form a
  Basic Auth header (`{email}/token:{api_key}` base64-encoded).
- Env vars (all required): `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`
  (non-sensitive), `ZENDESK_API_KEY` (sensitive).
- `test_endpoint` hits `GET /users/me.json` and asserts the `user`
  field.

## Runtime convention

Key-based but with three keys: every `@tool` accepts
`(subdomain, email, api_key, ...)` as positional args. The modulex
runtime injects all three from `auth_data`.

## Tools

| group | tools |
| --- | --- |
| Ticket CRUD | `create_ticket`, `update_ticket`, `delete_ticket`, `get_ticket`, `list_tickets`, `search_tickets` |
| Tags | `add_ticket_tags` (PUT — additive), `set_ticket_tags` (POST — replaces), `remove_ticket_tags` (DELETE) |
| Comments | `list_ticket_comments` |
| Custom fields | `set_custom_fields` |
| Users | `get_user` |
| Locales | `list_locales` |
| Macros | `list_macros`, `get_macro` |
| Help Center | `list_articles`, `get_article` |

## Notes

- All actions wrap in try/except → `success=False` envelope.
- 30s timeout on every request.
- `per_page` clamped to 100 (Zendesk's max).
- HTTP method semantics for tags are non-obvious (preserved from
  legacy): **PUT** appends, **POST** replaces, **DELETE** removes
  specific items. Documented in each action's docstring.

## Maintainer

ModuleX core team.
