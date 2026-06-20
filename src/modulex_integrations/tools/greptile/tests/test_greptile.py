"""Happy-path tests per action + failure-path and empty-credential tests.

Greptile returns proper HTTP status codes; the tools wrap everything in
try/except so non-2xx and timeouts surface as ``success=False`` + ``error``
rather than raising.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.greptile import (
    TOOLS,
    index_repo,
    manifest,
    query,
    search,
    status,
)
from modulex_integrations.tools.greptile.outputs import (
    IndexRepositoryOutput,
    QueryOutput,
    SearchOutput,
    StatusOutput,
)

API = "https://api.greptile.com/v2"
_API_KEY = "fake-api-key"
_GH_TOKEN = "fake-github-token"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, github_token=_GH_TOKEN, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_single_api_key_schema(self) -> None:
        # BYOK only: exactly one auth schema, no managed key.
        assert len(manifest.auth_schemas) == 1


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_query(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/query",
        json={
            "message": "Authentication is handled in auth/middleware.ts.",
            "sources": [
                {
                    "repository": "owner/repo",
                    "remote": "github",
                    "branch": "main",
                    "filepath": "src/auth/middleware.ts",
                    "linestart": 10,
                    "lineend": 42,
                    "summary": "JWT validation middleware",
                    "distance": 0.12,
                }
            ],
        },
    )

    result_dict = await query.ainvoke(
        _args(query="How does auth work?", repositories="owner/repo")
    )

    assert isinstance(result_dict, dict)

    result = QueryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message == "Authentication is handled in auth/middleware.ts."
    assert result.sources[0].filepath == "src/auth/middleware.ts"
    assert result.sources[0].linestart == 10
    assert result.sources[0].distance == 0.12

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"
    assert sent.headers["X-GitHub-Token"] == _GH_TOKEN


@pytest.mark.asyncio
async def test_search(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search",
        json={
            "sources": [
                {
                    "repository": "owner/repo",
                    "remote": "github",
                    "branch": "main",
                    "filepath": "src/db/connection.ts",
                    "linestart": 1,
                    "lineend": 20,
                    "summary": "Database connection pool",
                    "distance": 0.05,
                }
            ]
        },
    )

    result_dict = await search.ainvoke(
        _args(query="database connection", repositories="owner/repo")
    )

    assert isinstance(result_dict, dict)

    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sources[0].filepath == "src/db/connection.ts"
    assert result.sources[0].distance == 0.05


@pytest.mark.asyncio
async def test_index_repo(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/repositories",
        json={
            "statusEndpoint": (
                "https://api.greptile.com/v2/repositories/"
                "github%3Amain%3Aowner%2Frepo"
            ),
            "message": "Repository submitted for indexing",
        },
    )

    result_dict = await index_repo.ainvoke(
        _args(remote="github", repository="owner/repo", branch="main")
    )

    assert isinstance(result_dict, dict)

    result = IndexRepositoryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.repository_id == "github:main:owner/repo"
    assert result.message == "Repository submitted for indexing"


@pytest.mark.asyncio
async def test_index_repo_falls_back_to_constructed_id(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/repositories",
        json={"message": "Repository submitted for indexing"},
    )

    result_dict = await index_repo.ainvoke(
        _args(remote="github", repository="owner/repo", branch="dev")
    )

    result = IndexRepositoryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.repository_id == "github:dev:owner/repo"


@pytest.mark.asyncio
async def test_status(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repositories/github%3Amain%3Aowner%2Frepo",
        json={
            "repository": "owner/repo",
            "remote": "github",
            "branch": "main",
            "private": False,
            "status": "completed",
            "filesProcessed": 120,
            "numFiles": 120,
            "sampleQuestions": ["How does routing work?"],
            "sha": "abc123",
        },
    )

    result_dict = await status.ainvoke(
        _args(remote="github", repository="owner/repo", branch="main")
    )

    assert isinstance(result_dict, dict)

    result = StatusOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "completed"
    assert result.files_processed == 120
    assert result.num_files == 120
    assert result.sample_questions == ["How does routing work?"]
    assert result.sha == "abc123"


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_query_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/query",
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await query.ainvoke(
        _args(query="anything", repositories="owner/repo")
    )

    assert isinstance(result_dict, dict)

    result = QueryOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_query_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await query.ainvoke(
        {
            "query": "x",
            "repositories": "owner/repo",
            "api_key": "",
            "github_token": _GH_TOKEN,
        }
    )

    assert isinstance(result_dict, dict)

    result = QueryOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_status_validates_empty_github_token() -> None:
    """Empty github_token short-circuits before the HTTP call."""
    result_dict = await status.ainvoke(
        {
            "remote": "github",
            "repository": "owner/repo",
            "branch": "main",
            "api_key": _API_KEY,
            "github_token": "",
        }
    )

    assert isinstance(result_dict, dict)

    result = StatusOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "GitHub token" in result.error
