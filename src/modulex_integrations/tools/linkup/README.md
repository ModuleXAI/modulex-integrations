# Linkup

Web search for AI agents — retrieve up-to-date information from across
the web with source attribution, via the Linkup REST API
(`api.linkup.so/v1`).

## Authentication

One method supported — validated against `POST /v1/search` with a
minimal standard query.

### API Key

- Sign in at <https://app.linkup.so>, open the **API Keys** section, and
  generate or copy your key.
- Required env var: `LINKUP_API_KEY`.
- The key is sent as `Authorization: Bearer <key>` on every request; the
  runtime injects it into the tool's `api_key` parameter from the
  resolved credential.

## Tools

| name | description | required params |
| --- | --- | --- |
| `search` | Search the web and return an AI-generated sourced answer or raw ranked results | `q` |

Set `output_type` to `sourcedAnswer` (default) for an answer with a
`sources` citation list, `searchResults` for a `results` array, or
`structured` to return a custom JSON shape. `depth` selects how much work
the search performs (`standard`, `deep`, or `fast`). Optional filters
include date bounds (`from_date`/`to_date`) and comma-separated
`include_domains`/`exclude_domains`.

## Limits & Quotas

- **Rate limit**: ~60 requests/min.
- **Depth tiers**: `standard` queries are cheaper and faster; `deep`
  queries cost more and take longer.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
