# SEMrush

SEO analytics integration: domain overview/keywords/competitors,
backlinks, keyword research, traffic analytics, API-units balance.
All 17 SEO actions hit `api.semrush.com` (CSV responses, semicolon
separators); the two `.Trends` traffic actions hit
`api.semrush.com/analytics/ta/api/v3/` (JSON responses).

## Authentication

### API Key (query string `?key=`)

- Required env var: `SEMRUSH_API_KEY`.
- Sent as `?key={api_key}` query parameter.
- Fourth integration to use `TestEndpoint.params` (after convertapi,
  nasdaq, scrape_do).
- `test_endpoint` calls `?type=api_units` — minimal cost.

## Tools

19 actions across 4 capability groups:

| group | actions |
| --- | --- |
| Domain analytics | `domain_overview`, `domain_organic_keywords`, `domain_paid_keywords`, `competitors` |
| Backlinks | `backlinks`, `backlinks_domains` |
| Keyword research | `keyword_overview`, `keyword_overview_single_db`, `batch_keyword_overview`, `related_keywords`, `keyword_organic_results`, `keyword_paid_results`, `keyword_ads_history`, `broad_match_keywords`, `phrase_questions`, `keyword_difficulty` |
| Traffic (.Trends) | `traffic_summary`, `traffic_sources` |
| Utility | `api_units_balance` |

## Limits & Quotas

- SEMrush's main `https://api.semrush.com/` endpoint returns
  semicolon-separated CSV with a header row. The shared `_call_csv`
  helper parses it into `records: list[dict[str, str]]`.
- The two `.Trends` actions (`traffic_summary` / `traffic_sources`)
  return JSON (or text fallback) — surfaced verbatim on `data`.
- `batch_keyword_overview` and `keyword_difficulty` are capped at
  100 keywords per call (SEMrush's limit).
- API errors come back as HTTP 200 with `ERROR ...` body text — the
  helper detects this and converts to `success=False`.
- Each action carries an API-units cost (10-100 per record);
  consult SEMrush's docs.

## Maintainer

ModuleX core team.
