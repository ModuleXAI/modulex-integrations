# Exa Search

AI-powered semantic web search, content extraction, similarity
matching, and answer generation against the Exa REST API
(`api.exa.ai`).

## Authentication

Two methods supported — both validate against `POST /search` with a
minimal 1-result probe query.

### API Key (recommended)

- Sign in at <https://dashboard.exa.ai>, go to **API Keys**, generate
  or copy your key.
- Required env var: `EXA_API_KEY` (format:
  `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).

### ModuleX Managed Key

Uses ModuleX's managed Exa key with usage tracked against the
account's weekly credit limit. No env vars to configure — the
runtime injects the credential automatically.

## Tools

| name | description | required params |
| --- | --- | --- |
| `search` | Semantic web search with category/domain/date filters | `query` |
| `get_contents` | Extract full page text from a list of URLs | `urls` |
| `find_similar` | Find pages similar to a given URL | `url` |
| `answer` | AI-generated answer to a question with citations | `query` |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential (note: **not** the
`auth_type`/`auth_data` pair used by github and slack — Exa uses the
modulex `api_key` injection convention).

## Limits & Quotas

- **Standard tier**: ~60 req/min.
- **Deep search**: ~20 req/min (higher compute cost).
- **Pricing** (approx., per legacy manifest):
  - Neural search 1–25 results: $0.005
  - Neural search 26–100: $0.025
  - Deep search 1–25: $0.015
  - Deep search 26–100: $0.075
  - Content per page: $0.001
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
