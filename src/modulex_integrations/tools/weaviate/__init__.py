"""Weaviate integration."""
from modulex_integrations.tools.weaviate.manifest import manifest
from modulex_integrations.tools.weaviate.tools import (
    create_class,
    delete_class,
    delete_object,
    get_class_stats,
    insert_object,
    list_classes,
    query,
)

TOOLS = (
    query,
    list_classes,
    get_class_stats,
    insert_object,
    delete_object,
    create_class,
    delete_class,
)

__all__ = [
    "TOOLS",
    "create_class",
    "delete_class",
    "delete_object",
    "get_class_stats",
    "insert_object",
    "list_classes",
    "manifest",
    "query",
]
