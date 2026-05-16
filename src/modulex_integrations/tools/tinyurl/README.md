# TinyURL

URL shortening, analytics retrieval, and link-metadata updates against
the TinyURL REST API (`api.tinyurl.com`).

## Authentication

### API Token (Bearer)

- Required env var: `TINYURL_API_KEY`.
- Sign in at <https://tinyurl.com/app/dev>, copy your API token.
- Sent as `Authorization: Bearer <token>`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_shortened_link` | Shorten a URL with optional alias/tags | `url` |
| `retrieve_link_analytics` | Click analytics (paid only) | `alias`, `from_date` |
| `update_link_metadata` | Mutate an existing TinyURL | `domain`, `alias` |

## Limits & Quotas

- Free tier: shortening only; analytics + tags + expiration require
  a paid plan. Non-2xx responses are surfaced as `success=False` +
  parsed `error`.

## Maintainer

ModuleX core team.
