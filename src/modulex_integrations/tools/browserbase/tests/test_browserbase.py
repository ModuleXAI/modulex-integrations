"""Happy-path tests for every browserbase @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.browserbase import (
    TOOLS,
    create_context,
    create_session,
    list_projects,
    manifest,
)
from modulex_integrations.tools.browserbase.outputs import (
    CreateContextOutput,
    CreateSessionOutput,
    ListProjectsOutput,
)

API = "https://api.browserbase.com/v1"

_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_context(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contexts",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "ctx_abc123",
            "projectId": "proj_xyz",
            "createdAt": "2026-01-01T00:00:00Z",
        },
        status_code=201,
    )

    result_dict = await create_context.ainvoke(_args(project_id="proj_xyz"))

    assert isinstance(result_dict, dict)
    result = CreateContextOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "ctx_abc123"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-bb-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_create_session(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sessions",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "sess_abc123",
            "projectId": "proj_xyz",
            "status": "RUNNING",
            "createdAt": "2026-01-01T00:00:00Z",
            "region": "us-west-2",
            "connectUrl": "wss://connect.browserbase.com/sess_abc123",
        },
        status_code=201,
    )

    result_dict = await create_session.ainvoke(_args(project_id="proj_xyz"))

    assert isinstance(result_dict, dict)
    result = CreateSessionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "sess_abc123"
    assert result.status == "RUNNING"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-bb-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_list_projects(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/projects",
        json=[
            # TODO: fill in a representative response shape from the upstream API docs
            {"id": "proj_1", "name": "My Project"},
            {"id": "proj_2", "name": "Another Project"},
        ],
    )

    result_dict = await list_projects.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListProjectsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.projects) == 2
    assert result.projects[0].id == "proj_1"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-bb-api-key"] == _API_KEY


# --- Failure-path tests ---------------------------------------------------


@pytest.mark.asyncio
async def test_create_context_validates_empty_api_key() -> None:
    result_dict = await create_context.ainvoke({"project_id": "x", "api_key": ""})
    result = CreateContextOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")
