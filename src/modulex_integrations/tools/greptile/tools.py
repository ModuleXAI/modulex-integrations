"""Greptile LangChain ``@tool`` functions.

Four async tools wrapping the Greptile v2 REST API for AI-powered codebase
search and Q&A. The calling convention is *api_key*-based: the modulex
``ToolExecutor`` injects ``api_key: str`` (the Greptile API key, sent as a
Bearer token) directly. A second per-credential secret, ``github_token``
(sent as the ``X-GitHub-Token`` header so Greptile can clone private
repositories), is resolved from the same credential and injected by name.

Error model: every call is wrapped in try/except, returning the typed output
with ``success=False`` + ``error`` for non-2xx responses, timeouts, and
unexpected exceptions. Non-2xx HTTP responses do not raise.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.greptile.outputs import (
    IndexRepositoryOutput,
    QueryOutput,
    QuerySource,
    SearchOutput,
    StatusOutput,
)

__all__ = ["index_repo", "query", "search", "status"]

_GREPTILE_API_BASE = "https://api.greptile.com/v2"
_REQUEST_TIMEOUT = 120.0


# --- Auth + parsing helpers ------------------------------------------------


def _headers(api_key: str, github_token: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-GitHub-Token": github_token,
    }


def _parse_repositories(repo_string: str) -> list[dict[str, str]]:
    """Parse a comma-separated repository string into Greptile's structured form.

    Accepts ``github:branch:owner/repo`` or bare ``owner/repo`` (defaults to
    ``github:main``).
    """
    parsed: list[dict[str, str]] = []
    for raw in repo_string.split(","):
        repo = raw.strip()
        if not repo:
            continue
        parts = repo.split(":")
        if len(parts) == 3:
            parsed.append({"remote": parts[0], "branch": parts[1], "repository": parts[2]})
        else:
            parsed.append({"remote": "github", "branch": "main", "repository": repo})
    return parsed


def _parse_sources(data: dict[str, Any]) -> list[QuerySource]:
    raw_sources = data.get("sources")
    if raw_sources is None and isinstance(data, list):  # pragma: no cover - defensive
        raw_sources = data
    items: list[QuerySource] = []
    for source in raw_sources or []:
        if not isinstance(source, dict):
            continue
        items.append(
            QuerySource(
                repository=source.get("repository"),
                remote=source.get("remote"),
                branch=source.get("branch"),
                filepath=source.get("filepath"),
                linestart=source.get("linestart"),
                lineend=source.get("lineend"),
                summary=source.get("summary"),
                distance=source.get("distance"),
            )
        )
    return items


# --- Input schemas (args_schema for each @tool) ----------------------------


class QueryInput(BaseModel):
    query: str = Field(description="Natural language question about the codebase")
    repositories: str = Field(
        description=(
            "Comma-separated list of repositories. Format: 'github:branch:owner/repo' "
            "or just 'owner/repo' (defaults to github:main). "
            "Example: 'facebook/react' or 'github:main:facebook/react,github:main:facebook/relay'"
        )
    )
    api_key: str = Field(description="Greptile API key (provided by credential system)")
    github_token: str = Field(
        description="GitHub Personal Access Token with repo read access (from credential system)"
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session ID for conversation continuity across multiple queries",
    )
    genius: bool | None = Field(
        default=None,
        description="Enable genius mode for more thorough analysis (slower but more accurate)",
    )


class SearchInput(BaseModel):
    query: str = Field(description="Natural language search query to find relevant code")
    repositories: str = Field(
        description=(
            "Comma-separated list of repositories. Format: 'github:branch:owner/repo' "
            "or just 'owner/repo' (defaults to github:main)"
        )
    )
    api_key: str = Field(description="Greptile API key (provided by credential system)")
    github_token: str = Field(
        description="GitHub Personal Access Token with repo read access (from credential system)"
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session ID for conversation continuity across multiple searches",
    )
    genius: bool | None = Field(
        default=None,
        description="Enable genius mode for more thorough search (slower but more accurate)",
    )


class IndexRepositoryInput(BaseModel):
    remote: str = Field(description="Git remote type: 'github' or 'gitlab'")
    repository: str = Field(
        description="Repository in owner/repo format. Example: 'facebook/react'"
    )
    branch: str = Field(description="Branch to index (e.g. 'main' or 'master')")
    api_key: str = Field(description="Greptile API key (provided by credential system)")
    github_token: str = Field(
        description="GitHub Personal Access Token with repo read access (from credential system)"
    )
    reload: bool | None = Field(
        default=None, description="Force re-indexing even if already indexed"
    )
    notify: bool | None = Field(
        default=None, description="Send email notification when indexing completes"
    )


class StatusInput(BaseModel):
    remote: str = Field(description="Git remote type: 'github' or 'gitlab'")
    repository: str = Field(
        description="Repository in owner/repo format. Example: 'facebook/react'"
    )
    branch: str = Field(description="Branch name (e.g. 'main' or 'master')")
    api_key: str = Field(description="Greptile API key (provided by credential system)")
    github_token: str = Field(
        description="GitHub Personal Access Token with repo read access (from credential system)"
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=QueryInput)
@serialize_pydantic_return
async def query(
    query: str,
    repositories: str,
    api_key: str,
    github_token: str,
    session_id: str | None = None,
    genius: bool | None = None,
) -> QueryOutput:
    """Query repositories in natural language and get answers with relevant code references."""
    if not api_key or not api_key.strip():
        return QueryOutput(
            success=False,
            error="Greptile API key is empty. Please configure a valid Greptile credential.",
        )
    if not github_token or not github_token.strip():
        return QueryOutput(
            success=False,
            error="GitHub token is empty. Please configure a valid Greptile credential.",
        )

    body: dict[str, Any] = {
        "messages": [{"role": "user", "content": query}],
        "repositories": _parse_repositories(repositories),
        "stream": False,
    }
    if session_id:
        body["sessionId"] = session_id
    if genius is not None:
        body["genius"] = genius

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{_GREPTILE_API_BASE}/query",
                headers=_headers(api_key, github_token),
                json=body,
            )
        if response.status_code != 200:
            return QueryOutput(
                success=False,
                error=f"Greptile API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return QueryOutput(
            success=False,
            error="Request timed out. The query may be too complex or the repository large.",
        )
    except Exception as exc:
        return QueryOutput(success=False, error=f"Query failed: {exc}")

    return QueryOutput(
        success=True,
        message=data.get("message") or "",
        sources=_parse_sources(data),
    )


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(
    query: str,
    repositories: str,
    api_key: str,
    github_token: str,
    session_id: str | None = None,
    genius: bool | None = None,
) -> SearchOutput:
    """Search repositories in natural language for relevant code references, without an answer."""
    if not api_key or not api_key.strip():
        return SearchOutput(
            success=False,
            error="Greptile API key is empty. Please configure a valid Greptile credential.",
        )
    if not github_token or not github_token.strip():
        return SearchOutput(
            success=False,
            error="GitHub token is empty. Please configure a valid Greptile credential.",
        )

    body: dict[str, Any] = {
        "query": query,
        "repositories": _parse_repositories(repositories),
    }
    if session_id:
        body["sessionId"] = session_id
    if genius is not None:
        body["genius"] = genius

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{_GREPTILE_API_BASE}/search",
                headers=_headers(api_key, github_token),
                json=body,
            )
        if response.status_code != 200:
            return SearchOutput(
                success=False,
                error=f"Greptile API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchOutput(success=False, error=f"Search failed: {exc}")

    # The search endpoint may return the source list at the top level or under
    # a "sources" key; _parse_sources handles both shapes.
    payload: dict[str, Any] = data if isinstance(data, dict) else {"sources": data}
    return SearchOutput(success=True, sources=_parse_sources(payload))


@tool(args_schema=IndexRepositoryInput)
@serialize_pydantic_return
async def index_repo(
    remote: str,
    repository: str,
    branch: str,
    api_key: str,
    github_token: str,
    reload: bool | None = None,
    notify: bool | None = None,
) -> IndexRepositoryOutput:
    """Submit a repository to be indexed by Greptile so it can be queried."""
    if not api_key or not api_key.strip():
        return IndexRepositoryOutput(
            success=False,
            error="Greptile API key is empty. Please configure a valid Greptile credential.",
        )
    if not github_token or not github_token.strip():
        return IndexRepositoryOutput(
            success=False,
            error="GitHub token is empty. Please configure a valid Greptile credential.",
        )

    body: dict[str, Any] = {
        "remote": remote,
        "repository": repository,
        "branch": branch,
    }
    if reload is not None:
        body["reload"] = reload
    if notify is not None:
        body["notify"] = notify

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{_GREPTILE_API_BASE}/repositories",
                headers=_headers(api_key, github_token),
                json=body,
            )
        if response.status_code != 200:
            return IndexRepositoryOutput(
                success=False,
                error=f"Greptile API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return IndexRepositoryOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return IndexRepositoryOutput(success=False, error=f"Index repository failed: {exc}")

    status_endpoint = data.get("statusEndpoint") or ""
    repository_id = ""
    if status_endpoint:
        marker = "/repositories/"
        idx = status_endpoint.find(marker)
        if idx != -1:
            from urllib.parse import unquote

            repository_id = unquote(status_endpoint[idx + len(marker) :])
    if not repository_id:
        repository_id = f"{remote}:{branch}:{repository}"

    return IndexRepositoryOutput(
        success=True,
        repository_id=repository_id,
        status_endpoint=status_endpoint,
        message=data.get("message") or "Repository submitted for indexing",
    )


@tool(args_schema=StatusInput)
@serialize_pydantic_return
async def status(
    remote: str,
    repository: str,
    branch: str,
    api_key: str,
    github_token: str,
) -> StatusOutput:
    """Check the indexing status of a repository in Greptile."""
    if not api_key or not api_key.strip():
        return StatusOutput(
            success=False,
            error="Greptile API key is empty. Please configure a valid Greptile credential.",
        )
    if not github_token or not github_token.strip():
        return StatusOutput(
            success=False,
            error="GitHub token is empty. Please configure a valid Greptile credential.",
        )

    repository_id = f"{remote}:{branch}:{repository}"
    url = f"{_GREPTILE_API_BASE}/repositories/{quote(repository_id, safe='')}"

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers=_headers(api_key, github_token))
        if response.status_code != 200:
            return StatusOutput(
                success=False,
                error=f"Greptile API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return StatusOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return StatusOutput(success=False, error=f"Status check failed: {exc}")

    sample_questions = data.get("sampleQuestions")
    if not isinstance(sample_questions, list):
        sample_questions = []

    return StatusOutput(
        success=True,
        repository=data.get("repository") or "",
        remote=data.get("remote") or "",
        branch=data.get("branch") or "",
        private=data.get("private"),
        status=data.get("status") or "unknown",
        files_processed=data.get("filesProcessed"),
        num_files=data.get("numFiles"),
        sample_questions=sample_questions,
        sha=data.get("sha"),
    )
