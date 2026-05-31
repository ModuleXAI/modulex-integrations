"""Happy-path tests for every fellow @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.fellow import (
    TOOLS,
    archive_action_item,
    complete_action_item,
    get_note_by_id,
    manifest,
)
from modulex_integrations.tools.fellow.outputs import (
    ArchiveActionItemOutput,
    CompleteActionItemOutput,
    GetNoteByIdOutput,
)

_SUBDOMAIN = "testworkspace"
_API_KEY = "fake-api-key"

API = f"https://{_SUBDOMAIN}.fellow.app/api/v1"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(subdomain=_SUBDOMAIN, api_key=_API_KEY, **extra)


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
async def test_archive_action_item(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/action_item/123/archive",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
        },
    )

    result_dict = await archive_action_item.ainvoke(_args(action_item_id="123"))

    assert isinstance(result_dict, dict)
    result = ArchiveActionItemOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_complete_action_item(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/action_item/456/complete",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
        },
    )

    result_dict = await complete_action_item.ainvoke(_args(action_item_id="456"))

    assert isinstance(result_dict, dict)
    result = CompleteActionItemOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_note_by_id(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/note/789",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
        },
    )

    result_dict = await get_note_by_id.ainvoke(_args(note_id="789"))

    assert isinstance(result_dict, dict)
    result = GetNoteByIdOutput.model_validate(result_dict)
    assert result.success is True


# --- Failure-path tests ---------------------------------------------------


@pytest.mark.asyncio
async def test_archive_action_item_validates_empty_api_key() -> None:
    result_dict = await archive_action_item.ainvoke(
        {"action_item_id": "123", "subdomain": "test", "api_key": ""}
    )
    result = ArchiveActionItemOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")
