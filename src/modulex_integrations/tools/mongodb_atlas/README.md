# MongoDB Atlas

MongoDB Atlas integration with Vector Search: `$vectorSearch`
aggregations on your existing collections, database/collection/search-
index introspection, and document insert/delete. Uses the PyMongo async
driver (`AsyncMongoClient`) with your own connection string.

## Authentication

- **`custom` auth_type** (a single connection string, not an API key).
- Env var: `MONGODB_ATLAS_CONNECTION_STRING` (required) — a
  `mongodb+srv://user:password@cluster.mongodb.net/` string for a
  database user with access to the target databases. Create one in the
  Atlas UI under Database Access + Connect.
- MongoDB authenticates over its own TCP wire protocol, so the
  credential test is a generic reachability check; real validation
  happens on the first driver connection.

## Tools

| name | description | required params |
| --- | --- | --- |
| `query` | `$vectorSearch` similarity search; takes a query VECTOR (Atlas has no server-side text embedding). Adds a `score` field via `vectorSearchScore`. | `database`, `collection`, `index_name`, `query_vector`, `path` |
| `list_databases` | List all databases in the cluster. | — |
| `list_collections` | Native listCollections entries for a database. | `database` |
| `list_search_indexes` | Atlas Search / Vector Search index definitions on a collection. | `database`, `collection` |
| `insert_documents` | `insert_many` into a collection. | `database`, `collection`, `documents` |
| `delete_documents` | `delete_many` with a non-empty MQL filter (empty filters rejected). | `database`, `collection`, `filter` |

## Limits & Quotas

- 30s server-selection timeout; a fresh client per call (no pooling
  across invocations).
- Results are MongoDB Relaxed Extended JSON — BSON types survive
  serialization as `{"$oid": ...}` / `{"$date": ...}`.
- `query` excludes the vector field from results by default
  (`include_vectors=false`) to keep payloads small.
- Requires a cluster tier with Atlas Vector Search and a pre-created
  vector index (`list_search_indexes` helps discover it).

## Maintainer

ModuleX core team.
