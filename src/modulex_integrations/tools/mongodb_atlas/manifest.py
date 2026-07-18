"""MongoDB Atlas integration manifest.

Database-connection auth: a single ``mongodb+srv://`` connection
string. None of our standard auth_types fit, so the integration uses
``CustomAuthSchema``. The tool body reads ``connection_string``
straight out of ``auth_data``.

Like PostgreSQL, MongoDB authenticates over its own wire protocol, not
HTTP — the test endpoint is a generic reachability check and real
credential validation happens on the first driver connection.
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


def _database_param() -> ParameterDef:
    return ParameterDef(type="string", description="Database name", required=True)


def _collection_param() -> ParameterDef:
    return ParameterDef(type="string", description="Collection name", required=True)


manifest = IntegrationManifest(
    name="mongodb_atlas",
    display_name="MongoDB Atlas",
    description=(
        "MongoDB Atlas with Vector Search: semantic search on your "
        "existing data via native $vectorSearch aggregations, plus "
        "database/collection introspection and document insert/delete. "
        "Uses the PyMongo async driver with your own connection string."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:mongodb-icon",
    app_url="https://mongodb.com/atlas",
    categories=["Vector Database", "document-database", "semantic-search"],
    actions=[
        ActionDefinition(
            name="query",
            description=(
                "Vector similarity search via an Atlas $vectorSearch "
                "aggregation. Takes a query VECTOR — Atlas has no "
                "server-side text embedding, so embed the query before "
                "calling. Returns native documents plus a score field, in "
                "MongoDB Relaxed Extended JSON."
            ),
            parameters={
                "database": _database_param(),
                "collection": _collection_param(),
                "index_name": ParameterDef(
                    type="string",
                    description="Atlas Vector Search index name",
                    required=True,
                ),
                "query_vector": ParameterDef(
                    type="array",
                    description="Query embedding vector",
                    required=True,
                ),
                "path": ParameterDef(
                    type="string",
                    description="Document field that holds the vectors",
                    required=True,
                ),
                "num_candidates": ParameterDef(
                    type="integer",
                    description="Candidates considered by the ANN search",
                    default=100,
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=5,
                ),
                "filter": ParameterDef(
                    type="object",
                    description="Pre-filter conditions (MQL format)",
                ),
                "include_vectors": ParameterDef(
                    type="boolean",
                    description="Keep the vector field in the results",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="list_databases",
            description="List all databases in the cluster.",
            parameters={},
        ),
        ActionDefinition(
            name="list_collections",
            description="List collections in a database (native entries).",
            parameters={"database": _database_param()},
        ),
        ActionDefinition(
            name="list_search_indexes",
            description=(
                "List Atlas Search / Vector Search indexes on a collection "
                "— discover the index name, vector path, and dimensions "
                "needed by query."
            ),
            parameters={
                "database": _database_param(),
                "collection": _collection_param(),
            },
        ),
        ActionDefinition(
            name="insert_documents",
            description="Insert documents into a collection.",
            parameters={
                "database": _database_param(),
                "collection": _collection_param(),
                "documents": ParameterDef(
                    type="array",
                    description="Documents to insert",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_documents",
            description=(
                "Delete documents matching a non-empty MQL filter (empty "
                "filters are rejected)."
            ),
            parameters={
                "database": _database_param(),
                "collection": _collection_param(),
                "filter": ParameterDef(
                    type="object",
                    description="MQL filter selecting documents to delete",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="MongoDB Atlas Connection",
            description="Connect using a MongoDB Atlas connection string.",
            setup_environment_variables=[
                EnvVar(
                    name="MONGODB_ATLAS_CONNECTION_STRING",
                    display_name="Connection String",
                    description=(
                        "MongoDB Atlas connection string (mongodb+srv://...) "
                        "for a database user with access to the target "
                        "databases"
                    ),
                    required=True,
                    sensitive=True,
                    sample_format="mongodb+srv://user:password@cluster.mongodb.net/",
                    about_url=(
                        "https://www.mongodb.com/docs/atlas/driver-connection/"
                    ),
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://www.mongodb.com/",
                method="GET",
                # MongoDB credentials authenticate over the native wire
                # protocol on a TCP socket — there is no HTTP endpoint
                # to validate a connection string. This check confirms
                # the public MongoDB site is reachable (a generic
                # connectivity sanity test). Real credentials are
                # validated by the driver's connection at first-call
                # time in tools.py.
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description=(
                    "Generic reachability check (mongodb.com). MongoDB "
                    "uses its own TCP protocol for auth, so HTTP "
                    "credential validation isn't possible — real auth "
                    "runs at first action call via the driver."
                ),
            ),
        ),
    ],
)
