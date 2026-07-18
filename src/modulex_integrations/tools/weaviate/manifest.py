"""Weaviate integration manifest.

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


def _class_param() -> ParameterDef:
    return ParameterDef(
        type="string",
        description="Name of the Weaviate class (collection)",
        required=True,
    )


manifest = IntegrationManifest(
    name="weaviate",
    display_name="Weaviate",
    description=(
        "Open-source vector database with built-in ML models and GraphQL "
        "API. Pass-through access to your own Weaviate instance: vector "
        "and text similarity search, schema management, and object "
        "insert/delete via the native GraphQL + REST APIs."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:weaviate-themed",
    app_url="https://weaviate.io",
    categories=["Vector Database", "semantic-search", "graphql"],
    actions=[
        ActionDefinition(
            name="query",
            description=(
                "Similarity search on a Weaviate class via GraphQL Get. "
                "Send query_vector (nearVector — works on every class), "
                "OR query_text (nearText — ONLY on classes configured "
                "with a vectorizer module that embeds text server-side; "
                "classes without a vectorizer require a vector). Returns "
                "Weaviate's native objects with _additional metadata."
            ),
            parameters={
                "class_name": _class_param(),
                "query_vector": ParameterDef(
                    type="array",
                    description="Query embedding vector (nearVector)",
                ),
                "query_text": ParameterDef(
                    type="string",
                    description=(
                        "Text query (nearText) — requires a vectorizer "
                        "module on the class"
                    ),
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=5,
                ),
                "certainty": ParameterDef(
                    type="number",
                    description="Minimum certainty threshold (0-1)",
                ),
                "distance": ParameterDef(
                    type="number",
                    description="Maximum distance threshold",
                ),
                "properties": ParameterDef(
                    type="array",
                    description="Object properties to return",
                ),
                "where": ParameterDef(
                    type="object",
                    description="Weaviate where-filter (path/operator/value*)",
                ),
                "include_vector": ParameterDef(
                    type="boolean",
                    description="Include object vectors in results",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="list_classes",
            description="List all classes (collections) in the Weaviate schema.",
            parameters={},
        ),
        ActionDefinition(
            name="get_class_stats",
            description="Get the object count of a class via GraphQL Aggregate.",
            parameters={"class_name": _class_param()},
        ),
        ActionDefinition(
            name="insert_object",
            description=(
                "Insert one object into a class. Omit vector when the "
                "class has a vectorizer module (server-side embedding)."
            ),
            parameters={
                "class_name": _class_param(),
                "properties": ParameterDef(
                    type="object",
                    description="Object properties",
                    required=True,
                ),
                "object_id": ParameterDef(
                    type="string",
                    description="Optional object UUID (server-generated if omitted)",
                ),
                "vector": ParameterDef(
                    type="array",
                    description="Object vector (omit with a vectorizer)",
                ),
            },
        ),
        ActionDefinition(
            name="delete_object",
            description="Delete one object by UUID.",
            parameters={
                "class_name": _class_param(),
                "object_id": ParameterDef(
                    type="string",
                    description="Object UUID",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_class",
            description="Create a class (collection) in the Weaviate schema.",
            parameters={
                "class_name": _class_param(),
                "description": ParameterDef(
                    type="string",
                    description="Class description",
                ),
                "vectorizer": ParameterDef(
                    type="string",
                    description=(
                        "Vectorizer module (e.g. text2vec-openai; omit for "
                        "none — then queries need vectors)"
                    ),
                ),
                "properties": ParameterDef(
                    type="array",
                    description=(
                        "Weaviate-native property definitions "
                        "({name, dataType, ...})"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="delete_class",
            description="Delete a class and ALL its objects.",
            parameters={"class_name": _class_param()},
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Weaviate Connection",
            description=(
                "Connect to your Weaviate instance using its URL and an "
                "optional API key."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="WEAVIATE_BASE_URL",
                    display_name="Weaviate URL",
                    description=(
                        "URL of your Weaviate instance, scheme + host, no "
                        "trailing slash"
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="https://your-cluster.weaviate.cloud",
                ),
                EnvVar(
                    name="WEAVIATE_API_KEY",
                    display_name="API Key",
                    description=(
                        "API key for Weaviate Cloud (optional for "
                        "anonymous-access local instances)"
                    ),
                    required=False,
                    sensitive=True,
                    sample_format="weaviate-api-key-...",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="{WEAVIATE_BASE_URL}/v1/schema",
                method="GET",
                headers={
                    "Authorization": "Bearer {WEAVIATE_API_KEY}",
                    "Content-Type": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["classes"]
                ),
                cost_level="free",
                description=(
                    "Validates the connection by fetching the schema "
                    "(requires authentication on Weaviate Cloud)."
                ),
            ),
        ),
    ],
)
