"""Pinecone integration."""
from modulex_integrations.tools.pinecone.manifest import manifest
from modulex_integrations.tools.pinecone.tools import (
    create_index,
    delete_index,
    delete_vectors,
    describe_index,
    describe_index_stats,
    list_indexes,
    query,
    search_records,
    upsert_vectors,
)

TOOLS = (
    query,
    search_records,
    list_indexes,
    describe_index,
    describe_index_stats,
    upsert_vectors,
    delete_vectors,
    create_index,
    delete_index,
)

__all__ = [
    "TOOLS",
    "create_index",
    "delete_index",
    "delete_vectors",
    "describe_index",
    "describe_index_stats",
    "list_indexes",
    "manifest",
    "query",
    "search_records",
    "upsert_vectors",
]
