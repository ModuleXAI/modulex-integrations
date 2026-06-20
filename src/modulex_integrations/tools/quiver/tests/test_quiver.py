"""Happy-path tests per action + failure-path and empty-credential tests.

Quiver does not raise on non-2xx; the tools wrap everything and return
``success=False`` + ``error`` instead.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.quiver import (
    TOOLS,
    image_to_svg,
    list_models,
    manifest,
    text_to_svg,
)
from modulex_integrations.tools.quiver.outputs import (
    ImageToSvgOutput,
    ListModelsOutput,
    TextToSvgOutput,
)

API = "https://api.quiver.ai/v1"
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

    def test_manifest_logo(self) -> None:
        assert manifest.logo == "modulex:quiver"


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_text_to_svg(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/svgs/generations",
        json={
            "id": "gen-001",
            "created": 1234567890,
            "data": [{"svg": "<svg>hi</svg>", "mime_type": "image/svg+xml"}],
            "credits": 5,
            "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
        },
    )

    result_dict = await text_to_svg.ainvoke(_args(prompt="a red arrow icon"))

    assert isinstance(result_dict, dict)

    result = TextToSvgOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "gen-001"
    assert result.svg_content == "<svg>hi</svg>"
    assert result.artifacts[0].mime_type == "image/svg+xml"
    assert result.credits == 5
    assert result.usage is not None
    assert result.usage.total_tokens == 30

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_text_to_svg_with_references(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/svgs/generations",
        json={
            "id": "gen-002",
            "created": 1234567891,
            "data": [
                {"svg": "<svg>a</svg>", "mime_type": "image/svg+xml"},
                {"svg": "<svg>b</svg>", "mime_type": "image/svg+xml"},
            ],
            "credits": 10,
        },
    )

    result_dict = await text_to_svg.ainvoke(
        _args(
            prompt="two variants",
            references=["https://example.com/ref.png"],
            n=2,
            temperature=0.7,
        )
    )

    assert isinstance(result_dict, dict)

    result = TextToSvgOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.artifacts) == 2
    assert result.svg_content == "<svg>a</svg>"

    import json

    sent = httpx_mock.get_requests()[0]
    body = json.loads(sent.content)
    assert body["references"] == [{"url": "https://example.com/ref.png"}]
    assert body["n"] == 2
    assert body["temperature"] == 0.7


@pytest.mark.asyncio
async def test_image_to_svg(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/svgs/vectorizations",
        json={
            "id": "vec-001",
            "created": 1234567892,
            "data": [{"svg": "<svg>vec</svg>", "mime_type": "image/svg+xml"}],
            "credits": 8,
        },
    )

    result_dict = await image_to_svg.ainvoke(
        _args(image="https://example.com/logo.png", auto_crop=True, target_size=2048)
    )

    assert isinstance(result_dict, dict)

    result = ImageToSvgOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "vec-001"
    assert result.svg_content == "<svg>vec</svg>"
    assert result.credits == 8

    import json

    sent = httpx_mock.get_requests()[0]
    body = json.loads(sent.content)
    assert body["image"] == {"url": "https://example.com/logo.png"}
    assert body["auto_crop"] is True
    assert body["target_size"] == 2048


@pytest.mark.asyncio
async def test_list_models(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/models",
        json={
            "object": "list",
            "data": [
                {
                    "id": "arrow-1.1",
                    "name": "Arrow 1.1",
                    "description": "Default SVG model",
                    "created": 1700000000,
                    "owned_by": "quiver",
                    "input_modalities": ["text", "image"],
                    "output_modalities": ["svg"],
                    "context_length": 131072,
                    "max_output_length": 65536,
                    "supported_operations": ["svg_generate", "svg_vectorize"],
                    "supported_sampling_parameters": ["temperature", "top_p"],
                }
            ],
        },
    )

    result_dict = await list_models.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = ListModelsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total_models == 1
    assert result.models[0].id == "arrow-1.1"
    assert result.models[0].owned_by == "quiver"
    assert result.models[0].supported_operations == ["svg_generate", "svg_vectorize"]

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_text_to_svg_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Non-2xx responses are wrapped into success=False rather than raised."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/svgs/generations",
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await text_to_svg.ainvoke(_args(prompt="anything"))

    assert isinstance(result_dict, dict)

    result = TextToSvgOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_image_to_svg_requires_image() -> None:
    """Empty image URL short-circuits before the HTTP call."""
    result_dict = await image_to_svg.ainvoke({"image": "", "api_key": _API_KEY})

    assert isinstance(result_dict, dict)

    result = ImageToSvgOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "image" in result.error.lower()


# --- Empty-credential paths ------------------------------------------------


@pytest.mark.asyncio
async def test_text_to_svg_validates_empty_api_key() -> None:
    result_dict = await text_to_svg.ainvoke({"prompt": "x", "api_key": ""})

    assert isinstance(result_dict, dict)

    result = TextToSvgOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_list_models_validates_empty_api_key() -> None:
    result_dict = await list_models.ainvoke({"api_key": "   "})

    assert isinstance(result_dict, dict)

    result = ListModelsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
