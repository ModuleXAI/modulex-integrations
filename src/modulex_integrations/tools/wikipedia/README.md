# Wikipedia

Search and retrieve content from Wikipedia, the free online
encyclopedia. Backed by the two public Wikipedia read APIs: the Wikimedia
REST API (`<lang>.wikipedia.org/api/rest_v1`) for page summaries and
random articles, and the MediaWiki core REST API
(`<lang>.wikipedia.org/w/rest.php/v1`) for search and page HTML.

## Authentication

### ModuleX Managed Key (no credential)

- The Wikipedia read APIs are fully open — they accept no API key, no
  OAuth token, and no other credential. The `modulex_key` schema is
  declarative only: it exists because the runtime resolves a credential
  before every tool call, and it validates nothing.
- Each `@tool` accepts `api_key: str | None = None` for signature
  uniformity with the rest of the credential system but ignores it.
- The shipped `test_endpoint` is a reachability probe against the public
  page-summary endpoint, not a credential check.

Every request identifies itself with a descriptive `User-Agent`
(`modulex-integrations/1.0 (+https://modulex.dev)`). Wikimedia's
User-Agent policy requires automated clients to send a tool name, a
version and a contact URL; requests with a generic or absent agent are
throttled hard and may be answered with HTTP 403. Do not strip or
genericize this header.

## Tools

| name | description | required params |
| --- | --- | --- |
| `summary` | Lead extract and metadata for one article | `page_title` |
| `search` | Search articles by title or full text | `query` |
| `content` | Full rendered HTML of one article plus revision metadata | `page_title` |
| `random` | A randomly drawn article, summarized | — |

Every action takes an optional `language` (default `en`) selecting the
Wikipedia language edition: `tr`, `de`, `simple`, `zh-min-nan`, and so
on. The code is matched against an anchored pattern before it is used,
so the only host these tools can reach is a `wikipedia.org` subdomain; an
unrecognized shape comes back as `success=False` rather than being sent.

`summary` reports the resolved page kind in `summary.type` — `standard`
for an ordinary article, `disambiguation` when the title is ambiguous —
so an agent can detect an ambiguous lookup instead of quoting a list of
unrelated meanings. Titles that are redirects resolve to their target
automatically, in `summary`, `content` and `search` alike.

`search` returns `excerpt` as HTML with the matched terms wrapped in
`<span class="searchmatch">`, plus `description`, `thumbnail` and a
derived article `url`. `total_hits` counts the results in this response;
the search endpoint does not report a corpus-wide total.

`content` returns the article's Parsoid HTML together with `pageid`,
`title`, `revision`, `timestamp` and `tid` (the response ETag).

## Limits & Quotas

- **Rate limit**: Wikimedia allows roughly **200 requests per minute**
  for an anonymous client sending a compliant `User-Agent`, and drops
  to **10 requests per minute** for clients with no identifying
  characteristics. These tools do not sleep — pace calls on the agent
  side.
- **Search size**: `search_limit` is clamped to 1-100 (the endpoint
  rejects anything outside that range with HTTP 400); the default is 10.
- **HTML size**: full articles routinely exceed a megabyte of HTML, so
  `content` truncates at `max_length` characters (default 100,000) and
  reports `truncated: true` plus the original `html_length`. Pass `0` or
  a negative value to disable truncation.
- **Error model**: a missing page (HTTP 404), a rejected parameter
  (HTTP 400), a timeout, a non-JSON body, and a body whose shape or
  field types differ from the documented ones are all returned as
  `success=False` with an `error` string rather than raising. A missing
  page is reported by name — Wikipedia's own 404 body reads
  `{"status": 404, "type": "Internal error"}` and would otherwise look
  like a server fault rather than a bad title. A
  disambiguation page is **not** an error — it comes back as
  `success=True` with `summary.type == "disambiguation"`.
- **Content licensing**: article text is CC BY-SA; attribute Wikipedia
  and link back to the article when you republish it.

## Maintainer

ModuleX core team.
