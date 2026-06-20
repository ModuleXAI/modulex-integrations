"""Happy-path test for the single action + failure-path tests for the
non-2xx and invalid-input branches (the tool does not raise on errors)."""
from __future__ import annotations

import json
from typing import Any

import pytest

from modulex_integrations.tools.clay import TOOLS, manifest, populate
from modulex_integrations.tools.clay.outputs import PopulateOutput

WEBHOOK_URL = "https://api.clay.com/v3/sources/webhook/pull-in-data-from-a-webhook-abc123"
_AUTH_TOKEN = "fake-webhook-token"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_AUTH_TOKEN, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_1_action(self) -> None:
        assert len(manifest.actions) == 1

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy path -------------------------------------------------------------


@pytest.mark.asyncio
async def test_populate(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=WEBHOOK_URL,
        status_code=200,
        json={"status": "ok"},
        headers={"content-type": "application/json"},
    )

    result_dict = await populate.ainvoke(
        _args(
            webhook_url=WEBHOOK_URL,
            data={"name": "Ada Lovelace", "email": "ada@example.com"},
        )
    )

    assert isinstance(result_dict, dict)

    result = PopulateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data == {"status": "ok"}
    assert result.metadata is not None
    assert result.metadata.status == 200
    assert result.metadata.content_type is not None
    assert "application/json" in result.metadata.content_type
    assert result.metadata.timestamp is not None

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-clay-webhook-auth"] == _AUTH_TOKEN
    # Body wraps the record under "data" (matches the Clay webhook contract).
    assert json.loads(sent.content.decode())["data"] == {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
    }


@pytest.mark.asyncio
async def test_populate_without_auth_token_omits_header(httpx_mock):  # type: ignore[no-untyped-def]
    """Most Clay webhooks need no auth; an empty token must not short-circuit
    and must not attach the x-clay-webhook-auth header."""
    httpx_mock.add_response(
        method="POST",
        url=WEBHOOK_URL,
        status_code=200,
        text="Accepted",
        headers={"content-type": "text/plain"},
    )

    result_dict = await populate.ainvoke(
        {"webhook_url": WEBHOOK_URL, "data": {"x": 1}, "api_key": ""}
    )

    assert isinstance(result_dict, dict)

    result = PopulateOutput.model_validate(result_dict)
    assert result.success is True
    # Non-JSON body is wrapped as {"message": ...}.
    assert result.data == {"message": "Accepted"}

    sent = httpx_mock.get_requests()[0]
    assert "x-clay-webhook-auth" not in sent.headers


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_populate_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Non-2xx responses surface as success=False + error rather than
    raising; metadata is still captured."""
    httpx_mock.add_response(
        method="POST",
        url=WEBHOOK_URL,
        status_code=401,
        text="Unauthorized",
        headers={"content-type": "text/plain"},
    )

    result_dict = await populate.ainvoke(
        _args(webhook_url=WEBHOOK_URL, data={"x": 1})
    )

    assert isinstance(result_dict, dict)

    result = PopulateOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error
    assert result.metadata is not None
    assert result.metadata.status == 401


@pytest.mark.asyncio
async def test_populate_validates_empty_webhook_url() -> None:
    """Empty / whitespace-only webhook_url short-circuits before any HTTP call."""
    result_dict = await populate.ainvoke({"webhook_url": "", "data": {"x": 1}})

    assert isinstance(result_dict, dict)

    result = PopulateOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "webhook_url" in result.error
