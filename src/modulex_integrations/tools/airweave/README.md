# Airweave

AI-powered semantic search across your synced data collections via the
Airweave Search REST API (`api.airweave.ai`). One tool retrieves
relevant content from a collection using hybrid, neural, or keyword
strategies, and can optionally synthesize an AI-generated answer.

## Authentication

Authenticates with an API key sent in the `x-api-key` request header.
The credential is validated against `GET /collections`.

### API Key

- Sign in at <https://app.airweave.ai>, open the **API Keys** section,
  and generate or copy your key.
- Required env var: `AIRWEAVE_API_KEY`.

The `search` tool takes an additional `api_key` parameter that the
runtime fills in from the resolved credential.

## Tools

| name | description | required params |
| --- | --- | --- |
| `search` | Semantic search across a synced collection, with optional AI answer | `collection_id`, `query` |

Optional `search` params: `limit`, `retrieval_strategy`
(`hybrid` / `neural` / `keyword`), `expand_query`, `rerank`,
`generate_answer`.

## Limits & Quotas

- **Collection-scoped**: every search runs against one collection's
  readable ID; results carry per-source attribution (`source_name`,
  `breadcrumbs`, `url`).
- **Answer generation**: setting `generate_answer=true` runs an extra
  LLM synthesis step and populates the `completion` field; expect higher
  latency.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
