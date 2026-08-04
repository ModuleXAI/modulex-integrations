"""Happy-path tests per action plus failure-path, parse-guard, and
empty-credential tests for the non-2xx -> success=False branch (Fathom
tools don't raise)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.fathom import (
    TOOLS,
    get_summary,
    get_transcript,
    list_meeting_types,
    list_meetings,
    list_team_members,
    list_teams,
    manifest,
)
from modulex_integrations.tools.fathom.outputs import (
    GetSummaryOutput,
    GetTranscriptOutput,
    ListMeetingsOutput,
    ListMeetingTypesOutput,
    ListTeamMembersOutput,
    ListTeamsOutput,
)

API = "https://api.fathom.ai/external/v1"
_API_KEY = "fathom-fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_6_actions(self) -> None:
        assert len(manifest.actions) == 6

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_list_meetings(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        json={
            "limit": 10,
            "next_cursor": "eyJwYWdlX251bSI6Mn0=",
            "items": [
                {
                    "title": "Quarterly Business Review",
                    "meeting_title": "QBR 2025 Q1",
                    "meeting_type": "Quarterly Business Review",
                    "recording_id": 123456789,
                    "url": "https://fathom.video/xyz123",
                    "meeting_url": "https://us02web.zoom.us/j/123456789",
                    "share_url": "https://fathom.video/share/xyz123",
                    "created_at": "2025-03-01T17:01:30Z",
                    "scheduled_start_time": "2025-03-01T16:00:00Z",
                    "scheduled_end_time": "2025-03-01T17:00:00Z",
                    "recording_start_time": "2025-03-01T16:01:12Z",
                    "recording_end_time": "2025-03-01T17:00:55Z",
                    "transcript_language": "en",
                    "calendar_invitees_domains_type": "one_or_more_external",
                    "shared_with": "single_team",
                    "recorded_by": {
                        "name": "Alice Johnson",
                        "email": "alice.johnson@acme.com",
                        "email_domain": "acme.com",
                        "team": "Customer Success",
                    },
                    "calendar_invitees": [
                        {
                            "name": "John Smith",
                            "email": "john.smith@client.com",
                            "email_domain": "client.com",
                            "is_external": True,
                            "matched_speaker_display_name": "John Smith",
                        }
                    ],
                    "default_summary": {
                        "template_name": "general",
                        "markdown_formatted": "## Summary\n\nWe reviewed Q1 OKRs.",
                    },
                    "transcript": [
                        {
                            "speaker": {
                                "display_name": "Jane Doe",
                                "matched_calendar_invitee_email": "jane.doe@acme.com",
                            },
                            "text": "Let's revisit the budget allocations.",
                            "timestamp": "00:05:32",
                        }
                    ],
                    "action_items": [
                        {
                            "description": "Email revised proposal to client",
                            "user_generated": False,
                            "completed": False,
                            "recording_timestamp": "00:10:45",
                            "recording_playback_url": "https://fathom.video/xyz123#t=645",
                            "assignee": {
                                "name": "Jane Doe",
                                "email": "jane.doe@acme.com",
                                "team": "Marketing",
                            },
                        }
                    ],
                    "highlights": [
                        {
                            "type": "Objection",
                            "summary": "Pushed back on price",
                            "text": "They pushed back hard on the price",
                            "start_time": 16,
                            "end_time": 27.5,
                        }
                    ],
                    "crm_matches": {
                        "contacts": [
                            {
                                "name": "John Smith",
                                "email": "john.smith@client.com",
                                "record_url": "https://app.hubspot.com/contacts/123",
                            }
                        ],
                        "companies": [
                            {
                                "name": "Acme Corp",
                                "record_url": "https://app.hubspot.com/companies/456",
                            }
                        ],
                        "deals": [
                            {
                                "name": "Q1 Renewal",
                                "amount": 50000,
                                "record_url": "https://app.hubspot.com/deals/789",
                            }
                        ],
                        "error": None,
                    },
                }
            ],
        },
    )

    result_dict = await list_meetings.ainvoke(
        _args(
            include_summary=True,
            include_transcript=True,
            include_action_items=True,
            include_crm_matches=True,
            include_highlights=True,
            created_after="2025-01-01T00:00:00Z",
            created_before="2025-12-31T23:59:59Z",
            recorded_by="alice.johnson@acme.com",
            teams="Sales",
            meeting_type="Quarterly Business Review",
            calendar_invitees_domains="client.com",
            calendar_invitees_domains_type="one_or_more_external",
            cursor="prev-cursor",
        )
    )

    assert isinstance(result_dict, dict)

    result = ListMeetingsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.limit == 10
    assert result.next_cursor == "eyJwYWdlX251bSI6Mn0="

    meeting = result.meetings[0]
    assert meeting.recording_id == 123456789
    assert meeting.transcript_language == "en"
    assert meeting.recorded_by is not None
    assert meeting.recorded_by.email == "alice.johnson@acme.com"
    assert meeting.calendar_invitees[0].is_external is True
    assert meeting.default_summary is not None
    assert meeting.default_summary.template_name == "general"
    assert meeting.transcript is not None
    assert meeting.transcript[0].speaker is not None
    assert meeting.transcript[0].speaker.display_name == "Jane Doe"
    assert meeting.action_items is not None
    assert meeting.action_items[0].assignee is not None
    assert meeting.action_items[0].assignee.team == "Marketing"
    assert meeting.highlights is not None
    assert meeting.highlights[0].start_time == 16.0
    assert meeting.highlights[0].end_time == 27.5
    assert meeting.crm_matches is not None
    assert meeting.crm_matches.deals[0].amount == 50000.0

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["X-Api-Key"] == _API_KEY
    assert sent.url.path == "/external/v1/meetings"
    params = sent.url.params
    assert params["include_summary"] == "true"
    assert params["include_transcript"] == "true"
    assert params["include_action_items"] == "true"
    assert params["include_crm_matches"] == "true"
    assert params["include_highlights"] == "true"
    assert params["created_after"] == "2025-01-01T00:00:00Z"
    assert params["created_before"] == "2025-12-31T23:59:59Z"
    assert params["recorded_by[]"] == "alice.johnson@acme.com"
    assert params["teams[]"] == "Sales"
    assert params["meeting_type"] == "Quarterly Business Review"
    assert params["calendar_invitees_domains[]"] == "client.com"
    assert params["calendar_invitees_domains_type"] == "one_or_more_external"
    assert params["cursor"] == "prev-cursor"


@pytest.mark.asyncio
async def test_list_meetings_without_filters(httpx_mock):  # type: ignore[no-untyped-def]
    """No filters -> a bare GET; optional blocks stay None on each meeting."""
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/meetings",
        json={
            "limit": 10,
            "next_cursor": None,
            "items": [
                {
                    "title": "Standup",
                    "meeting_title": None,
                    "meeting_type": None,
                    "recording_id": 42,
                    "url": "https://fathom.video/abc",
                    "meeting_url": None,
                    "share_url": "https://fathom.video/share/abc",
                    "created_at": "2026-02-01T09:00:00Z",
                    "transcript_language": "en",
                    "calendar_invitees": [],
                    "recorded_by": None,
                }
            ],
        },
    )

    result_dict = await list_meetings.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = ListMeetingsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.next_cursor is None
    assert result.meetings[0].title == "Standup"
    assert result.meetings[0].recorded_by is None
    assert result.meetings[0].transcript is None
    assert result.meetings[0].action_items is None
    assert result.meetings[0].highlights is None
    assert result.meetings[0].crm_matches is None
    assert result.meetings[0].calendar_invitees == []


@pytest.mark.asyncio
async def test_list_meetings_rejects_unknown_domain_type() -> None:
    """The invitee-domain filter is a closed enum; a miss short-circuits."""
    result_dict = await list_meetings.ainvoke(
        _args(calendar_invitees_domains_type="everyone")
    )

    assert isinstance(result_dict, dict)

    result = ListMeetingsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "one_or_more_external" in result.error


@pytest.mark.asyncio
async def test_list_meeting_types(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/meeting_types?cursor=abc",
        json={
            "limit": 2,
            "next_cursor": None,
            "items": [
                {
                    "name": "Quarterly Business Review",
                    "status": "active",
                    "created_at": "2023-11-10T12:00:00Z",
                },
                {
                    "name": "Onboarding Call",
                    "status": "inactive",
                    "created_at": "2022-05-04T08:00:00Z",
                },
            ],
        },
    )

    result_dict = await list_meeting_types.ainvoke(_args(cursor="abc"))

    assert isinstance(result_dict, dict)

    result = ListMeetingTypesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.limit == 2
    assert [t.name for t in result.meeting_types] == [
        "Quarterly Business Review",
        "Onboarding Call",
    ]
    assert result.meeting_types[1].status == "inactive"


@pytest.mark.asyncio
async def test_get_summary(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/recordings/123456789/summary",
        json={
            "summary": {
                "template_name": "general",
                "markdown_formatted": "## Summary\n\nWe agreed to revisit projections.",
            }
        },
    )

    result_dict = await get_summary.ainvoke(_args(recording_id="123456789"))

    assert isinstance(result_dict, dict)

    result = GetSummaryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.template_name == "general"
    assert result.markdown_formatted is not None
    assert "revisit projections" in result.markdown_formatted

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["X-Api-Key"] == _API_KEY


@pytest.mark.asyncio
async def test_get_summary_accepts_flat_payload(httpx_mock):  # type: ignore[no-untyped-def]
    """A payload without the "summary" wrapper still parses."""
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/recordings/987/summary",
        json={"template_name": None, "markdown_formatted": "## Recap"},
    )

    result_dict = await get_summary.ainvoke(_args(recording_id=" 987 "))

    assert isinstance(result_dict, dict)

    result = GetSummaryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.template_name is None
    assert result.markdown_formatted == "## Recap"


@pytest.mark.asyncio
async def test_get_transcript(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/recordings/123456789/transcript",
        json={
            "transcript": [
                {
                    "speaker": {
                        "display_name": "Jane Doe",
                        "matched_calendar_invitee_email": "jane.doe@acme.com",
                    },
                    "text": "Let's revisit the budget allocations.",
                    "timestamp": "00:05:32",
                },
                {
                    "speaker": {
                        "display_name": "John Smith",
                        "matched_calendar_invitee_email": None,
                    },
                    "text": "I agree.",
                    "timestamp": "00:05:40",
                },
            ]
        },
    )

    result_dict = await get_transcript.ainvoke(_args(recording_id="123456789"))

    assert isinstance(result_dict, dict)

    result = GetTranscriptOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.transcript) == 2
    assert result.transcript[0].speaker is not None
    assert result.transcript[0].speaker.display_name == "Jane Doe"
    assert result.transcript[0].timestamp == "00:05:32"
    assert result.transcript[1].speaker is not None
    assert result.transcript[1].speaker.matched_calendar_invitee_email is None


@pytest.mark.asyncio
async def test_get_transcript_accepts_bare_array(httpx_mock):  # type: ignore[no-untyped-def]
    """A top-level array body is handled instead of raising past @tool."""
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/recordings/555/transcript",
        json=[
            {
                "speaker": {"display_name": "Alice Johnson"},
                "text": "Hello everyone.",
                "timestamp": "00:00:04",
            }
        ],
    )

    result_dict = await get_transcript.ainvoke(_args(recording_id="555"))

    assert isinstance(result_dict, dict)

    result = GetTranscriptOutput.model_validate(result_dict)
    assert result.success is True
    assert result.transcript[0].text == "Hello everyone."
    assert result.transcript[0].speaker is not None
    assert result.transcript[0].speaker.matched_calendar_invitee_email is None


@pytest.mark.asyncio
async def test_get_transcript_encodes_recording_id(httpx_mock):  # type: ignore[no-untyped-def]
    """A recording id can never escape its path segment."""
    httpx_mock.add_response(method="GET", json={"transcript": []})

    result_dict = await get_transcript.ainvoke(_args(recording_id="12/34"))

    assert isinstance(result_dict, dict)

    result = GetTranscriptOutput.model_validate(result_dict)
    assert result.success is True

    sent = httpx_mock.get_requests()[0]
    assert str(sent.url) == f"{API}/recordings/12%2F34/transcript"


@pytest.mark.asyncio
async def test_list_team_members(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/team_members?team=Sales&cursor=abc",
        json={
            "limit": 1,
            "next_cursor": "next",
            "items": [
                {
                    "name": "Bob Lee",
                    "email": "bob.lee@acme.com",
                    "created_at": "2024-06-01T08:30:00Z",
                }
            ],
        },
    )

    result_dict = await list_team_members.ainvoke(_args(team="Sales", cursor="abc"))

    assert isinstance(result_dict, dict)

    result = ListTeamMembersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.members[0].name == "Bob Lee"
    assert result.members[0].email == "bob.lee@acme.com"
    assert result.next_cursor == "next"


@pytest.mark.asyncio
async def test_list_teams(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/teams",
        json={
            "limit": 2,
            "next_cursor": None,
            "items": [
                {"name": "Sales", "created_at": "2023-11-10T12:00:00Z"},
                {"name": "Engineering", "created_at": "2024-01-02T09:00:00Z"},
            ],
        },
    )

    result_dict = await list_teams.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = ListTeamsOutput.model_validate(result_dict)
    assert result.success is True
    assert [t.name for t in result.teams] == ["Sales", "Engineering"]
    assert result.next_cursor is None
    assert result.limit == 2


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_list_meetings_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """Fathom errors come back as HTTP 4xx/5xx; the tool wraps them in
    ``success=False`` + ``error`` rather than raising."""
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/meetings",
        status_code=401,
        json={"message": "Invalid API key"},
    )

    result_dict = await list_meetings.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = ListMeetingsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error
    assert "Invalid API key" in result.error


@pytest.mark.asyncio
async def test_get_summary_error_on_non_json_body(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/recordings/1/summary",
        status_code=429,
        text="Too Many Requests",
    )

    result_dict = await get_summary.ainvoke(_args(recording_id="1"))

    assert isinstance(result_dict, dict)

    result = GetSummaryOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "429" in result.error
    assert "Too Many Requests" in result.error


@pytest.mark.asyncio
async def test_list_teams_survives_non_object_body(httpx_mock):  # type: ignore[no-untyped-def]
    """A 200 whose body is a bare array degrades to an empty result rather
    than raising through the @tool boundary."""
    httpx_mock.add_response(method="GET", url=f"{API}/teams", json=[])

    result_dict = await list_teams.ainvoke(_args())

    assert isinstance(result_dict, dict)

    result = ListTeamsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.teams == []
    assert result.next_cursor is None


@pytest.mark.asyncio
async def test_list_meetings_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await list_meetings.ainvoke({"api_key": ""})

    assert isinstance(result_dict, dict)

    result = ListMeetingsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_get_transcript_validates_empty_api_key() -> None:
    result_dict = await get_transcript.ainvoke({"recording_id": "1", "api_key": "   "})

    assert isinstance(result_dict, dict)

    result = GetTranscriptOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_list_meeting_types_validates_empty_api_key() -> None:
    result_dict = await list_meeting_types.ainvoke({"api_key": ""})

    assert isinstance(result_dict, dict)

    result = ListMeetingTypesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_list_team_members_validates_empty_api_key() -> None:
    result_dict = await list_team_members.ainvoke({"api_key": ""})

    assert isinstance(result_dict, dict)

    result = ListTeamMembersOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_list_teams_validates_empty_api_key() -> None:
    result_dict = await list_teams.ainvoke({"api_key": ""})

    assert isinstance(result_dict, dict)

    result = ListTeamsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error


@pytest.mark.asyncio
async def test_get_summary_validates_empty_recording_id() -> None:
    result_dict = await get_summary.ainvoke(_args(recording_id="  "))

    assert isinstance(result_dict, dict)

    result = GetSummaryOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "recording_id" in result.error
