"""Happy-path tests per action + failure-path and empty-credential tests
for the non-2xx -> success=False branch (Granola tools don't raise)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.granola import (
    TOOLS,
    get_note,
    list_folders,
    list_notes,
    manifest,
)
from modulex_integrations.tools.granola.outputs import (
    GetNoteOutput,
    ListFoldersOutput,
    ListNotesOutput,
)

API = "https://public-api.granola.ai/v1"
_API_KEY = "grn_fake-api-key"


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


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_list_notes(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/notes?created_after=2026-01-01",
        json={
            "notes": [
                {
                    "id": "not_1d3tmYTlCICgjy",
                    "title": "Weekly sync",
                    "owner": {"name": "Alice", "email": "alice@example.com"},
                    "created_at": "2026-01-01T10:00:00Z",
                    "updated_at": "2026-01-01T11:00:00Z",
                }
            ],
            "hasMore": True,
            "cursor": "next-cursor",
        },
    )

    result_dict = await list_notes.ainvoke(_args(created_after="2026-01-01"))

    assert isinstance(result_dict, dict)

    result = ListNotesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.notes[0].id == "not_1d3tmYTlCICgjy"
    assert result.notes[0].owner_name == "Alice"
    assert result.notes[0].owner_email == "alice@example.com"
    assert result.has_more is True
    assert result.cursor == "next-cursor"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"
    assert "created_after=2026-01-01" in str(sent.url)


@pytest.mark.asyncio
async def test_get_note(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/notes/not_1d3tmYTlCICgjy?include=transcript",
        json={
            "id": "not_1d3tmYTlCICgjy",
            "title": "Weekly sync",
            "owner": {"name": "Alice", "email": "alice@example.com"},
            "created_at": "2026-01-01T10:00:00Z",
            "updated_at": "2026-01-01T11:00:00Z",
            "web_url": "https://granola.ai/notes/not_1d3tmYTlCICgjy",
            "summary_text": "Discussed the roadmap.",
            "summary_markdown": "# Summary\n\nDiscussed the roadmap.",
            "attendees": [{"name": "Bob", "email": "bob@example.com"}],
            "folder_membership": [{"id": "fol_4y6LduVdwSKC27", "name": "Sales"}],
            "calendar_event": {
                "event_title": "Weekly sync",
                "organiser": "alice@example.com",
                "calendar_event_id": "evt_123",
                "scheduled_start_time": "2026-01-01T10:00:00Z",
                "scheduled_end_time": "2026-01-01T11:00:00Z",
                "invitees": [{"email": "bob@example.com"}, {"email": "carol@example.com"}],
            },
            "transcript": [
                {
                    "speaker": {"source": "microphone", "diarization_label": "Speaker A"},
                    "text": "Hello everyone.",
                    "start_time": "0.0",
                    "end_time": "1.5",
                }
            ],
        },
    )

    result_dict = await get_note.ainvoke(
        _args(note_id="not_1d3tmYTlCICgjy", include_transcript=True)
    )

    assert isinstance(result_dict, dict)

    result = GetNoteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "not_1d3tmYTlCICgjy"
    assert result.owner_name == "Alice"
    assert result.web_url == "https://granola.ai/notes/not_1d3tmYTlCICgjy"
    assert result.attendees[0].email == "bob@example.com"
    assert result.folders[0].name == "Sales"
    assert result.calendar_event_title == "Weekly sync"
    assert result.calendar_organiser == "alice@example.com"
    assert result.invitees == ["bob@example.com", "carol@example.com"]
    assert result.transcript is not None
    assert result.transcript[0].speaker == "microphone"
    assert result.transcript[0].speaker_label == "Speaker A"
    assert result.transcript[0].text == "Hello everyone."


@pytest.mark.asyncio
async def test_get_note_without_transcript(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/notes/not_abc",
        json={
            "id": "not_abc",
            "title": "Standup",
            "owner": {"name": None, "email": "owner@example.com"},
            "created_at": "2026-02-01T09:00:00Z",
            "updated_at": "2026-02-01T09:15:00Z",
            "summary_text": "Quick standup.",
            "attendees": [],
            "folder_membership": [],
            "calendar_event": {},
            "transcript": None,
        },
    )

    result_dict = await get_note.ainvoke(_args(note_id="not_abc"))

    assert isinstance(result_dict, dict)

    result = GetNoteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.title == "Standup"
    assert result.transcript is None
    assert result.invitees == []


@pytest.mark.asyncio
async def test_list_folders(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/folders?page_size=10",
        json={
            "folders": [
                {"id": "fol_4y6LduVdwSKC27", "name": "Sales", "parent_folder_id": None},
                {"id": "fol_child", "name": "Q1", "parent_folder_id": "fol_4y6LduVdwSKC27"},
            ],
            "hasMore": False,
            "cursor": None,
        },
    )

    result_dict = await list_folders.ainvoke(_args(page_size=10))

    assert isinstance(result_dict, dict)

    result = ListFoldersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.folders[0].name == "Sales"
    assert result.folders[0].parent_folder_id is None
    assert result.folders[1].parent_folder_id == "fol_4y6LduVdwSKC27"
    assert result.has_more is False


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_list_notes_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Granola errors come back as HTTP 4xx/5xx; the tool wraps them in
    ``success=False`` + ``error`` rather than raising."""
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/notes",
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await list_notes.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = ListNotesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_list_notes_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await list_notes.ainvoke({"api_key": ""})

    assert isinstance(result_dict, dict)

    result = ListNotesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_get_note_validates_empty_api_key() -> None:
    result_dict = await get_note.ainvoke({"note_id": "not_abc", "api_key": "   "})

    assert isinstance(result_dict, dict)

    result = GetNoteOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
