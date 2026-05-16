"""Jina AI LangChain ``@tool`` functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.jina_ai.outputs import (
    ClassifyOutput,
    DeepSearchOutput,
    GenerateEmbeddingsOutput,
    ReadWebpageOutput,
    RerankDocumentsOutput,
    SegmentTextOutput,
    WebSearchOutput,
)

__all__ = [
    "classify",
    "deep_search",
    "generate_embeddings",
    "read_webpage",
    "rerank_documents",
    "segment_text",
    "web_search",
]

# Jina splits its API across multiple subdomains.
_EMBEDDINGS_URL = "https://api.jina.ai/v1/embeddings"
_RERANK_URL = "https://api.jina.ai/v1/rerank"
_READER_URL = "https://r.jina.ai/"
_SEARCH_URL = "https://s.jina.ai/"
_DEEPSEARCH_URL = "https://deepsearch.jina.ai/v1/chat/completions"
_SEGMENT_URL = "https://segment.jina.ai/"
_CLASSIFY_URL = "https://api.jina.ai/v1/classify"

_TIMEOUT = 60.0
_LONG_TIMEOUT = 120.0
_DEEP_TIMEOUT = 300.0  # deepsearch can take minutes


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _empty_key_error(name: str) -> str:
    return (
        f"Jina AI API key is empty for {name}. "
        "Get your key at https://jina.ai/?sui=apikey"
    )


def _extract_error(response: httpx.Response) -> str:
    try:
        body = response.json()
    except Exception:
        return response.text
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            msg = err.get("message")
            if msg:
                return str(msg)
        if isinstance(err, str) and err:
            return err
        if "detail" in body:
            return str(body["detail"])
    return response.text


async def _post(
    url: str,
    api_key: str,
    json_body: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout: float = _TIMEOUT,
) -> tuple[bool, str | None, dict[str, Any] | None]:
    merged = headers if headers is not None else _headers(api_key)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=merged, json=json_body)
        if response.status_code != 200:
            return (
                False,
                f"API error ({response.status_code}): {_extract_error(response)}",
                None,
            )
        body = response.json() or {}
    except Exception as exc:
        return False, f"Request failed: {exc}", None
    if not isinstance(body, dict):
        return True, None, {"value": body}
    return True, None, body


# --- Input schemas ---------------------------------------------------------


class EmbeddingsInput(BaseModel):
    api_key: str = Field(description="Jina AI API key (provided by credential system)")
    input: list[str | dict[str, Any]] = Field(description="Inputs to embed")
    model: str = Field(default="jina-embeddings-v3", description="Embedding model")
    task: str | None = Field(default=None, description="Task optimization type")
    dimensions: int | None = Field(default=None, description="Embedding size truncation")
    late_chunking: bool = Field(default=False, description="Late chunking mode")
    truncate: bool = Field(default=False, description="Auto-truncate input")


class RerankInput(BaseModel):
    api_key: str = Field(description="Jina AI API key (provided by credential system)")
    query: str = Field(description="Search query to rank documents against")
    documents: list[str | dict[str, Any]] = Field(description="Documents to rerank")
    model: str = Field(
        default="jina-reranker-v2-base-multilingual", description="Reranker model"
    )
    top_n: int | None = Field(default=None, description="Number of top results")
    return_documents: bool = Field(default=True, description="Include document text")


class ReaderInput(BaseModel):
    api_key: str = Field(description="Jina AI API key (provided by credential system)")
    url: str = Field(description="URL to read")
    return_format: str = Field(default="markdown", description="Output format")
    target_selector: str | None = Field(default=None, description="CSS focus selectors")
    remove_selector: str | None = Field(default=None, description="CSS exclude selectors")
    wait_for_selector: str | None = Field(default=None, description="CSS wait selectors")
    with_links_summary: bool = Field(default=False, description="Include links summary")
    with_images_summary: bool = Field(default=False, description="Include images summary")
    timeout: int | None = Field(default=None, description="Max wait seconds")
    no_cache: bool = Field(default=False, description="Bypass cache")


class SearchInput(BaseModel):
    api_key: str = Field(description="Jina AI API key (provided by credential system)")
    query: str = Field(description="Search query")
    site: str | None = Field(default=None, description="Limit to a specific domain")
    return_format: str = Field(default="markdown", description="Output format")
    num: int | None = Field(default=None, description="Maximum results")
    gl: str | None = Field(default=None, description="Country code")
    hl: str | None = Field(default=None, description="Language code")
    with_links_summary: bool = Field(default=False, description="Include links summary")
    with_images_summary: bool = Field(default=False, description="Include images summary")
    no_cache: bool = Field(default=False, description="Bypass cache")


class DeepSearchInput(BaseModel):
    api_key: str = Field(description="Jina AI API key (provided by credential system)")
    query: str = Field(description="Research query")
    reasoning_effort: str = Field(default="medium", description="low/medium/high")
    budget_tokens: int | None = Field(default=None, description="Max process tokens")
    max_attempts: int | None = Field(default=None, description="Max retries")
    no_direct_answer: bool = Field(default=False, description="Force deeper search")
    max_returned_urls: int | None = Field(default=None, description="Max URLs in answer")
    boost_hostnames: list[str] | None = Field(default=None, description="Boost domains")
    bad_hostnames: list[str] | None = Field(default=None, description="Exclude domains")
    only_hostnames: list[str] | None = Field(default=None, description="Restrict to domains")


class SegmenterInput(BaseModel):
    api_key: str = Field(description="Jina AI API key (provided by credential system)")
    content: str = Field(description="Text content to segment")
    tokenizer: str = Field(default="cl100k_base", description="Tokenizer to use")
    return_tokens: bool = Field(default=False, description="Include tokens in response")
    return_chunks: bool = Field(default=True, description="Segment into chunks")
    max_chunk_length: int = Field(default=1000, description="Max chars per chunk")
    head: int | None = Field(default=None, description="Return first N tokens")
    tail: int | None = Field(default=None, description="Return last N tokens")


class ClassifyInput(BaseModel):
    api_key: str = Field(description="Jina AI API key (provided by credential system)")
    input: list[str | dict[str, Any]] = Field(description="Inputs to classify")
    labels: list[str] = Field(description="Classification labels")
    model: str = Field(default="jina-embeddings-v3", description="Classification model")
    classifier_id: str | None = Field(default=None, description="Existing classifier id")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=EmbeddingsInput)
@serialize_pydantic_return
async def generate_embeddings(
    api_key: str,
    input: list[str | dict[str, Any]],
    model: str = "jina-embeddings-v3",
    task: str | None = None,
    dimensions: int | None = None,
    late_chunking: bool = False,
    truncate: bool = False,
) -> GenerateEmbeddingsOutput:
    """Generate embeddings for text or images via Jina AI Embeddings API."""
    if not api_key or not api_key.strip():
        return GenerateEmbeddingsOutput(
            success=False, error=_empty_key_error("generate_embeddings")
        )

    payload: dict[str, Any] = {
        "model": model,
        "input": input,
        "late_chunking": late_chunking,
        "truncate": truncate,
    }
    if task:
        payload["task"] = task
    if dimensions:
        payload["dimensions"] = dimensions

    ok, err, data = await _post(_EMBEDDINGS_URL, api_key, payload)
    return GenerateEmbeddingsOutput(success=ok, error=err, data=data)


@tool(args_schema=RerankInput)
@serialize_pydantic_return
async def rerank_documents(
    api_key: str,
    query: str,
    documents: list[str | dict[str, Any]],
    model: str = "jina-reranker-v2-base-multilingual",
    top_n: int | None = None,
    return_documents: bool = True,
) -> RerankDocumentsOutput:
    """Re-rank documents by relevance to a query via Jina AI Reranker API."""
    if not api_key or not api_key.strip():
        return RerankDocumentsOutput(
            success=False, error=_empty_key_error("rerank_documents")
        )

    payload: dict[str, Any] = {
        "model": model,
        "query": query,
        "documents": documents,
        "return_documents": return_documents,
    }
    if top_n:
        payload["top_n"] = top_n

    ok, err, data = await _post(_RERANK_URL, api_key, payload)
    return RerankDocumentsOutput(success=ok, error=err, data=data)


@tool(args_schema=ReaderInput)
@serialize_pydantic_return
async def read_webpage(
    api_key: str,
    url: str,
    return_format: str = "markdown",
    target_selector: str | None = None,
    remove_selector: str | None = None,
    wait_for_selector: str | None = None,
    with_links_summary: bool = False,
    with_images_summary: bool = False,
    timeout: int | None = None,
    no_cache: bool = False,
) -> ReadWebpageOutput:
    """Read and parse web content via Jina AI Reader (``r.jina.ai``)."""
    if not api_key or not api_key.strip():
        return ReadWebpageOutput(success=False, error=_empty_key_error("read_webpage"))

    headers = _headers(api_key)
    headers["X-Return-Format"] = return_format
    if target_selector:
        headers["X-Target-Selector"] = target_selector
    if remove_selector:
        headers["X-Remove-Selector"] = remove_selector
    if wait_for_selector:
        headers["X-Wait-For-Selector"] = wait_for_selector
    if with_links_summary:
        headers["X-With-Links-Summary"] = "true"
    if with_images_summary:
        headers["X-With-Images-Summary"] = "true"
    if timeout:
        headers["X-Timeout"] = str(timeout)
    if no_cache:
        headers["X-No-Cache"] = "true"

    ok, err, body = await _post(
        _READER_URL, api_key, {"url": url}, headers=headers, timeout=_LONG_TIMEOUT
    )
    if not ok or body is None:
        return ReadWebpageOutput(success=False, error=err)

    inner = body.get("data", body) if isinstance(body, dict) else {}
    if not isinstance(inner, dict):
        inner = {}
    return ReadWebpageOutput(
        success=True,
        data=body,
        title=inner.get("title"),
        description=inner.get("description"),
        url=inner.get("url"),
        content=inner.get("content"),
        links=inner.get("links") if isinstance(inner.get("links"), dict) else None,
        images=inner.get("images") if isinstance(inner.get("images"), dict) else None,
        usage=inner.get("usage") if isinstance(inner.get("usage"), dict) else None,
    )


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def web_search(
    api_key: str,
    query: str,
    site: str | None = None,
    return_format: str = "markdown",
    num: int | None = None,
    gl: str | None = None,
    hl: str | None = None,
    with_links_summary: bool = False,
    with_images_summary: bool = False,
    no_cache: bool = False,
) -> WebSearchOutput:
    """Search the web with LLM-optimized results via Jina AI Search."""
    if not api_key or not api_key.strip():
        return WebSearchOutput(success=False, error=_empty_key_error("web_search"))

    headers = _headers(api_key)
    headers["X-Return-Format"] = return_format
    if site:
        headers["X-Site"] = site
    if with_links_summary:
        headers["X-With-Links-Summary"] = "true"
    if with_images_summary:
        headers["X-With-Images-Summary"] = "true"
    if no_cache:
        headers["X-No-Cache"] = "true"

    payload: dict[str, Any] = {"q": query}
    if num:
        payload["num"] = num
    if gl:
        payload["gl"] = gl
    if hl:
        payload["hl"] = hl

    ok, err, body = await _post(
        _SEARCH_URL, api_key, payload, headers=headers, timeout=_LONG_TIMEOUT
    )
    if not ok or body is None:
        return WebSearchOutput(success=False, error=err)

    data = body.get("data")
    if isinstance(data, list):
        return WebSearchOutput(success=True, data=body, results=data, count=len(data))
    return WebSearchOutput(success=True, data=body)


@tool(args_schema=DeepSearchInput)
@serialize_pydantic_return
async def deep_search(
    api_key: str,
    query: str,
    reasoning_effort: str = "medium",
    budget_tokens: int | None = None,
    max_attempts: int | None = None,
    no_direct_answer: bool = False,
    max_returned_urls: int | None = None,
    boost_hostnames: list[str] | None = None,
    bad_hostnames: list[str] | None = None,
    only_hostnames: list[str] | None = None,
) -> DeepSearchOutput:
    """Comprehensive research via Jina AI DeepSearch (non-streaming)."""
    if not api_key or not api_key.strip():
        return DeepSearchOutput(success=False, error=_empty_key_error("deep_search"))

    payload: dict[str, Any] = {
        "model": "jina-deepsearch-v1",
        "messages": [{"role": "user", "content": query}],
        "reasoning_effort": reasoning_effort,
        "stream": False,
    }
    if budget_tokens:
        payload["budget_tokens"] = budget_tokens
    if max_attempts:
        payload["max_attempts"] = max_attempts
    if no_direct_answer:
        payload["no_direct_answer"] = no_direct_answer
    if max_returned_urls:
        payload["max_returned_urls"] = max_returned_urls
    if boost_hostnames:
        payload["boost_hostnames"] = boost_hostnames
    if bad_hostnames:
        payload["bad_hostnames"] = bad_hostnames
    if only_hostnames:
        payload["only_hostnames"] = only_hostnames

    ok, err, data = await _post(_DEEPSEARCH_URL, api_key, payload, timeout=_DEEP_TIMEOUT)
    return DeepSearchOutput(success=ok, error=err, data=data)


@tool(args_schema=SegmenterInput)
@serialize_pydantic_return
async def segment_text(
    api_key: str,
    content: str,
    tokenizer: str = "cl100k_base",
    return_tokens: bool = False,
    return_chunks: bool = True,
    max_chunk_length: int = 1000,
    head: int | None = None,
    tail: int | None = None,
) -> SegmentTextOutput:
    """Tokenize and chunk text via Jina AI Segmenter."""
    if not api_key or not api_key.strip():
        return SegmentTextOutput(success=False, error=_empty_key_error("segment_text"))

    payload: dict[str, Any] = {
        "content": content,
        "tokenizer": tokenizer,
        "return_tokens": return_tokens,
        "return_chunks": return_chunks,
        "max_chunk_length": max_chunk_length,
    }
    if head:
        payload["head"] = head
    if tail:
        payload["tail"] = tail

    ok, err, body = await _post(_SEGMENT_URL, api_key, payload)
    if not ok or body is None:
        return SegmentTextOutput(success=False, error=err)

    return SegmentTextOutput(
        success=True,
        data=body,
        num_tokens=body.get("num_tokens"),
        num_chunks=body.get("num_chunks"),
        chunks=body.get("chunks"),
        chunk_positions=body.get("chunk_positions"),
        tokens=body.get("tokens") if return_tokens else None,
        tokenizer=body.get("tokenizer"),
        usage=body.get("usage") if isinstance(body.get("usage"), dict) else None,
    )


@tool(args_schema=ClassifyInput)
@serialize_pydantic_return
async def classify(
    api_key: str,
    input: list[str | dict[str, Any]],
    labels: list[str],
    model: str = "jina-embeddings-v3",
    classifier_id: str | None = None,
) -> ClassifyOutput:
    """Zero-shot classification via Jina AI Classifier."""
    if not api_key or not api_key.strip():
        return ClassifyOutput(success=False, error=_empty_key_error("classify"))

    payload: dict[str, Any] = {"input": input, "labels": labels}
    if classifier_id:
        payload["classifier_id"] = classifier_id
    else:
        payload["model"] = model

    ok, err, body = await _post(_CLASSIFY_URL, api_key, payload)
    if not ok or body is None:
        return ClassifyOutput(success=False, error=err)

    raw = body.get("data")
    classifications = raw if isinstance(raw, list) else []
    return ClassifyOutput(
        success=True,
        data=body,
        classifications=classifications,
        usage=body.get("usage") if isinstance(body.get("usage"), dict) else None,
    )
