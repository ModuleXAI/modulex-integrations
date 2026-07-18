# Pinecone

Pass-through integration for the [Pinecone](https://pinecone.io) vector
database REST API: vector similarity search, raw-text search on
integrated-embedding indexes, index management, and vector
upsert/delete in your own Pinecone project.

## Authentication

- **`custom` auth_type** (single API key, kept alongside the other
  vector-database connection-style credentials).
- Env var: `PINECONE_API_KEY` (required). Create one in the [Pinecone
  console](https://app.pinecone.io) under API Keys.
- The legacy `environment` field is gone: since Pinecone's serverless
  API, each index's data-plane host is resolved via the control plane
  (`api.pinecone.io`), so the key is the only credential needed.

## Tools

| name | description | required params |
| --- | --- | --- |
| `query` | Vector similarity search (`POST /query`); works on every index type. | `index_name`, `query_vector` |
| `search_records` | Raw-text search, embedded server-side — integrated-embedding indexes ONLY. | `index_name`, `query_text` |
| `list_indexes` | List all indexes in the project. | — |
| `describe_index` | Native index config (dimension, metric, host, spec, status). | `index_name` |
| `describe_index_stats` | Native index stats (namespaces, totalVectorCount). | `index_name` |
| `upsert_vectors` | Upsert native `{id, values, metadata?}` vectors. | `index_name`, `vectors` |
| `delete_vectors` | Delete by IDs, by metadata filter, or all in a namespace. | `index_name` |
| `create_index` | Create a serverless index. | `name`, `dimension` |
| `delete_index` | Delete an index. | `index_name` |

## Limits & Quotas

- 30s request timeout per call.
- All requests pin `X-Pinecone-Api-Version: 2025-01`.
- Data-plane actions resolve the index host via a control-plane
  describe first (one extra GET per call — the tool stays stateless).
- No ModuleX-side embedding: `search_records` relies on Pinecone's
  server-side integrated embedding and fails on non-integrated
  indexes; use `query` with a vector there.
- Rate limits are those of your Pinecone plan.

## Maintainer

ModuleX core team.
