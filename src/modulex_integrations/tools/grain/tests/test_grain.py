"""Happy-path tests per action + failure-path + empty-credential tests.

The Grain tools wrap every call in try/except so non-2xx responses come
back as ``success=False`` + ``error`` rather than raising.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.grain import (
    TOOLS,
    create_hook,
    delete_hook,
    get_recording,
    get_transcript,
    list_hooks,
    list_meeting_types,
    list_recordings,
    list_teams,
    list_views,
    manifest,
)
from modulex_integrations.tools.grain.outputs import (
    CreateHookOutput,
    DeleteHookOutput,
    GetRecordingOutput,
    GetTranscriptOutput,
    ListHooksOutput,
    ListMeetingTypesOutput,
    ListRecordingsOutput,
    ListTeamsOutput,
    ListViewsOutput,
)

BASE = "https://api.grain.com/_/public-api"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_9_actions(self) -> None:
        assert len(manifest.actions) == 9

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo(self) -> None:
        assert manifest.logo == "modulex:grain"


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_list_recordings(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/v2/recordings",
        json={
            "recordings": [
                {
                    "id": "rec-1",
                    "title": "Weekly standup",
                    "start_datetime": "2024-01-01T10:00:00Z",
                    "end_datetime": "2024-01-01T10:30:00Z",
                    "duration_ms": 1800000,
                    "media_type": "video",
                    "source": "zoom",
                    "url": "https://grain.com/share/rec-1",
                    "thumbnail_url": None,
                    "tags": ["standup"],
                    "teams": [{"id": "t-1", "name": "Eng"}],
                    "meeting_type": {"id": "mt-1", "name": "Sync", "scope": "internal"},
                }
            ],
            "cursor": "next-cursor",
        },
    )

    result_dict = await list_recordings.ainvoke(_args(title_search="standup"))

    assert isinstance(result_dict, dict)
    result = ListRecordingsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.recordings[0].title == "Weekly standup"
    assert result.recordings[0].duration_ms == 1800000
    assert result.cursor == "next-cursor"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"
    assert sent.headers["Public-Api-Version"] == "2025-10-31"


@pytest.mark.asyncio
async def test_get_recording(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/v2/recordings/rec-1",
        json={
            "id": "rec-1",
            "title": "Customer call",
            "source": "meet",
            "tags": [],
            "teams": [],
            "ai_summary": {"text": "Great call."},
        },
    )

    result_dict = await get_recording.ainvoke(
        _args(recording_id="rec-1", include_ai_summary=True)
    )

    assert isinstance(result_dict, dict)
    result = GetRecordingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.recording is not None
    assert result.recording.title == "Customer call"
    assert result.recording.ai_summary == {"text": "Great call."}


@pytest.mark.asyncio
async def test_get_transcript(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/v2/recordings/rec-1/transcript",
        json=[
            {
                "participant_id": "p-1",
                "speaker": "Alice",
                "start": 0,
                "end": 5000,
                "text": "Hello everyone.",
            }
        ],
    )

    result_dict = await get_transcript.ainvoke(_args(recording_id="rec-1"))

    assert isinstance(result_dict, dict)
    result = GetTranscriptOutput.model_validate(result_dict)
    assert result.success is True
    assert result.transcript[0].speaker == "Alice"
    assert result.transcript[0].text == "Hello everyone."


@pytest.mark.asyncio
async def test_list_views(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/views?type_filter=recordings",
        json={"views": [{"id": "v-1", "name": "All calls", "type": "recordings"}]},
    )

    result_dict = await list_views.ainvoke(_args(type_filter="recordings"))

    assert isinstance(result_dict, dict)
    result = ListViewsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.views[0].id == "v-1"
    assert result.views[0].type == "recordings"


@pytest.mark.asyncio
async def test_list_teams(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/v2/teams",
        json={"teams": [{"id": "t-1", "name": "Engineering"}]},
    )

    result_dict = await list_teams.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListTeamsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.teams[0].name == "Engineering"


@pytest.mark.asyncio
async def test_list_teams_bare_array(httpx_mock):  # type: ignore[no-untyped-def]
    """The API may return a bare array; the tool falls back to it."""
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/v2/teams",
        json=[{"id": "t-2", "name": "Sales"}],
    )

    result_dict = await list_teams.ainvoke(_args())

    result = ListTeamsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.teams[0].name == "Sales"


@pytest.mark.asyncio
async def test_list_meeting_types(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/v2/meeting_types",
        json={
            "meeting_types": [
                {"id": "mt-1", "name": "Customer call", "scope": "external"}
            ]
        },
    )

    result_dict = await list_meeting_types.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListMeetingTypesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.meeting_types[0].scope == "external"


@pytest.mark.asyncio
async def test_create_hook(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/hooks",
        json={
            "id": "hook-1",
            "enabled": True,
            "version": 2,
            "hook_url": "https://example.com/webhooks/grain",
            "view_id": "v-1",
            "actions": ["added", "updated"],
            "inserted_at": "2024-01-01T00:00:00Z",
        },
    )

    result_dict = await create_hook.ainvoke(
        _args(
            hook_url="https://example.com/webhooks/grain",
            view_id="v-1",
            actions=["added", "updated"],
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateHookOutput.model_validate(result_dict)
    assert result.success is True
    assert result.hook is not None
    assert result.hook.id == "hook-1"
    assert result.hook.actions == ["added", "updated"]


@pytest.mark.asyncio
async def test_list_hooks(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/hooks",
        json={
            "hooks": [
                {
                    "id": "hook-1",
                    "enabled": True,
                    "hook_url": "https://example.com/webhooks/grain",
                    "view_id": "v-1",
                    "actions": ["added"],
                    "inserted_at": "2024-01-01T00:00:00Z",
                }
            ]
        },
    )

    result_dict = await list_hooks.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListHooksOutput.model_validate(result_dict)
    assert result.success is True
    assert result.hooks[0].id == "hook-1"


@pytest.mark.asyncio
async def test_delete_hook(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{BASE}/hooks/hook-1",
        status_code=204,
    )

    result_dict = await delete_hook.ainvoke(_args(hook_id="hook-1"))

    assert isinstance(result_dict, dict)
    result = DeleteHookOutput.model_validate(result_dict)
    assert result.success is True
    assert result.error is None


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_list_recordings_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/v2/recordings",
        status_code=401,
        text="Invalid token",
    )

    result_dict = await list_recordings.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListRecordingsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_create_hook_missing_id_in_response(httpx_mock):  # type: ignore[no-untyped-def]
    """A 200 with no webhook id surfaces as success=False."""
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/hooks",
        json={"enabled": True},
    )

    result_dict = await create_hook.ainvoke(
        _args(hook_url="https://example.com/h", view_id="v-1")
    )

    result = CreateHookOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None


# --- Empty-credential paths ------------------------------------------------


@pytest.mark.asyncio
async def test_list_recordings_validates_empty_api_key() -> None:
    result_dict = await list_recordings.ainvoke({"api_key": ""})

    assert isinstance(result_dict, dict)
    result = ListRecordingsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_delete_hook_validates_empty_api_key() -> None:
    result_dict = await delete_hook.ainvoke({"api_key": "  ", "hook_id": "hook-1"})

    result = DeleteHookOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
