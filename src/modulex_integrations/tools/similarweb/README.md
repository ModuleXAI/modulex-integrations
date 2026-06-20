# Similarweb

Website traffic and analytics data: traffic estimates, engagement
metrics, rankings, and traffic-source breakdowns from the Similarweb
Web Traffic API (`api.similarweb.com`).

## Authentication

One method supported. The credential is validated against a lightweight
`general-data/all` website-overview request that returns HTTP 200 for a
valid key.

### API Key

- Sign in at <https://www.similarweb.com> and open the API account
  dashboard at <https://account.similarweb.com>.
- Copy your Web Traffic API key from the API management section.
- Required env var: `SIMILARWEB_API_KEY`.
- The key is sent as the `api_key` query-string parameter on every
  request.

## Tools

| name | description | required params |
| --- | --- | --- |
| `website_overview` | Comprehensive analytics: traffic, rankings, engagement, and traffic sources | `domain` |
| `traffic_visits` | Total website visits over time (desktop + mobile) | `domain` |
| `bounce_rate` | Website bounce rate over time (desktop + mobile) | `domain` |
| `pages_per_visit` | Average pages per visit over time (desktop + mobile) | `domain` |
| `visit_duration` | Average desktop visit duration over time (seconds) | `domain` |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential. The four time-series tools
(`traffic_visits`, `bounce_rate`, `pages_per_visit`, `visit_duration`)
also accept `country` (default `world`), `granularity` (default
`monthly`: `daily`/`weekly`/`monthly`), optional `start_date`/`end_date`
in `YYYY-MM` format, and `main_domain_only`.

## Limits & Quotas

- Rate limits and historical data depth (typically up to 37 months) are
  determined by your Similarweb subscription tier.
- Time-series responses are scoped by `country` and `granularity`; query
  a single country or `world` per call.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
