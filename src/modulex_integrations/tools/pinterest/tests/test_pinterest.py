"""Tests for the Pinterest integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.pinterest import (
    create_pin,
    get_board_sections,
    list_boards,
    list_pins,
    manifest,
)
from modulex_integrations.tools.pinterest.outputs import (
    CreatePinOutput,
    GetBoardSectionsOutput,
    ListBoardsOutput,
    ListPinsOutput,
)

API = "https://api.pinterest.com/v5"
_API_KEY = "pinterest-fake-token"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


class TestManifest:
    def test_four_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_two_auth_schemas(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key", "oauth2"}


@pytest.mark.asyncio
async def test_list_boards(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/boards?page_size=25",
        json={
            "items": [
                {"id": "b1", "name": "Inspiration", "privacy": "PUBLIC", "pin_count": 12},
            ],
            "bookmark": "next-cursor",
        },
    )
    result_dict = await list_boards.ainvoke(_args())
    result = ListBoardsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.boards[0]["name"] == "Inspiration"
    assert result.bookmark == "next-cursor"


@pytest.mark.asyncio
async def test_list_boards_auth_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/boards?page_size=25", status_code=401, text=""
    )
    result_dict = await list_boards.ainvoke(_args())
    result = ListBoardsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "Authentication" in result.error


@pytest.mark.asyncio
async def test_get_board_sections(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/boards/b1/sections?page_size=25",
        json={"items": [{"id": "s1", "name": "Section A"}]},
    )
    result_dict = await get_board_sections.ainvoke(_args(board_id="b1"))
    result = GetBoardSectionsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sections[0]["name"] == "Section A"


@pytest.mark.asyncio
async def test_create_pin(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/pins",
        status_code=201,
        json={
            "id": "pin123",
            "title": "Sunset",
            "description": "Beautiful",
            "link": None,
            "board_id": "b1",
            "board_section_id": None,
            "created_at": "2026-05-16T12:00:00Z",
            "media": {"images": {"600x": {"url": "..."}}},
        },
    )
    result_dict = await create_pin.ainvoke(
        _args(board_id="b1", title="Sunset", media_url="https://example.com/sunset.jpg")
    )
    result = CreatePinOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "pin123"
    assert result.title == "Sunset"


@pytest.mark.asyncio
async def test_list_pins_board(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/boards/b1/pins?page_size=25",
        json={"items": [{"id": "pin1", "title": "First"}]},
    )
    result_dict = await list_pins.ainvoke(_args(board_id="b1"))
    result = ListPinsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.board_section_id is None


@pytest.mark.asyncio
async def test_list_pins_section(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/boards/b1/sections/s1/pins?page_size=25",
        json={"items": [{"id": "pin1"}]},
    )
    result_dict = await list_pins.ainvoke(_args(board_id="b1", board_section_id="s1"))
    result = ListPinsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.board_section_id == "s1"
