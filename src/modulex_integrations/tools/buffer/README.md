# Buffer

Schedule and publish social media posts across connected channels — create,
edit, and delete posts, browse channels, and capture content ideas via the
Buffer GraphQL API (`api.buffer.com`).

## Authentication

### API Key (bearer token)

- Sign in at <https://publish.buffer.com> and open **API settings**
  (<https://publish.buffer.com/settings/api>) to create a personal API key
  ([docs](https://developers.buffer.com/guides/getting-started.html)).
- Env var: `BUFFER_API_KEY` — the Buffer API key.
- Sent on every request as `Authorization: Bearer <key>`.
- A key acts on its own account's data only; there is no third-party
  authorization flow to complete.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_post` | Create a post — queue it, share now, schedule it, or save a draft | `channel_id` (plus `text` and/or `media_url`) |
| `edit_post` | Update an existing post's text, schedule, or media | `post_id` |
| `get_post` | Get a single post with its status, schedule, and media | `post_id` |
| `get_posts` | List posts, filtered by channel and status, with cursor paging | `organization_id` |
| `delete_post` | Delete a post by ID | `post_id` |
| `get_channels` | List connected channels and their channel IDs | `organization_id` |
| `get_account` | Get the authenticated account and its organization IDs | — |
| `create_idea` | Save a content idea to the ideas board | `organization_id`, `text` |
| `get_ideas` | List content ideas with cursor paging | `organization_id` |
| `get_idea_groups` | List idea groups (board columns) and their IDs | `organization_id` |

Every tool takes an additional `api_key` parameter that the runtime fills in
from the resolved credential.

Start from `get_account` to discover organization IDs, then `get_channels`
to discover channel IDs — both are required inputs elsewhere.

## Limits & Quotas

- The API is a single GraphQL endpoint (`POST https://api.buffer.com`) and
  answers **HTTP 200 for nearly everything**, including failures: check the
  `errors` array and typed mutation errors, not the status code. These tools
  fold all three shapes into `success=false` + `error`.
- Rate limiting surfaces as a `RATE_LIMIT_EXCEEDED` error code; posting
  volume is additionally capped by the plan's channel and scheduled-post
  limits (`LimitReachedError`).
- Media is attached by **public URL only** — Buffer downloads the file itself
  at publish time, so the URL must remain reachable until the post publishes.
  Attaching media on `edit_post` replaces the post's existing attachments.
- `edit_post` must send `scheduling_type` on every call (the API requires it),
  so pass `notification` when editing a post that publishes by notification —
  the `automatic` default would otherwise change how it publishes.
- `get_posts` and `get_ideas` are cursor-paginated: pass
  `page_info.end_cursor` back as `after` while `page_info.has_next_page` is
  true.
- Error model: non-200 responses, timeouts, and GraphQL errors are caught and
  returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
