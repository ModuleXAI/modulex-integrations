"""Happy-path tests for every zoom @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.zoom import (
    TOOLS,
    add_meeting_registrant,
    add_webinar_registrant,
    create_meeting,
    create_user,
    delete_meeting,
    delete_user,
    get_current_user,
    get_meeting_details,
    get_meeting_recordings,
    get_meeting_summary,
    get_meeting_transcript,
    get_webinar_details,
    list_all_recordings,
    list_call_recordings,
    list_channels,
    list_meetings,
    list_past_meeting_participants,
    list_past_webinar_qa,
    list_user_call_logs,
    list_webinar_participants_report,
    manifest,
    send_chat_message,
    update_meeting,
    update_webinar,
)
from modulex_integrations.tools.zoom.outputs import (
    AddMeetingRegistrantOutput,
    AddWebinarRegistrantOutput,
    CreateMeetingOutput,
    CreateUserOutput,
    DeleteMeetingOutput,
    DeleteUserOutput,
    GetCurrentUserOutput,
    GetMeetingDetailsOutput,
    GetMeetingRecordingsOutput,
    GetMeetingSummaryOutput,
    GetMeetingTranscriptOutput,
    GetWebinarDetailsOutput,
    ListAllRecordingsOutput,
    ListCallRecordingsOutput,
    ListChannelsOutput,
    ListMeetingsOutput,
    ListPastMeetingParticipantsOutput,
    ListPastWebinarQaOutput,
    ListUserCallLogsOutput,
    ListWebinarParticipantsReportOutput,
    SendChatMessageOutput,
    UpdateMeetingOutput,
    UpdateWebinarOutput,
)

API = "https://api.zoom.us/v2"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_23_actions(self) -> None:
        assert len(manifest.actions) == 23

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_meeting(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/me/meetings",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": 12345678,
            "uuid": "abc123",
            "topic": "Test Meeting",
            "start_time": "2024-01-01T10:00:00Z",
            "join_url": "https://zoom.us/j/12345678",
            "password": "abc123",
            "start_url": "https://zoom.us/s/12345678",
        },
        status_code=201,
    )

    result_dict = await create_meeting.ainvoke(_args(topic="Test Meeting"))

    assert isinstance(result_dict, dict)
    result = CreateMeetingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == 12345678


@pytest.mark.asyncio
async def test_list_meetings(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me/meetings",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "meetings": [
                {"id": 1, "uuid": "u1", "topic": "Daily Standup", "type": 2}
            ],
            "total_records": 1,
        },
    )

    result_dict = await list_meetings.ainvoke(_args(user_id="me"))

    assert isinstance(result_dict, dict)
    result = ListMeetingsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.meetings) == 1


@pytest.mark.asyncio
async def test_get_meeting_details(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/meetings/12345",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": 12345,
            "uuid": "abc",
            "topic": "Team Sync",
            "type": 2,
            "status": "waiting",
        },
    )

    result_dict = await get_meeting_details.ainvoke(_args(meeting_id="12345"))

    assert isinstance(result_dict, dict)
    result = GetMeetingDetailsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == 12345


@pytest.mark.asyncio
async def test_update_meeting(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/meetings/12345",
        status_code=204,
    )

    result_dict = await update_meeting.ainvoke(_args(meeting_id="12345", topic="New Topic"))

    assert isinstance(result_dict, dict)
    result = UpdateMeetingOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_meeting(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/meetings/12345",
        status_code=204,
    )

    result_dict = await delete_meeting.ainvoke(_args(meeting_id="12345"))

    assert isinstance(result_dict, dict)
    result = DeleteMeetingOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_current_user(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me",
        json={
            "id": "user123",
            "first_name": "Jane",
            "last_name": "Doe",
            "display_name": "Jane Doe",
            "email": "jane@example.com",
            "account_id": "acc123",
            "timezone": "America/New_York",
            "type": 2,
        },
    )

    result_dict = await get_current_user.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetCurrentUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user is not None
    assert result.user.email == "jane@example.com"


@pytest.mark.asyncio
async def test_send_chat_message(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/chat/users/me/messages",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "msg123",
        },
        status_code=201,
    )

    result_dict = await send_chat_message.ainvoke(
        _args(message="Hello!", to_contact="test@example.com")
    )

    assert isinstance(result_dict, dict)
    result = SendChatMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "msg123"


@pytest.mark.asyncio
async def test_list_channels(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/chat/users/me/channels",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "channels": [{"id": "ch1", "name": "General"}],
        },
    )

    result_dict = await list_channels.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListChannelsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.channels) == 1


@pytest.mark.asyncio
async def test_add_meeting_registrant(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/meetings/12345/registrants",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "reg1",
            "registrant_id": "r123",
            "start_time": "2024-01-01T10:00:00Z",
            "join_url": "https://zoom.us/j/12345",
            "topic": "Test",
        },
        status_code=201,
    )

    result_dict = await add_meeting_registrant.ainvoke(
        _args(
            meeting_id="12345",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
        )
    )

    assert isinstance(result_dict, dict)
    result = AddMeetingRegistrantOutput.model_validate(result_dict)
    assert result.success is True
    assert result.registrant is not None


@pytest.mark.asyncio
async def test_get_meeting_recordings(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/meetings/12345/recordings",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "recording_files": [
                {
                    "id": "rf1",
                    "file_type": "MP4",
                    "file_size": 1024000,
                    "download_url": "https://zoom.us/rec/download/abc",
                    "recording_type": "shared_screen_with_speaker_view",
                }
            ],
        },
    )

    result_dict = await get_meeting_recordings.ainvoke(_args(meeting_id="12345"))

    assert isinstance(result_dict, dict)
    result = GetMeetingRecordingsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.recording_files) == 1


@pytest.mark.asyncio
async def test_get_meeting_transcript(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/meetings/12345/recordings?include_fields=download_access_token",
        json={
            "recording_files": [
                {
                    "file_type": "TRANSCRIPT",
                    "download_url": "https://zoom.us/rec/download/vtt123",
                }
            ],
            "download_access_token": "tok123",
        },
    )
    httpx_mock.add_response(
        method="GET",
        url="https://zoom.us/rec/download/vtt123?access_token=tok123",
        text="WEBVTT\n\n1\n00:00:01.000 --> 00:00:05.000\nSpeaker: Hello everyone\n",
    )

    result_dict = await get_meeting_transcript.ainvoke(_args(meeting_id="12345"))

    assert isinstance(result_dict, dict)
    result = GetMeetingTranscriptOutput.model_validate(result_dict)
    assert result.success is True
    assert "Hello everyone" in (result.transcript_text or "")


@pytest.mark.asyncio
async def test_get_meeting_summary(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/meetings/12345/meeting_summary",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "meeting_id": 12345,
            "meeting_uuid": "abc",
            "summary_title": "Team Sync Summary",
            "summary_overview": "Discussed project updates",
            "next_steps": ["Follow up on task A"],
        },
    )

    result_dict = await get_meeting_summary.ainvoke(_args(meeting_id="12345"))

    assert isinstance(result_dict, dict)
    result = GetMeetingSummaryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.summary is not None


@pytest.mark.asyncio
async def test_list_all_recordings(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me/recordings",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "meetings": [
                {
                    "uuid": "u1",
                    "id": 123,
                    "topic": "Recorded Meeting",
                    "recording_files": [],
                }
            ],
            "total_records": 1,
        },
    )

    result_dict = await list_all_recordings.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListAllRecordingsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.meetings) == 1


@pytest.mark.asyncio
async def test_list_call_recordings(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/phone/recordings",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "recordings": [{"id": "rec1", "caller_number": "+1234567890"}],
            "total_records": 1,
        },
    )

    result_dict = await list_call_recordings.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListCallRecordingsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.recordings) == 1


@pytest.mark.asyncio
async def test_list_user_call_logs(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/phone/users/user123/call_logs",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "call_logs": [{"id": "cl1", "direction": "inbound"}],
            "total_records": 1,
        },
    )

    result_dict = await list_user_call_logs.ainvoke(_args(user_id="user123"))

    assert isinstance(result_dict, dict)
    result = ListUserCallLogsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.call_logs) == 1


@pytest.mark.asyncio
async def test_list_past_meeting_participants(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/past_meetings/12345/participants",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "participants": [
                {
                    "id": "p1",
                    "name": "Jane",
                    "user_email": "jane@example.com",
                    "join_time": "2024-01-01T10:00:00Z",
                    "leave_time": "2024-01-01T11:00:00Z",
                    "duration": 3600,
                }
            ],
            "total_records": 1,
        },
    )

    result_dict = await list_past_meeting_participants.ainvoke(_args(meeting_id="12345"))

    assert isinstance(result_dict, dict)
    result = ListPastMeetingParticipantsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.participants) == 1


@pytest.mark.asyncio
async def test_create_user(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "newuser123",
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "type": 1,
        },
        status_code=201,
    )

    result_dict = await create_user.ainvoke(
        _args(action="create", email="new@example.com", type=1)
    )

    assert isinstance(result_dict, dict)
    result = CreateUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "newuser123"


@pytest.mark.asyncio
async def test_delete_user(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/users/user123",
        status_code=204,
    )

    result_dict = await delete_user.ainvoke(_args(user_id="user123"))

    assert isinstance(result_dict, dict)
    result = DeleteUserOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_webinar_details(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/webinars/99999",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": 99999,
            "uuid": "web-uuid",
            "topic": "Product Demo",
            "type": 5,
            "start_time": "2024-02-01T14:00:00Z",
            "duration": 60,
            "timezone": "America/New_York",
            "join_url": "https://zoom.us/w/99999",
            "host_email": "host@example.com",
        },
    )

    result_dict = await get_webinar_details.ainvoke(_args(webinar_id="99999"))

    assert isinstance(result_dict, dict)
    result = GetWebinarDetailsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == 99999


@pytest.mark.asyncio
async def test_update_webinar(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/webinars/99999",
        status_code=204,
    )

    result_dict = await update_webinar.ainvoke(_args(webinar_id="99999", topic="Updated"))

    assert isinstance(result_dict, dict)
    result = UpdateWebinarOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_add_webinar_registrant(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/webinars/99999/registrants",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "wreg1",
            "registrant_id": "wr123",
            "start_time": "2024-02-01T14:00:00Z",
            "join_url": "https://zoom.us/w/99999",
            "topic": "Product Demo",
        },
        status_code=201,
    )

    result_dict = await add_webinar_registrant.ainvoke(
        _args(
            webinar_id="99999",
            email="attendee@example.com",
            first_name="Bob",
            last_name="Smith",
        )
    )

    assert isinstance(result_dict, dict)
    result = AddWebinarRegistrantOutput.model_validate(result_dict)
    assert result.success is True
    assert result.registrant is not None


@pytest.mark.asyncio
async def test_list_webinar_participants_report(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/report/webinars/99999/participants",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "participants": [
                {
                    "id": "wp1",
                    "name": "Attendee",
                    "user_email": "a@example.com",
                    "join_time": "2024-02-01T14:00:00Z",
                    "leave_time": "2024-02-01T15:00:00Z",
                    "duration": 3600,
                }
            ],
            "total_records": 1,
        },
    )

    result_dict = await list_webinar_participants_report.ainvoke(_args(webinar_id="99999"))

    assert isinstance(result_dict, dict)
    result = ListWebinarParticipantsReportOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.participants) == 1


@pytest.mark.asyncio
async def test_list_past_webinar_qa(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/past_webinars/99999/qa",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "questions": [
                {
                    "name": "Attendee",
                    "email": "a@example.com",
                    "question_details": [
                        {"question": "When does it ship?", "answer": "Q2 2024"}
                    ],
                }
            ],
        },
    )

    result_dict = await list_past_webinar_qa.ainvoke(_args(webinar_id="99999"))

    assert isinstance(result_dict, dict)
    result = ListPastWebinarQaOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.questions) == 1
    assert result.questions[0].question == "When does it ship?"


@pytest.mark.asyncio
async def test_create_meeting_empty_credentials() -> None:
    """Failure path: empty access token returns error without hitting the wire."""
    from modulex_integrations.tools.zoom.outputs import CreateMeetingOutput

    result_dict = await create_meeting.ainvoke(
        _args(auth_data={"access_token": ""}, topic="Should Fail")
    )

    assert isinstance(result_dict, dict)
    result = CreateMeetingOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "access token" in result.error.lower()
