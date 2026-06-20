"""Happy-path tests per action + failure-path and empty-credential tests
for the non-2xx and empty-key branches (Gamma's tools don't raise)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.gamma import (
    TOOLS,
    check_status,
    generate,
    generate_from_template,
    list_folders,
    list_themes,
    manifest,
)
from modulex_integrations.tools.gamma.outputs import (
    CheckStatusOutput,
    GenerateFromTemplateOutput,
    GenerateOutput,
    ListFoldersOutput,
    ListThemesOutput,
)

API = "https://public-api.gamma.app/v1.0"
_API_KEY = "sk-gamma-fake"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_5_actions(self) -> None:
        assert len(manifest.actions) == 5

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_generate(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/generations",
        json={"generationId": "gen-123", "warnings": "numCards ignored"},
    )

    result_dict = await generate.ainvoke(
        _args(input_text="A deck about solar power", text_mode="generate", num_cards=8)
    )

    assert isinstance(result_dict, dict)

    result = GenerateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.generation_id == "gen-123"
    assert result.warnings == "numCards ignored"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["X-API-KEY"] == _API_KEY


@pytest.mark.asyncio
async def test_generate_from_template(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/generations/from-template",
        json={"generationId": "gen-456"},
    )

    result_dict = await generate_from_template.ainvoke(
        _args(gamma_id="tmpl-1", prompt="Adapt for healthcare", folder_ids="f1, f2")
    )

    assert isinstance(result_dict, dict)

    result = GenerateFromTemplateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.generation_id == "gen-456"


@pytest.mark.asyncio
async def test_check_status(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/generations/gen-123",
        json={
            "generationId": "gen-123",
            "status": "completed",
            "gammaUrl": "https://gamma.app/docs/abc",
            "gammaId": "abc",
            "exportUrl": "https://files.gamma.app/abc.pdf",
            "credits": {"deducted": 5, "remaining": 95},
        },
    )

    result_dict = await check_status.ainvoke(_args(generation_id="gen-123"))

    assert isinstance(result_dict, dict)

    result = CheckStatusOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "completed"
    assert result.gamma_url == "https://gamma.app/docs/abc"
    assert result.export_url == "https://files.gamma.app/abc.pdf"
    assert result.credits is not None
    assert result.credits.deducted == 5
    assert result.credits.remaining == 95


@pytest.mark.asyncio
async def test_check_status_failed(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/generations/gen-789",
        json={
            "generationId": "gen-789",
            "status": "failed",
            "gammaUrl": None,
            "error": {"message": "Input too long", "statusCode": 422},
        },
    )

    result_dict = await check_status.ainvoke(_args(generation_id="gen-789"))

    assert isinstance(result_dict, dict)

    result = CheckStatusOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "failed"
    assert result.generation_error is not None
    assert result.generation_error.message == "Input too long"
    assert result.generation_error.status_code == 422


@pytest.mark.asyncio
async def test_list_themes(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/themes?limit=2",
        json={
            "data": [
                {
                    "id": "theme-1",
                    "name": "Oasis",
                    "type": "standard",
                    "colorKeywords": ["blue", "green"],
                    "toneKeywords": ["calm"],
                }
            ],
            "hasMore": True,
            "nextCursor": "cursor-2",
        },
    )

    result_dict = await list_themes.ainvoke(_args(limit=2))

    assert isinstance(result_dict, dict)

    result = ListThemesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.themes[0].id == "theme-1"
    assert result.themes[0].color_keywords == ["blue", "green"]
    assert result.has_more is True
    assert result.next_cursor == "cursor-2"


@pytest.mark.asyncio
async def test_list_folders(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/folders",
        json={
            "data": [{"id": "folder-1", "name": "Sales decks"}],
            "hasMore": False,
            "nextCursor": None,
        },
    )

    result_dict = await list_folders.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = ListFoldersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.folders[0].name == "Sales decks"
    assert result.has_more is False


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Non-2xx responses come back as ``success=False`` + ``error``."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/generations",
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await generate.ainvoke(
        _args(input_text="anything", text_mode="generate")
    )

    assert isinstance(result_dict, dict)

    result = GenerateOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_generate_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await generate.ainvoke(
        {"input_text": "x", "text_mode": "generate", "api_key": ""}
    )

    assert isinstance(result_dict, dict)

    result = GenerateOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_check_status_validates_empty_api_key() -> None:
    result_dict = await check_status.ainvoke({"generation_id": "g", "api_key": "   "})

    assert isinstance(result_dict, dict)

    result = CheckStatusOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
