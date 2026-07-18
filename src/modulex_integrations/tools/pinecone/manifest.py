"""Pinecone integration manifest.

API-key auth carried as ``CustomAuthSchema`` (matching the other
vector-database integrations' connection-style credentials). The legacy
``environment`` field is gone: since Pinecone's serverless API, the
data-plane host is resolved per index via the control plane, so the API
key is the only credential needed.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


def _index_param() -> ParameterDef:
    return ParameterDef(
        type="string", description="Name of the Pinecone index", required=True
    )


manifest = IntegrationManifest(
    name="pinecone",
    display_name="Pinecone",
    description=(
        "Managed vector database for machine learning applications with "
        "serverless and pod-based deployments. Pass-through access to "
        "your own Pinecone project: vector similarity search, raw-text "
        "search on integrated-embedding indexes, index management, and "
        "vector upsert/delete via the native REST API."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:pinecone-icon",
    app_url="https://pinecone.io",
    categories=["Vector Database", "semantic-search", "ml-ops"],
    actions=[
        ActionDefinition(
            name="query",
            description=(
                "Vector similarity search on a Pinecone index. Takes a "
                "query vector — works on every index type. For raw-text "
                "queries, use search_records (integrated-embedding "
                "indexes only). Returns Pinecone's native matches."
            ),
            parameters={
                "index_name": _index_param(),
                "query_vector": ParameterDef(
                    type="array",
                    description="Query embedding vector",
                    required=True,
                ),
                "top_k": ParameterDef(
                    type="integer",
                    description="Number of results to return",
                    default=5,
                ),
                "namespace": ParameterDef(
                    type="string",
                    description="Namespace within the index",
                ),
                "filter": ParameterDef(
                    type="object",
                    description="Metadata filter conditions",
                ),
                "include_metadata": ParameterDef(
                    type="boolean",
                    description="Include metadata in results",
                    default=True,
                ),
                "include_values": ParameterDef(
                    type="boolean",
                    description="Include vector values in results",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="search_records",
            description=(
                "Raw-text semantic search — Pinecone embeds the text "
                "server-side. Works ONLY on indexes created with "
                "integrated embedding; for all other indexes use query "
                "with a vector. Returns Pinecone's native hits."
            ),
            parameters={
                "index_name": _index_param(),
                "query_text": ParameterDef(
                    type="string",
                    description="Text query (embedded server-side)",
                    required=True,
                ),
                "namespace": ParameterDef(
                    type="string",
                    description="Namespace within the index",
                    default="__default__",
                ),
                "top_k": ParameterDef(
                    type="integer",
                    description="Number of results to return",
                    default=5,
                ),
                "fields": ParameterDef(
                    type="array",
                    description="Record fields to return (default: all)",
                ),
                "filter": ParameterDef(
                    type="object",
                    description="Metadata filter conditions",
                ),
                "rerank": ParameterDef(
                    type="object",
                    description=(
                        "Optional native rerank spec "
                        "({model, rank_fields, top_n, ...})"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="list_indexes",
            description="List all indexes in the Pinecone project.",
            parameters={},
        ),
        ActionDefinition(
            name="describe_index",
            description=(
                "Get an index's native config (dimension, metric, host, "
                "spec, status)."
            ),
            parameters={"index_name": _index_param()},
        ),
        ActionDefinition(
            name="describe_index_stats",
            description=(
                "Get an index's stats (namespaces, dimension, "
                "totalVectorCount, indexFullness)."
            ),
            parameters={"index_name": _index_param()},
        ),
        ActionDefinition(
            name="upsert_vectors",
            description=(
                "Insert or update Pinecone-native {id, values, metadata?} "
                "vectors in an index."
            ),
            parameters={
                "index_name": _index_param(),
                "vectors": ParameterDef(
                    type="array",
                    description="Vectors to upsert ({id, values, metadata?})",
                    required=True,
                ),
                "namespace": ParameterDef(
                    type="string",
                    description="Namespace to upsert into",
                ),
            },
        ),
        ActionDefinition(
            name="delete_vectors",
            description=(
                "Delete vectors by ID list, by metadata filter, or all in "
                "a namespace."
            ),
            parameters={
                "index_name": _index_param(),
                "ids": ParameterDef(
                    type="array",
                    description="Vector IDs to delete",
                ),
                "namespace": ParameterDef(
                    type="string",
                    description="Namespace to delete from",
                ),
                "delete_all": ParameterDef(
                    type="boolean",
                    description="Delete every vector in the namespace",
                    default=False,
                ),
                "filter": ParameterDef(
                    type="object",
                    description="Metadata filter selecting vectors to delete",
                ),
            },
        ),
        ActionDefinition(
            name="create_index",
            description="Create a serverless index.",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Index name",
                    required=True,
                ),
                "dimension": ParameterDef(
                    type="integer",
                    description="Dimensionality of the vectors",
                    required=True,
                ),
                "metric": ParameterDef(
                    type="string",
                    description="Distance metric: cosine, euclidean, dotproduct",
                    default="cosine",
                ),
                "cloud": ParameterDef(
                    type="string",
                    description="Serverless cloud provider",
                    default="aws",
                ),
                "region": ParameterDef(
                    type="string",
                    description="Serverless region",
                    default="us-east-1",
                ),
            },
        ),
        ActionDefinition(
            name="delete_index",
            description="Delete an index.",
            parameters={"index_name": _index_param()},
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Pinecone API Key",
            description="Connect to Pinecone using your API key.",
            setup_environment_variables=[
                EnvVar(
                    name="PINECONE_API_KEY",
                    display_name="API Key",
                    description="Your Pinecone API key",
                    required=True,
                    sensitive=True,
                    sample_format="pcsk_...",
                    about_url="https://docs.pinecone.io/guides/projects/manage-api-keys",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.pinecone.io/indexes",
                method="GET",
                headers={
                    "Api-Key": "{PINECONE_API_KEY}",
                    "Content-Type": "application/json",
                    "X-Pinecone-Api-Version": "2025-01",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["indexes"]
                ),
                cost_level="free",
                description="Validates the API key by listing indexes.",
            ),
        ),
    ],
)
