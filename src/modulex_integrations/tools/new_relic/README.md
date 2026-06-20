# New Relic

Query observability data and record deployments in New Relic. Run NRQL
queries, search monitored entities, fetch entity details, and create
deployment change events through New Relic's NerdGraph GraphQL API
(`api.newrelic.com/graphql`, or `api.eu.newrelic.com/graphql` for the EU
region).

## Authentication

### API Key

- Sign in to New Relic at <https://one.newrelic.com>, open the user menu,
  and go to **API keys**.
- Create a **User** key — its value starts with `NRAK-`.
- Required env var: `NEW_RELIC_API_KEY` (format:
  `NRAK-<your-user-key>`).
- The key is sent in the `API-Key` request header. Validation POSTs a
  minimal NerdGraph query (`{ actor { user { name } } }`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `nrql_query` | Run a NRQL query against a New Relic account | `account_id`, `nrql` |
| `search_entities` | Search monitored entities by name, type, tags, or state | `query` |
| `get_entity` | Fetch a New Relic entity by GUID | `guid` |
| `create_deployment_event` | Record a deployment change tracking event | `entity_guid`, `version` |

Every tool takes an additional `api_key` parameter that the runtime fills
in from the resolved credential, plus an optional `region` (`us` default,
or `eu`) that selects the data center endpoint.

## Limits & Quotas

- All actions hit the NerdGraph GraphQL endpoint; New Relic enforces
  account-level NerdGraph rate limits (per-minute request and query-cost
  budgets). Heavy or unbounded NRQL queries may be throttled or time out.
- `nrql_query` accepts an optional `timeout` (seconds) forwarded to
  NerdGraph; the HTTP client itself caps each call at 90 seconds.
- `create_deployment_event` custom attribute names must be letters,
  numbers, and underscores (not starting with a number), must not contain
  `.`, and must avoid New Relic's reserved NRQL keywords; invalid names are
  rejected before the call. A supplied `timestamp` must be within one day
  of the current time per New Relic's change tracking rules.
- **Error model**: non-2xx responses, GraphQL `errors`, and timeouts are
  caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
