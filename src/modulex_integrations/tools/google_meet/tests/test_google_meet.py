"""Happy-path tests for every google_meet @tool, plus a manifest sanity check."""
from __future__ import annotations

import re
from typing import Any

import pytest

from modulex_integrations.tools.google_meet import (
    TOOLS,
    list_color_id_options,
    manifest,
    schedule_meeting,
)
from modulex_integrations.tools.google_meet.outputs import (
    ListColorIdOptionsOutput,
    ScheduleMeetingOutput,
)

API = "https://www.googleapis.com/calendar/v3"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_2_actions(self) -> None:
        assert len(manifest.actions) == 2

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_schedule_meeting(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        # TODO: tighten URL match (query string) if needed — Google appends conferenceDataVersion=1
        url=re.compile(rf"{re.escape(API)}/calendars/primary/events.*"),
        json={
            # TODO: fill in a representative response shape from Google's events.insert docs.
            "id": "evt_fake_id_123",
            "status": "confirmed",
            "summary": "Team sync",
            "htmlLink": "https://calendar.google.com/event?eid=fake",
            "hangoutLink": "https://meet.google.com/fake-meet-link",
            "start": {"dateTime": "2026-06-01T10:00:00-07:00", "timeZone": "America/Los_Angeles"},
            "end": {"dateTime": "2026-06-01T11:00:00-07:00", "timeZone": "America/Los_Angeles"},
            "attendees": [{"email": "alice@example.com", "responseStatus": "needsAction"}],
            "conferenceData": {
                "conferenceId": "fake-conf-id",
                "entryPoints": [
                    {
                        "entryPointType": "video",
                        "uri": "https://meet.google.com/fake-meet-link",
                        "label": "meet.google.com/fake-meet-link",
                    },
                ],
            },
        },
    )

    result_dict = await schedule_meeting.ainvoke(
        _args(
            event_start_date="2026-06-01T10:00:00-07:00",
            event_end_date="2026-06-01T11:00:00-07:00",
            summary="Team sync",
            attendees=["alice@example.com"],
            time_zone="America/Los_Angeles",
        )
    )

    assert isinstance(result_dict, dict)
    result = ScheduleMeetingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.event_id == "evt_fake_id_123"
    assert result.meet_link == "https://meet.google.com/fake-meet-link"
    assert result.summary == "Team sync"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"


@pytest.mark.asyncio
async def test_list_color_id_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/colors",
        json={
            # TODO: fill in the full color palette from Google Calendar's /colors response.
            "kind": "calendar#colors",
            "updated": "2024-01-01T00:00:00.000Z",
            "calendar": {},
            "event": {
                "1": {"background": "#a4bdfc", "foreground": "#1d1d1d"},
                "2": {"background": "#7ae7bf", "foreground": "#1d1d1d"},
            },
        },
    )

    result_dict = await list_color_id_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListColorIdOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 2
    assert {opt.id for opt in result.options} == {"1", "2"}

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"


# --- Failure-path coverage --------------------------------------------------


@pytest.mark.asyncio
async def test_schedule_meeting_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=re.compile(rf"{re.escape(API)}/calendars/primary/events.*"),
        status_code=401,
        text="Invalid Credentials",
    )

    result_dict = await schedule_meeting.ainvoke(
        _args(
            event_start_date="2026-06-01T10:00:00-07:00",
            event_end_date="2026-06-01T11:00:00-07:00",
        )
    )
    result = ScheduleMeetingOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_schedule_meeting_missing_token() -> None:
    """Missing OAuth access_token short-circuits before the HTTP call."""
    result_dict = await schedule_meeting.ainvoke(
        {
            "auth_type": "oauth2",
            "auth_data": {},
            "event_start_date": "2026-06-01",
            "event_end_date": "2026-06-02",
        }
    )
    result = ScheduleMeetingOutput.model_validate(result_dict)
    assert result.success is False
    assert "access_token" in (result.error or "")
