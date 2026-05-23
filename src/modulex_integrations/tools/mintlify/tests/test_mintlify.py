"""Happy-path tests for every mintlify @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.mintlify import (
    TOOLS,
    chat_with_assistant,
    manifest,
    search_documentation,
    trigger_update,
)
from modulex_integrations.tools.mintlify.outputs import (
    ChatWithAssistantOutput,
    SearchDocumentationOutput,
    TriggerUpdateOutput,
)

API_DSC = "https://api-dsc.mintlify.com/v1"
API_ADMIN = "https://api.mintlify.com/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {
        "assistant_api_key": "fake-assistant-key",
        "admin_api_key": "fake-admin-key",
        "project_id": "fake-project-id",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_chat_with_assistant(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API_DSC}/assistant/my-domain/message",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "resp-123",
            "content": "Here is the answer.",
        },
    )

    result_dict = await chat_with_assistant.ainvoke(
        _args(domain="my-domain", fp="fingerprint-1", message="How do I deploy?")
    )

    assert isinstance(result_dict, dict)
    result = ChatWithAssistantOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message_id == "resp-123"


@pytest.mark.asyncio
async def test_search_documentation(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API_DSC}/search/my-domain",
        json=[
            # TODO: fill in a representative response shape from the upstream API docs
            {"title": "Getting Started", "url": "/docs/start", "content": "Welcome...", "score": 0.95},
        ],
    )

    result_dict = await search_documentation.ainvoke(
        _args(domain="my-domain", query="getting started")
    )

    assert isinstance(result_dict, dict)
    result = SearchDocumentationOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.results) == 1
    assert result.results[0].title == "Getting Started"


@pytest.mark.asyncio
async def test_trigger_update(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API_ADMIN}/project/update/fake-project-id",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "status": "triggered",
        },
    )

    result_dict = await trigger_update.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = TriggerUpdateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_chat_with_assistant_empty_credential() -> None:
    """Empty assistant API key returns inline error without hitting the wire."""
    result_dict = await chat_with_assistant.ainvoke(
        _args(
            domain="my-domain",
            fp="fp-1",
            message="hello",
            auth_data={"assistant_api_key": "", "admin_api_key": "x", "project_id": "x"},
        )
    )
    assert isinstance(result_dict, dict)
    result = ChatWithAssistantOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "empty" in result.error.lower() or "api key" in result.error.lower()
