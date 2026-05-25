"""Happy-path tests for every fal_ai @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.fal_ai import (
    TOOLS,
    add_request_to_queue,
    cancel_request,
    get_request_response,
    get_request_status,
    manifest,
)
from modulex_integrations.tools.fal_ai.outputs import (
    AddRequestToQueueOutput,
    CancelRequestOutput,
    GetRequestResponseOutput,
    GetRequestStatusOutput,
)

API = "https://queue.fal.run/fal-ai"

_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_add_request_to_queue(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/fast-sdxl",
        json={
            # TODO: fill in a representative response shape from the fal.ai API docs
            "request_id": "req_abc123",
            "response_url": "https://queue.fal.run/fal-ai/fast-sdxl/requests/req_abc123",
            "status_url": "https://queue.fal.run/fal-ai/fast-sdxl/requests/req_abc123/status",
            "cancel_url": "https://queue.fal.run/fal-ai/fast-sdxl/requests/req_abc123/cancel",
        },
    )

    result_dict = await add_request_to_queue.ainvoke(
        _args(app_id="fast-sdxl", data={"prompt": "a cat"})
    )

    assert isinstance(result_dict, dict)
    result = AddRequestToQueueOutput.model_validate(result_dict)
    assert result.success is True
    assert result.request_id == "req_abc123"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["authorization"] == f"Key {_API_KEY}"


@pytest.mark.asyncio
async def test_cancel_request(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/fast-sdxl/requests/req_abc123/cancel",
        json={},
    )

    result_dict = await cancel_request.ainvoke(
        _args(app_id="fast-sdxl", request_id="req_abc123")
    )

    assert isinstance(result_dict, dict)
    result = CancelRequestOutput.model_validate(result_dict)
    assert result.success is True

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["authorization"] == f"Key {_API_KEY}"


@pytest.mark.asyncio
async def test_get_request_response(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/fast-sdxl/requests/req_abc123",
        json={
            # TODO: fill in a representative response shape from the fal.ai API docs
            "images": [{"url": "https://fal.media/files/image.png", "width": 1024, "height": 1024}],
            "seed": 42,
        },
    )

    result_dict = await get_request_response.ainvoke(
        _args(app_id="fast-sdxl", request_id="req_abc123")
    )

    assert isinstance(result_dict, dict)
    result = GetRequestResponseOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["authorization"] == f"Key {_API_KEY}"


@pytest.mark.asyncio
async def test_get_request_status(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/fast-sdxl/requests/req_abc123/status?logs=1",
        json={
            # TODO: fill in a representative response shape from the fal.ai API docs
            "status": "IN_PROGRESS",
            "queue_position": 2,
            "logs": [{"message": "Loading model...", "level": "info", "timestamp": "2024-01-01T00:00:00Z"}],
        },
    )

    result_dict = await get_request_status.ainvoke(
        _args(app_id="fast-sdxl", request_id="req_abc123", logs=True)
    )

    assert isinstance(result_dict, dict)
    result = GetRequestStatusOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "IN_PROGRESS"
    assert result.queue_position == 2
    assert len(result.logs) == 1

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["authorization"] == f"Key {_API_KEY}"


# --- Failure-path tests ---------------------------------------------------


@pytest.mark.asyncio
async def test_add_request_validates_empty_api_key() -> None:
    result_dict = await add_request_to_queue.ainvoke(
        {"app_id": "fast-sdxl", "data": {"prompt": "test"}, "api_key": ""}
    )
    result = AddRequestToQueueOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")
