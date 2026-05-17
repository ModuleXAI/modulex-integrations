# Scrape.do

Enterprise web-scraping API integration: basic HTTP, JS-rendered
browser, screenshots, markdown conversion, and credit-usage stats.
All five actions hit `api.scrape.do` (or `/info` for usage).

## Authentication

### API Key (query string `?token=`)

- Required env var: `SCRAPEDO_API_KEY`.
- Created at <https://scrape.do> dashboard.
- Sent as `?token={api_key}` query parameter (third integration to
  use `TestEndpoint.params` after convertapi and nasdaq).

## Tools

| name | description | required params |
| --- | --- | --- |
| `scrape` | Basic HTTP scrape (no JS) | `url` |
| `scrape_with_js` | Headless-browser scrape | `url` |
| `take_screenshot` | Viewport/full-page/element capture | `url` |
| `scrape_to_markdown` | HTML → markdown | `url` |
| `get_usage_stats` | Account credits + monthly quota | — |

## Limits & Quotas

- Each scrape action exposes 20+ optional knobs (proxy routing,
  geo-targeting, device emulation, cookies, headers, wait
  conditions, viewport). All map to Scrape.do's camelCase query
  string keys via a single `_PARAM_MAP` translation table.
- `take_screenshot` is mutually-exclusive between viewport / full-page
  / element modes — the tool validates that `full_page` and
  `selector` aren't both set.
- Output shape varies per upstream response:
  - JSON → `payload: dict`
  - text/html/markdown → `data: str` with `is_binary=False`
  - image/* → `data: <base64>` with `is_binary=True`
- 180s timeout for scrape operations (matches legacy); 30s for the
  usage-stats endpoint.

## Maintainer

ModuleX core team.
