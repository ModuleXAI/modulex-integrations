"""Happy-path tests for every mixpanel @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.mixpanel import (
    TOOLS,
    emit_event_to,
    manifest,
)
from modulex_integrations.tools.mixpanel.outputs import EmitEventToOutput

API = "https://api.mixpanel.com"

_API_KEY = "fake-project-token"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_1_action(self) -> None:
        assert len(manifest.actions) == 1

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_emit_event_to(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/track",
        text="1",
    )

    result_dict = await emit_event_to.ainvoke(
        _args(
            event_name="Sign Up",
            distinct_id="user_123",
            properties={"plan": "pro"},
        )
    )

    assert isinstance(result_dict, dict)
    result = EmitEventToOutput.model_validate(result_dict)
    assert result.success is True
    assert result.distinct_id == "user_123"
    assert result.properties is not None
    assert result.properties["token"] == _API_KEY
    assert result.properties["plan"] == "pro"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["content-type"] == "application/json"


@pytest.mark.asyncio
async def test_emit_event_to_validates_empty_api_key() -> None:
    result_dict = await emit_event_to.ainvoke(
        {"event_name": "Test", "distinct_id": "u1", "api_key": ""}
    )
    result = EmitEventToOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")


@pytest.mark.asyncio
async def test_emit_event_to_handles_rejection(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/track",
        text="0",
    )

    result_dict = await emit_event_to.ainvoke(
        _args(event_name="Bad Event", distinct_id="user_x")
    )
    result = EmitEventToOutput.model_validate(result_dict)
    assert result.success is False
    assert "rejected" in (result.error or "").lower()
