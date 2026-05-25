"""Happy-path tests for every segment @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.segment import (
    TOOLS,
    alias,
    group,
    identify,
    manifest,
    page,
    screen,
    track,
)
from modulex_integrations.tools.segment.outputs import (
    AliasOutput,
    GroupOutput,
    IdentifyOutput,
    PageOutput,
    ScreenOutput,
    TrackOutput,
)

API = "https://api.segment.io/v1"

_WRITE_KEY = "fake-write-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(write_key=_WRITE_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_6_actions(self) -> None:
        assert len(manifest.actions) == 6

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_alias(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/alias",
        json={"success": True},
    )

    result_dict = await alias.ainvoke(_args(previous_id="old-id", user_id="new-id"))

    assert isinstance(result_dict, dict)
    result = AliasOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_group(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/group",
        json={"success": True},
    )

    result_dict = await group.ainvoke(_args(group_id="grp-123", user_id="usr-1"))

    assert isinstance(result_dict, dict)
    result = GroupOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_identify(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/identify",
        json={"success": True},
    )

    result_dict = await identify.ainvoke(_args(user_id="usr-1", traits={"email": "a@b.com"}))

    assert isinstance(result_dict, dict)
    result = IdentifyOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_page(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/page",
        json={"success": True},
    )

    result_dict = await page.ainvoke(_args(user_id="usr-1", name="Home"))

    assert isinstance(result_dict, dict)
    result = PageOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_screen(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/screen",
        json={"success": True},
    )

    result_dict = await screen.ainvoke(_args(user_id="usr-1", name="Dashboard"))

    assert isinstance(result_dict, dict)
    result = ScreenOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_track(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/track",
        json={"success": True},
    )

    result_dict = await track.ainvoke(_args(event="Button Clicked", user_id="usr-1"))

    assert isinstance(result_dict, dict)
    result = TrackOutput.model_validate(result_dict)
    assert result.success is True


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_alias_validates_empty_write_key() -> None:
    result_dict = await alias.ainvoke({"previous_id": "x", "write_key": ""})
    result = AliasOutput.model_validate(result_dict)
    assert result.success is False
    assert "Write key" in (result.error or "")
