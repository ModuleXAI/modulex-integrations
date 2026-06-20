# Mem0

Persistent agent memory management against the Mem0 REST API
(`api.mem0.ai`) — add, search, and retrieve long-term memories so AI
agents can recall user context, preferences, and prior conversations
across sessions.

## Authentication

Mem0 authenticates with an API key sent as `Authorization: Token <api_key>`.
The credential is validated against `POST /v3/memories/` with a minimal
1-result paginated list query.

### API Key

- Sign in at <https://app.mem0.ai>, open the dashboard, and go to the
  **API Keys** section to generate or copy your key.
- Required env var: `MEM0_API_KEY`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_memories` | Add memories to Mem0 for persistent storage and retrieval | `user_id`, `messages` |
| `search_memories` | Semantic search over a user's memories | `user_id`, `query` |
| `get_memories` | Retrieve memories by ID or by filter criteria (date range, pagination) | `user_id` |

Every tool takes an additional `api_key` parameter that the runtime
fills in from the resolved credential.

`add_memories` accepts `messages` as a list of `{"role": ..., "content": ...}`
objects (role must be `user` or `assistant`); a JSON string of the same
shape is also accepted. `get_memories` retrieves a single memory when a
`memory_id` is supplied, otherwise returns a paginated, optionally
date-filtered list for the given `user_id`.

## Limits & Quotas

- Rate limits and quotas depend on your Mem0 plan; see
  <https://docs.mem0.ai> for current tiers.
- `add_memories` is processed asynchronously — the response returns a
  `status` (initially `PENDING`) and an `event_id` for polling progress,
  not the stored memory records themselves.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising. Plan for
  retries on the agent side based on the error string.

## Maintainer

ModuleX core team.
