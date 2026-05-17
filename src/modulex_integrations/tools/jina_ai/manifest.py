"""Jina AI integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ModulexKeyAuthSchema,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


def _embeddings_test_endpoint(description: str) -> TestEndpoint:
    return TestEndpoint(
        url="https://api.jina.ai/v1/embeddings",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer {api_key}",
        },
        body={"model": "jina-embeddings-v3", "input": ["test"]},
        success_indicators=SuccessIndicators(
            status_codes=[200], response_fields=["data"]
        ),
        cost_level="minimal",
        description=description,
    )


manifest = IntegrationManifest(
    name="jina_ai",
    display_name="Jina AI",
    description=(
        "AI-powered search foundation with embeddings, reranking, web "
        "reading, search, deep research, text segmentation, and zero-shot "
        "classification capabilities."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:jina_ai-themed",
    app_url="https://jina.ai",
    categories=[
        "Web Search & Scraping",
        "ai",
        "embeddings",
        "nlp",
        "research",
    ],
    actions=[
        ActionDefinition(
            name="generate_embeddings",
            description=(
                "Generate embeddings for text or images. Converts inputs to "
                "fixed-length vectors for semantic search, similarity "
                "matching, clustering, and RAG applications."
            ),
            parameters={
                "input": ParameterDef(
                    type="array",
                    description=(
                        "Array of input strings or objects with 'text', "
                        "'image', or 'pdf' keys"
                    ),
                    required=True,
                ),
                "model": ParameterDef(
                    type="string",
                    description="Embedding model to use",
                    default="jina-embeddings-v3",
                ),
                "task": ParameterDef(
                    type="string", description="Task optimization type"
                ),
                "dimensions": ParameterDef(
                    type="integer",
                    description="Truncate embeddings to specified size",
                ),
                "late_chunking": ParameterDef(
                    type="boolean",
                    description="Enable late chunking mode",
                    default=False,
                ),
                "truncate": ParameterDef(
                    type="boolean",
                    description="Auto-truncate content beyond max length",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="rerank_documents",
            description=(
                "Re-rank documents by relevance to a query. Improves search "
                "result relevance for RAG and search applications."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Search query to rank documents against",
                    required=True,
                ),
                "documents": ParameterDef(
                    type="array",
                    description="Documents to rerank (strings or objects)",
                    required=True,
                ),
                "model": ParameterDef(
                    type="string",
                    description="Reranker model to use",
                    default="jina-reranker-v2-base-multilingual",
                ),
                "top_n": ParameterDef(
                    type="integer", description="Number of top results to return"
                ),
                "return_documents": ParameterDef(
                    type="boolean",
                    description="Include document text in response",
                    default=True,
                ),
            },
        ),
        ActionDefinition(
            name="read_webpage",
            description=(
                "Read and parse web content in LLM-friendly format. Extracts "
                "structured content from web pages optimized for AI processing."
            ),
            parameters={
                "url": ParameterDef(
                    type="string",
                    description="The URL to read and parse",
                    required=True,
                ),
                "return_format": ParameterDef(
                    type="string",
                    description="Output format",
                    default="markdown",
                ),
                "target_selector": ParameterDef(
                    type="string",
                    description="CSS selectors to focus on specific elements",
                ),
                "remove_selector": ParameterDef(
                    type="string",
                    description="CSS selectors to exclude from page",
                ),
                "wait_for_selector": ParameterDef(
                    type="string",
                    description="CSS selectors to wait for before returning",
                ),
                "with_links_summary": ParameterDef(
                    type="boolean",
                    description="Gather all links at the end of response",
                    default=False,
                ),
                "with_images_summary": ParameterDef(
                    type="boolean",
                    description="Gather all images at the end of response",
                    default=False,
                ),
                "timeout": ParameterDef(
                    type="integer",
                    description="Maximum time in seconds to wait for webpage to load",
                ),
                "no_cache": ParameterDef(
                    type="boolean",
                    description="Bypass cache for fresh retrieval",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="web_search",
            description=(
                "Search the web with LLM-optimized results. Returns search "
                "results in formats optimized for AI and enterprise search."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="The search query to execute",
                    required=True,
                ),
                "site": ParameterDef(
                    type="string",
                    description="Limit search to specific domain (e.g. 'github.com')",
                ),
                "return_format": ParameterDef(
                    type="string",
                    description="Output format",
                    default="markdown",
                ),
                "num": ParameterDef(
                    type="integer", description="Maximum number of results to return"
                ),
                "gl": ParameterDef(
                    type="string",
                    description="Two-letter country code for localized results",
                ),
                "hl": ParameterDef(
                    type="string", description="Two-letter language code for search"
                ),
                "with_links_summary": ParameterDef(
                    type="boolean", description="Include links summary", default=False
                ),
                "with_images_summary": ParameterDef(
                    type="boolean", description="Include images summary", default=False
                ),
                "no_cache": ParameterDef(
                    type="boolean",
                    description="Bypass cache for real-time data",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="deep_search",
            description=(
                "Perform comprehensive research combining web searching, "
                "reading, and reasoning. Acts as a research agent for "
                "thorough investigation."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Research query or question to investigate",
                    required=True,
                ),
                "reasoning_effort": ParameterDef(
                    type="string",
                    description="Reasoning effort level (low, medium, high)",
                    default="medium",
                ),
                "budget_tokens": ParameterDef(
                    type="integer",
                    description=(
                        "Maximum tokens for the process (overrides "
                        "reasoning_effort)"
                    ),
                ),
                "max_attempts": ParameterDef(
                    type="integer",
                    description="Maximum retries for problem solving",
                ),
                "no_direct_answer": ParameterDef(
                    type="boolean",
                    description="Force deeper search even for simple queries",
                    default=False,
                ),
                "max_returned_urls": ParameterDef(
                    type="integer", description="Maximum URLs in final answer"
                ),
                "boost_hostnames": ParameterDef(
                    type="array",
                    description="Domains to prioritize for content retrieval",
                ),
                "bad_hostnames": ParameterDef(
                    type="array",
                    description="Domains to exclude from content retrieval",
                ),
                "only_hostnames": ParameterDef(
                    type="array",
                    description="Only retrieve content from these domains",
                ),
            },
        ),
        ActionDefinition(
            name="segment_text",
            description=(
                "Tokenize and segment text into chunks. Useful for counting "
                "tokens and preparing text for embedding in RAG applications."
            ),
            parameters={
                "content": ParameterDef(
                    type="string",
                    description="Text content to segment",
                    required=True,
                ),
                "tokenizer": ParameterDef(
                    type="string",
                    description="Tokenizer to use",
                    default="cl100k_base",
                ),
                "return_tokens": ParameterDef(
                    type="boolean",
                    description="Include tokens and IDs in response",
                    default=False,
                ),
                "return_chunks": ParameterDef(
                    type="boolean",
                    description="Segment into semantic chunks",
                    default=True,
                ),
                "max_chunk_length": ParameterDef(
                    type="integer",
                    description="Maximum characters per chunk",
                    default=1000,
                ),
                "head": ParameterDef(
                    type="integer",
                    description="Return only first N tokens (exclusive with tail)",
                ),
                "tail": ParameterDef(
                    type="integer",
                    description="Return only last N tokens (exclusive with head)",
                ),
            },
        ),
        ActionDefinition(
            name="classify",
            description=(
                "Zero-shot classification for text or images. Classifies "
                "content into provided categories without training."
            ),
            parameters={
                "input": ParameterDef(
                    type="array",
                    description="Array of texts or image objects to classify",
                    required=True,
                ),
                "labels": ParameterDef(
                    type="array",
                    description="List of classification categories",
                    required=True,
                ),
                "model": ParameterDef(
                    type="string",
                    description="Classification model",
                    default="jina-embeddings-v3",
                ),
                "classifier_id": ParameterDef(
                    type="string",
                    description="Existing classifier ID to reuse",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description=(
                "Authenticate using your Jina AI API key. Get your free "
                "API key at https://jina.ai/?sui=apikey"
            ),
            setup_environment_variables=[
                EnvVar(
                    name="JINA_API_KEY",
                    display_name="Jina AI API Key",
                    description=(
                        "Your Jina AI API key for authentication. Get your "
                        "free key at https://jina.ai/?sui=apikey"
                    ),
                    required=True,
                    sensitive=True,
                    sample_format="jina_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://jina.ai/?sui=apikey",
                ),
            ],
            test_endpoint=_embeddings_test_endpoint(
                "Validates API key with a minimal embeddings request"
            ),
        ),
        ModulexKeyAuthSchema(
            display_name="ModuleX Managed Key",
            description=(
                "Use ModuleX's managed API keys with usage tracked against "
                "your weekly credit limit"
            ),
            setup_environment_variables=[],
            test_endpoint=_embeddings_test_endpoint(
                "Validates system API key with a minimal embeddings request"
            ),
        ),
    ],
)
