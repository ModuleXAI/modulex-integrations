"""Jina AI integration."""
from modulex_integrations.tools.jina_ai.manifest import manifest
from modulex_integrations.tools.jina_ai.tools import (
    classify,
    deep_search,
    generate_embeddings,
    read_webpage,
    rerank_documents,
    segment_text,
    web_search,
)

TOOLS = (
    generate_embeddings,
    rerank_documents,
    read_webpage,
    web_search,
    deep_search,
    segment_text,
    classify,
)

__all__ = [
    "TOOLS",
    "classify",
    "deep_search",
    "generate_embeddings",
    "manifest",
    "read_webpage",
    "rerank_documents",
    "segment_text",
    "web_search",
]
