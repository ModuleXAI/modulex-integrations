# Weaviate

Pass-through integration for the [Weaviate](https://weaviate.io) vector
database: similarity search via the native GraphQL `Get` API, schema
management and object insert/delete via the REST API, against your own
Weaviate Cloud or self-hosted instance.

## Authentication

- **`custom` auth_type** (instance URL + optional API key).
- Env vars: `WEAVIATE_BASE_URL` (required — scheme + host, e.g.
  `https://your-cluster.weaviate.cloud`) and `WEAVIATE_API_KEY`
  (required for Weaviate Cloud, optional for anonymous-access local
  instances).
- Get a Cloud API key from the [Weaviate Cloud
  console](https://console.weaviate.cloud) under cluster details.

## Tools

| name | description | required params |
| --- | --- | --- |
| `query` | GraphQL `Get` similarity search. `query_vector` (nearVector) works on every class; `query_text` (nearText) ONLY on classes with a vectorizer module. | `class_name` |
| `list_classes` | List all classes in the schema. | — |
| `get_class_stats` | Object count via GraphQL `Aggregate`. | `class_name` |
| `insert_object` | Insert one object (vector optional with a vectorizer). | `class_name`, `properties` |
| `delete_object` | Delete one object by UUID. | `class_name`, `object_id` |
| `create_class` | Create a class (description/vectorizer/properties optional). | `class_name` |
| `delete_class` | Delete a class and ALL its objects. | `class_name` |

## Limits & Quotas

- 30s request timeout per call.
- No ModuleX-side embedding: `query_text` relies on the class's own
  vectorizer module; classes without one require `query_vector`.
- GraphQL identifiers (class and property names) must match
  `[A-Za-z][A-Za-z0-9_]*`; the `where` filter is serialized from JSON
  with the `operator` field emitted as a GraphQL enum.
- Responses are Weaviate's native shapes (`data.Get.<Class>` objects
  with `_additional`, schema class arrays) — no normalization.
- Rate limits are those of your own Weaviate instance/cluster.

## Maintainer

ModuleX core team.
