# ArXiv

Search and retrieve academic papers from ArXiv, the open-access
repository of preprints in physics, mathematics, computer science,
quantitative biology, quantitative finance, statistics, electrical
engineering and economics. Backed by the public arXiv API at
`export.arxiv.org/api/query`.

## Authentication

### ModuleX Managed Key (no credential)

- The arXiv API is fully open — it accepts no API key, no OAuth token,
  and no other credential. The `modulex_key` schema is declarative only:
  it exists because the runtime resolves a credential before every tool
  call, and it validates nothing.
- Each `@tool` accepts `api_key: str | None = None` for signature
  uniformity with the rest of the credential system but ignores it.
- The shipped `test_endpoint` is a reachability probe against the public
  query endpoint, not a credential check.

Requests identify themselves with a descriptive `User-Agent`
(`modulex-integrations/1.0 (+https://modulex.dev)`), which is how arXiv
asks automated clients to be reachable.

## Tools

| name | description | required params |
| --- | --- | --- |
| `search` | Keyword/field search across ArXiv papers | `search_query` |
| `get_paper` | Full metadata for one paper by its ArXiv identifier | `paper_id` |
| `get_author_papers` | An author's papers, newest submissions first | `author_name` |

`search` accepts a `search_field` of `all`, `ti`, `au`, `abs`, `co`,
`jr`, `cat` or `rn`. With `all`, the query string is forwarded verbatim,
so full boolean expressions (`au:Smith AND ti:electron`) work as-is.
Paging is done with `start` (zero-based offset) plus `max_results`.

## Limits & Quotas

- **Rate limit**: arXiv asks for no more than **one request every three
  seconds**, from a single connection at a time, counted across every
  machine you control. These tools do **not** sleep — pace calls on the
  agent side. Exceeding the limit returns HTTP `429` with a plain-text
  `Rate exceeded.` body, surfaced as `success=False`.
- **Result size**: `max_results` is capped at 2000 per request (the
  arXiv per-slice maximum); values above that are clamped, values below
  1 are raised to 1.
- **Response format**: every response is an Atom 1.0 feed, parsed with
  the standard library. A response carrying a document type declaration
  is rejected before parsing rather than expanded.
- **Error model**: non-2xx statuses, timeouts, unparseable XML, and
  arXiv's own in-feed error entry (a `200` feed whose single `<entry>`
  is titled `Error`) are all caught and returned as `success=False` with
  an `error` string rather than raising. `get_paper` reports a
  no-such-paper result as `success=False` too.

## Maintainer

ModuleX core team.
