"""MongoDB Atlas integration."""
from modulex_integrations.tools.mongodb_atlas.manifest import manifest
from modulex_integrations.tools.mongodb_atlas.tools import (
    delete_documents,
    insert_documents,
    list_collections,
    list_databases,
    list_search_indexes,
    query,
)

TOOLS = (
    query,
    list_databases,
    list_collections,
    list_search_indexes,
    insert_documents,
    delete_documents,
)

__all__ = [
    "TOOLS",
    "delete_documents",
    "insert_documents",
    "list_collections",
    "list_databases",
    "list_search_indexes",
    "manifest",
    "query",
]
