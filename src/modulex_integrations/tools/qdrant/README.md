# Qdrant

Pass-through integration for the [Qdrant](https://qdrant.tech) vector
database REST API: vector similarity search, collection management,
and point upsert/delete against your own Qdrant Cloud or self-hosted
instance.

## Authentication

- **`custom` auth_type** (instance URL + optional API key).
- Env vars: `QDRANT_BASE_URL` (required — scheme + host, plus port for
  self-hosted, e.g. `https://xyz.aws.cloud.qdrant.io:6333`) and
  `QDRANT_API_KEY` (required for Qdrant Cloud, optional for unsecured
  self-hosted instances).
- Get a Cloud API key from the [Qdrant Cloud
  console](https://cloud.qdrant.io) under Data Access Control.

## Tools

| name | description | required params |
| --- | --- | --- |
| `query` | Similarity search (`points/query`). `query_vector` works everywhere; `query_text` + `model` only on Qdrant Cloud with inference (self-hosted needs a vector). | `collection_name` |
| `list_collections` | List all collections. | — |
| `get_collection_info` | Native collection info (status, points_count, config). | `collection_name` |
| `upsert_points` | Insert/update native `{id, vector, payload?}` points. | `collection_name`, `points` |
| `delete_points` | Delete points by ID list or by filter. | `collection_name` |
| `create_collection` | Create a collection (single unnamed vector config). | `collection_name`, `vector_size` |
| `delete_collection` | Delete a collection and all its points. | `collection_name` |

## Limits & Quotas

- 30s request timeout per call.
- No ModuleX-side embedding: text queries (`query_text`) are embedded
  by Qdrant Cloud inference and require a `model` name; plain
  self-hosted instances must send `query_vector`.
- Responses are Qdrant's native shapes (scored points, update
  results) — no normalization.
- Rate limits are those of your own Qdrant instance/cluster.

## Maintainer

ModuleX core team.
