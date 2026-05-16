"""Tests for the Jina AI integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.jina_ai import (
    TOOLS,
    classify,
    deep_search,
    generate_embeddings,
    manifest,
    read_webpage,
    rerank_documents,
    segment_text,
    web_search,
)
from modulex_integrations.tools.jina_ai.outputs import (
    ClassifyOutput,
    DeepSearchOutput,
    GenerateEmbeddingsOutput,
    ReadWebpageOutput,
    RerankDocumentsOutput,
    SegmentTextOutput,
    WebSearchOutput,
)

_API_KEY = "jina-fake-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


class TestManifest:
    def test_manifest_exposes_seven_actions(self) -> None:
        assert len(manifest.actions) == 7

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_paired_api_key_and_modulex_key_auth(self) -> None:
        types = {a.auth_type for a in manifest.auth_schemas}
        assert types == {"api_key", "modulex_key"}


@pytest.mark.asyncio
async def test_generate_embeddings(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.jina.ai/v1/embeddings",
        json={
            "model": "jina-embeddings-v3",
            "object": "list",
            "usage": {"total_tokens": 1, "prompt_tokens": 1},
            "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
        },
    )

    result_dict = await generate_embeddings.ainvoke(_args(input=["hello"]))
    assert isinstance(result_dict, dict)
    result = GenerateEmbeddingsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None
    assert result.data["data"][0]["embedding"] == [0.1, 0.2]


@pytest.mark.asyncio
async def test_generate_embeddings_api_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.jina.ai/v1/embeddings",
        status_code=429,
        json={"error": {"message": "rate limit exceeded"}},
    )
    result = GenerateEmbeddingsOutput.model_validate(
        await generate_embeddings.ainvoke(_args(input=["hello"]))
    )
    assert result.success is False
    assert result.error is not None and "rate limit" in result.error


@pytest.mark.asyncio
async def test_rerank_documents(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.jina.ai/v1/rerank",
        json={
            "model": "jina-reranker-v2-base-multilingual",
            "object": "list",
            "usage": {"total_tokens": 3},
            "results": [
                {"index": 0, "relevance_score": 0.9, "document": "first"},
                {"index": 1, "relevance_score": 0.4, "document": "second"},
            ],
        },
    )
    result = RerankDocumentsOutput.model_validate(
        await rerank_documents.ainvoke(
            _args(query="q", documents=["first", "second"], top_n=2)
        )
    )
    assert result.success is True
    assert result.data is not None
    assert len(result.data["results"]) == 2


@pytest.mark.asyncio
async def test_read_webpage_flattens_data(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://r.jina.ai/",
        json={
            "data": {
                "title": "Example",
                "description": "An example domain",
                "url": "https://example.com",
                "content": "# Example",
                "links": {"home": "https://example.com"},
                "images": None,
                "usage": {"tokens": 42},
            }
        },
    )

    result = ReadWebpageOutput.model_validate(
        await read_webpage.ainvoke(_args(url="https://example.com"))
    )
    assert result.success is True
    assert result.title == "Example"
    assert result.content == "# Example"
    assert result.links == {"home": "https://example.com"}
    assert result.usage == {"tokens": 42}


@pytest.mark.asyncio
async def test_web_search_extracts_results(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://s.jina.ai/",
        json={
            "data": [
                {"title": "R1", "url": "https://x", "description": "first"},
                {"title": "R2", "url": "https://y", "description": "second"},
            ]
        },
    )
    result = WebSearchOutput.model_validate(
        await web_search.ainvoke(_args(query="ai papers", site="github.com"))
    )
    assert result.success is True
    assert result.count == 2
    assert result.results[0]["title"] == "R1"


@pytest.mark.asyncio
async def test_deep_search(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://deepsearch.jina.ai/v1/chat/completions",
        json={
            "id": "dsr-1",
            "object": "chat.completion",
            "created": 1759000000,
            "model": "jina-deepsearch-v1",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "answer", "type": "text"},
                    "logprobs": None,
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
            "visitedURLs": ["https://example.com"],
        },
    )
    result = DeepSearchOutput.model_validate(
        await deep_search.ainvoke(_args(query="how does retrieval work"))
    )
    assert result.success is True
    assert result.data is not None
    assert result.data["choices"][0]["message"]["content"] == "answer"


@pytest.mark.asyncio
async def test_segment_text(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://segment.jina.ai/",
        json={
            "num_tokens": 5,
            "num_chunks": 2,
            "chunks": ["hello ", "world"],
            "chunk_positions": [[0, 6], [6, 11]],
            "tokens": None,
            "tokenizer": "cl100k_base",
            "usage": {"tokens": 5},
        },
    )
    result = SegmentTextOutput.model_validate(
        await segment_text.ainvoke(_args(content="hello world"))
    )
    assert result.success is True
    assert result.num_tokens == 5
    assert result.chunks == ["hello ", "world"]


@pytest.mark.asyncio
async def test_classify(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.jina.ai/v1/classify",
        json={
            "data": [
                {
                    "object": "classification",
                    "index": 0,
                    "prediction": "positive",
                    "score": 0.95,
                    "predictions": [
                        {"label": "positive", "score": 0.95},
                        {"label": "negative", "score": 0.05},
                    ],
                }
            ],
            "usage": {"total_tokens": 7},
        },
    )
    result = ClassifyOutput.model_validate(
        await classify.ainvoke(
            _args(input=["I love this"], labels=["positive", "negative"])
        )
    )
    assert result.success is True
    assert result.classifications[0]["prediction"] == "positive"


@pytest.mark.asyncio
async def test_classify_uses_classifier_id_when_present(httpx_mock: Any) -> None:
    # When classifier_id is given, `model` must NOT be in the payload.
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json
        captured.update(json.loads(request.content.decode()))
        from httpx import Response
        return Response(200, json={"data": [], "usage": {}})

    httpx_mock.add_callback(_capture, method="POST", url="https://api.jina.ai/v1/classify")
    await classify.ainvoke(
        _args(input=["x"], labels=["a", "b"], classifier_id="clf-1")
    )
    assert captured.get("classifier_id") == "clf-1"
    assert "model" not in captured


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result = GenerateEmbeddingsOutput.model_validate(
        await generate_embeddings.ainvoke({"api_key": "", "input": ["x"]})
    )
    assert result.success is False
    assert result.error is not None and "API key" in result.error
