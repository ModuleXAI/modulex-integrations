"""Qdrant integration manifest.

Connection-style auth: instance base URL + optional API key. None of
our single-credential auth_types fit, so the integration uses
``CustomAuthSchema``; the tool body reads ``base_url`` and ``api_key``
straight out of ``auth_data``.
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


def _collection_param() -> ParameterDef:
    return ParameterDef(
        type="string", description="Name of the Qdrant collection", required=True
    )


manifest = IntegrationManifest(
    name="qdrant",
    display_name="Qdrant",
    description=(
        "High-performance vector database with advanced filtering "
        "capabilities for semantic search. Pass-through access to your "
        "own Qdrant instance: vector similarity search, collection "
        "management, and point upsert/delete via the native REST API."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:qdrant-icon",
    app_url="https://qdrant.tech",
    categories=["Vector Database", "semantic-search"],
    actions=[
        ActionDefinition(
            name="query",
            description=(
                "Vector similarity search on a Qdrant collection. Send "
                "query_vector (works on every Qdrant instance), OR "
                "query_text + model to have Qdrant Cloud embed the text "
                "server-side (Cloud inference feature only — plain "
                "self-hosted Qdrant requires a vector). Returns Qdrant's "
                "native scored points."
            ),
            parameters={
                "collection_name": _collection_param(),
                "query_vector": ParameterDef(
                    type="array",
                    description="Query embedding vector",
                ),
                "query_text": ParameterDef(
                    type="string",
                    description=(
                        "Text to embed server-side (Qdrant Cloud inference "
                        "only; requires model)"
                    ),
                ),
                "model": ParameterDef(
                    type="string",
                    description=(
                        "Inference model used to embed query_text "
                        "(Qdrant Cloud only)"
                    ),
                ),
                "using": ParameterDef(
                    type="string",
                    description="Named vector to search against",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=5,
                ),
                "score_threshold": ParameterDef(
                    type="number",
                    description="Minimum similarity score threshold",
                ),
                "filter": ParameterDef(
                    type="object",
                    description="Qdrant filter conditions (must/should/must_not)",
                ),
                "with_payload": ParameterDef(
                    type="boolean",
                    description="Include payload in results",
                    default=True,
                ),
                "with_vector": ParameterDef(
                    type="boolean",
                    description="Include vectors in results",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="list_collections",
            description="List all collections in the Qdrant instance.",
            parameters={},
        ),
        ActionDefinition(
            name="get_collection_info",
            description=(
                "Get native info about a collection (status, points_count, "
                "vector config, payload schema)."
            ),
            parameters={"collection_name": _collection_param()},
        ),
        ActionDefinition(
            name="upsert_points",
            description=(
                "Insert or update points in a collection. Each point is a "
                "Qdrant-native {id, vector, payload?} object; on Qdrant "
                "Cloud with inference, vector may be a {text, model} "
                "document embedded server-side."
            ),
            parameters={
                "collection_name": _collection_param(),
                "points": ParameterDef(
                    type="array",
                    description="Points to upsert ({id, vector, payload?} objects)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_points",
            description="Delete points from a collection by ID list or by filter.",
            parameters={
                "collection_name": _collection_param(),
                "point_ids": ParameterDef(
                    type="array",
                    description="Point IDs to delete (numbers or UUID strings)",
                ),
                "filter": ParameterDef(
                    type="object",
                    description="Qdrant filter selecting the points to delete",
                ),
            },
        ),
        ActionDefinition(
            name="create_collection",
            description="Create a collection with a single unnamed vector config.",
            parameters={
                "collection_name": _collection_param(),
                "vector_size": ParameterDef(
                    type="integer",
                    description="Dimensionality of the vectors",
                    required=True,
                ),
                "distance": ParameterDef(
                    type="string",
                    description="Distance metric: Cosine, Euclid, Dot, Manhattan",
                    default="Cosine",
                ),
            },
        ),
        ActionDefinition(
            name="delete_collection",
            description="Delete a collection and all its points.",
            parameters={"collection_name": _collection_param()},
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Qdrant Connection",
            description=(
                "Connect to your Qdrant instance using its URL and an "
                "optional API key."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="QDRANT_BASE_URL",
                    display_name="Qdrant URL",
                    description=(
                        "URL of your Qdrant instance, scheme + host (+ port "
                        "for self-hosted), no trailing slash"
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="https://xyz-abc.aws.cloud.qdrant.io:6333",
                ),
                EnvVar(
                    name="QDRANT_API_KEY",
                    display_name="API Key",
                    description=(
                        "API key for Qdrant Cloud (optional for unsecured "
                        "self-hosted instances)"
                    ),
                    required=False,
                    sensitive=True,
                    sample_format="qdrant-api-key-...",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="{QDRANT_BASE_URL}/collections",
                method="GET",
                headers={
                    "api-key": "{QDRANT_API_KEY}",
                    "Content-Type": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["result"]
                ),
                cost_level="free",
                description="Validates the connection by listing collections.",
            ),
        ),
    ],
)
