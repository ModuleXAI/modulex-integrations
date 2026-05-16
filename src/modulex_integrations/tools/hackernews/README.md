# Hacker News

Read-only access to the official Hacker News JSON API
(`hacker-news.firebaseio.com/v0`) plus keyword search backed by
`hnrss.org` RSS feeds.

## Authentication

### ModuleX Managed Key (no credential)

- The Hacker News API is public; the `modulex_key` auth_schema is
  declarative-only. No `test_endpoint` is shipped.
- Each `@tool` accepts `api_key: str | None = None` for signature
  uniformity with the rest of the credential system but ignores it.

## Tools

| name | description | required params |
| --- | --- | --- |
| `search_stories` | RSS keyword search across stories | — |
| `search_comments` | RSS keyword search across comments | — |
| `get_top_stories` | Front-page top stories | — |
| `get_new_stories` | Newest stories | — |
| `get_best_stories` | Highest-ranked recent stories | — |
| `get_ask_stories` | Ask HN | — |
| `get_show_stories` | Show HN | — |
| `get_job_stories` | Job postings | — |
| `get_item` | Story/comment/poll by id | `item_id` |
| `get_user` | User profile | `username` |

## Limits & Quotas

- `fetch_details=False` returns only the ID list (one HTTP call instead
  of N+1). `fetch_details=True` issues one detail call per item, capped
  at `limit`.
- `max_results` is capped at 50 on the RSS endpoints (hnrss.org cap).
- Failures and parse errors surface as `success=False` with `error`.

## Maintainer

ModuleX core team.
