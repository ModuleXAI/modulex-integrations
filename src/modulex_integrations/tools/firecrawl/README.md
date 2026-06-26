# Firecrawl

AI-powered web scraping, crawling, and search against the Firecrawl
v1 REST API (`api.firecrawl.dev/v1`). Covers single-URL scraping,
URL discovery (map), web search, multi-page crawls with job-id +
status polling, LLM-based structured extraction, and batch scraping.

## Authentication

### API Key (Bearer)

- **Single `api_key` schema** (bring-your-own-key), authed via
  `Authorization: Bearer <key>`. `api_key: str` is the tool parameter.
- API-key env var: `FIRECRAWL_API_KEY`.
- The `test_endpoint` hits POST `/scrape` with `example.com` to
  validate the credential cheaply.

## Tools

| name | description | required params |
| --- | --- | --- |
| `scrape` | Single-URL content extraction | `url` |
| `map_website` | Discover URLs on a site | `url` |
| `search` | Web search (with optional scraping) | `query` |
| `crawl` | Start a multi-page crawl job | `url` |
| `check_crawl_status` | Poll a crawl job by id | `crawl_id` |
| `extract` | LLM-based structured extraction | `urls` |
| `batch_scrape` | Scrape many URLs in one job | `urls` |

## Limits & Quotas

- HTTP timeouts: 120s for scrape/map/search/status; 180s for
  crawl/extract/batch (long-running jobs).
- Snake_case input parameters are converted to camelCase for the
  upstream API (`only_main_content` → `onlyMainContent`, etc.).
- Response `data` carries the upstream JSON body unchanged so callers
  see the rich nested metadata Firecrawl returns.
- Failures (non-2xx, timeouts, parse errors) surface as
  `success=False` + `error`; empty/blank API keys short-circuit.

## Maintainer

ModuleX core team.
