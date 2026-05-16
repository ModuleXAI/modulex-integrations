# Notion

Notion v1 REST API integration. Pure HTTP (no SDK dep). 19 actions
across pages, databases, blocks, users, comments, and search.

## Authentication

- **Paired `oauth2 + bearer_token` schemas.** OAuth uses
  `https://api.notion.com/v1/oauth/{authorize,token}` with **HTTP
  Basic** for the token exchange (Notion's specific quirk).
  Bearer is the Internal Integration Token (`secret_…`).
- OAuth env vars: `NOTION_OAUTH2_CLIENT_ID`,
  `NOTION_OAUTH2_CLIENT_SECRET` (both `only_for_custom`).
- Bearer env var: `NOTION_ACCESS_TOKEN`.
- Both `test_endpoint`s GET `/users/me`.

## Runtime convention

Token-based: every `@tool` accepts `(auth_type, auth_data, ...)`.
Header `Notion-Version: 2022-06-28` is sent on every request.

## Tools

| group | tools |
| --- | --- |
| Search | `search` |
| Pages | `create_page`, `get_page`, `update_page` |
| Databases | `query_database`, `get_database`, `create_database`, `update_database`, `create_database_item` |
| Blocks | `get_block`, `get_block_children`, `append_blocks`, `update_block`, `delete_block` |
| Users | `list_users`, `get_user`, `get_bot_user` |
| Comments | `create_comment`, `get_comments` |

## N+1 fetch

`get_page` with `include_content=True` does a second call to
`/blocks/<page_id>/children` to populate the `content` field on the
response. Preserved verbatim from legacy. Failures of the content
fetch are silently dropped (the page fetch's `success` still wins).

## Limits & Quotas

- 30s timeout on every request.
- `page_size` clamped to 100 (Notion's max).
- All actions wrap in try/except → `success=False` envelope
  (exa-style).
- Trivial markdown→blocks conversion in `create_page.content`:
  splits on newlines and creates one paragraph block per non-empty
  line. Use `children` for anything fancier.

## Maintainer

ModuleX core team.
