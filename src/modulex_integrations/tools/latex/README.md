# LaTeX

Inspect the typesetting resources available on the public LaTeX-on-HTTP
service at `latex.ytotech.com`: search the installed TeX Live package
collection, read a single package's full metadata, and list the system
fonts the LaTeX compilers can address with `fontspec`.

## Authentication

### ModuleX Managed Key (no credential)

- The LaTeX-on-HTTP API is fully open — it accepts no API key, no OAuth
  token, and no other credential. The `modulex_key` schema is declarative
  only: it exists because the runtime resolves a credential before every
  tool call, and it validates nothing.
- Each `@tool` accepts `api_key: str | None = None` for signature
  uniformity with the rest of the credential system but ignores it.
- The shipped `test_endpoint` is a reachability probe against the service
  root (which answers with the API and TeX Live versions), not a
  credential check.

Requests identify themselves with a descriptive `User-Agent`
(`modulex-integrations/1.0 (+https://modulex.dev)`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `search_packages` | Search installed TeX Live packages by name or description | `query` |
| `get_package` | Full metadata for one TeX Live package by its exact name | `name` |
| `list_fonts` | System fonts available to the compiler, optionally filtered | – |

`search_packages` and `list_fonts` both accept `max_results`
(default 25 / 50, capped at 100 / 200) and report `total_matches`, the
number of entries that matched before truncation. `get_package` returns
the package's description, category, license, CTAN topics, related
packages, homepage and CTAN page; names are validated against the TeX
Live naming rules (letters, digits and `. _ + -`) before the request is
made.

## Limits & Quotas

- **Rate limit**: the service publishes no documented rate limit. It is a
  small, free, community-run deployment — keep call volume modest and do
  not poll.
- **Response size**: neither listing endpoint accepts a server-side
  filter, so `search_packages` downloads the whole package catalogue
  (~5000 entries, roughly a megabyte of JSON) and `list_fonts` the whole
  font list (~2700 entries) on every call, then filters and truncates
  locally. The request timeout is 60 seconds accordingly.
- **Filtering**: matching is a case-insensitive substring test — against
  package name and short description for `search_packages`, against font
  family and full font name for `list_fonts`.
- **Error model**: non-200 statuses (including the `404` +
  `{"error": "Package not found"}` a missing package returns), timeouts,
  non-JSON bodies, and wrong-typed fields are all caught and returned as
  `success=False` with an `error` string rather than raising.
- **Coverage**: the reported packages and fonts describe the TeX Live
  installation on that specific service host, so results can change when
  the host is updated.

## Maintainer

ModuleX core team.
