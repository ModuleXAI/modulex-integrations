# Serper

Search the web with the Serper Google Search API. A single `search`
tool returns structured Google SERP data — web, news, places, and image
results — over the `google.serper.dev` REST endpoint.

## Authentication

One method is supported: an API key sent in the `X-API-KEY` header. The
key is validated against `POST /search` with a minimal probe query.

### API Key

- Sign up or log in at <https://serper.dev>, open your dashboard, and go
  to the **API Key** section to create or copy your key.
- Required env var: `SERPER_API_KEY`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `search` | Google search across web, news, places, and images with organic results plus knowledge graph, answer box, people-also-ask, and related searches | `query` |

The tool takes an additional `api_key` parameter that the runtime fills
in from the resolved credential. The `type` parameter selects the search
mode — `search` (default), `news`, `places`, `images`, `videos`, or
`shopping` — and is routed to the matching `google.serper.dev/<type>`
endpoint.

## Limits & Quotas

- **Rate limit**: ~100 requests/minute (per the standard tier).
- **Result count**: control with `num` (e.g. 10, 20, 50, 100); larger
  result counts consume more credits.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
