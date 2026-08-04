"""Happy-path tests per action, plus the failure paths that matter for a
GraphQL API that answers HTTP 200 for everything: a top-level ``errors``
array, a coded error, a non-200 response, a non-object body, a wrongly typed
200 body, and an empty credential."""
from __future__ import annotations

import json
from typing import Any

import pytest

from modulex_integrations.tools.fireflies import (
    TOOLS,
    add_to_live_meeting,
    create_bite,
    delete_transcript,
    get_transcript,
    get_user,
    list_bites,
    list_contacts,
    list_transcripts,
    list_users,
    manifest,
    upload_audio,
)
from modulex_integrations.tools.fireflies.outputs import (
    AddToLiveMeetingOutput,
    CreateBiteOutput,
    DeleteTranscriptOutput,
    GetTranscriptOutput,
    GetUserOutput,
    ListBitesOutput,
    ListContactsOutput,
    ListTranscriptsOutput,
    ListUsersOutput,
    UploadAudioOutput,
)

API = "https://api.fireflies.ai/graphql"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


def _sent_variables(httpx_mock: Any, index: int = 0) -> dict[str, Any]:
    body = json.loads(httpx_mock.get_requests()[index].content)
    variables = body.get("variables")
    return variables if isinstance(variables, dict) else {}


def _sent_query(httpx_mock: Any, index: int = 0) -> str:
    body = json.loads(httpx_mock.get_requests()[index].content)
    query = body.get("query")
    return query if isinstance(query, str) else ""


_TRANSCRIPT_SUMMARY_NODE: dict[str, Any] = {
    "id": "tr_1",
    "title": "Weekly sync",
    "date": 1767225600000,
    "duration": 32.5,
    "host_email": "host@example.com",
    "participants": ["host@example.com", "guest@example.com"],
}

_TRANSCRIPT_NODE: dict[str, Any] = {
    **_TRANSCRIPT_SUMMARY_NODE,
    "dateString": "2026-01-01T00:00:00.000Z",
    "privacy": "public",
    "transcript_url": "https://app.fireflies.ai/view/tr_1",
    "audio_url": "https://cdn.fireflies.ai/tr_1.mp3",
    "video_url": "https://cdn.fireflies.ai/tr_1.mp4",
    "meeting_link": "https://zoom.us/j/123",
    "organizer_email": "host@example.com",
    "fireflies_users": ["host@example.com"],
    "speakers": [{"id": 0, "name": "Ada"}, {"id": 1, "name": "Grace"}],
    "meeting_attendees": [
        {
            "displayName": "Ada Lovelace",
            "email": "ada@example.com",
            "phoneNumber": None,
            "name": "Ada",
            "location": None,
        }
    ],
    "sentences": [
        {
            "index": 0,
            "speaker_name": "Ada",
            "speaker_id": 0,
            "text": "Let's ship it on Friday.",
            "raw_text": "lets ship it on friday",
            "start_time": 12.5,
            "end_time": 15.25,
            "ai_filters": {
                "task": True,
                "pricing": False,
                "metric": False,
                "question": False,
                "date_and_time": True,
                "sentiment": "positive",
            },
        }
    ],
    "summary": {
        "keywords": ["release", "friday"],
        "action_items": "Ada: cut the release branch",
        "outline": "00:00 Intro",
        "shorthand_bullet": "- ship friday",
        "overview": "The team agreed to ship on Friday.",
        "bullet_gist": "- ship friday",
        "gist": "Ship on Friday",
        "short_summary": "Ship on Friday.",
        "short_overview": "Release planning.",
        "meeting_type": "internal",
        "topics_discussed": ["release", "qa"],
    },
    "analytics": {
        "sentiments": {
            "negative_pct": 5.0,
            "neutral_pct": 70.0,
            "positive_pct": 25.0,
        },
        "categories": {"questions": 4, "date_times": 2, "metrics": 1, "tasks": 3},
        "speakers": [
            {
                "speaker_id": 0,
                "name": "Ada",
                "duration": 600.0,
                "word_count": 1200,
                "longest_monologue": 95.5,
                "monologues_count": 4,
                "filler_words": 12,
                "questions": 3,
                "duration_pct": 62.5,
                "words_per_minute": 120.0,
            }
        ],
    },
}

_USER_NODE: dict[str, Any] = {
    "user_id": "user_1",
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "integrations": ["slack", "notion"],
    "is_admin": True,
    "minutes_consumed": 480.5,
    "num_transcripts": 42,
    "recent_transcript": "tr_1",
    "recent_meeting": "2026-01-01T00:00:00.000Z",
}

_BITE_NODE: dict[str, Any] = {
    "id": "bite_1",
    "name": "Decision moment",
    "transcript_id": "tr_1",
    "user_id": "user_1",
    "start_time": 30.0,
    "end_time": 90.0,
    "status": "pending",
    "summary": "The team commits to Friday.",
    "media_type": "video",
    "thumbnail": "https://cdn.fireflies.ai/bite_1.jpg",
    "preview": "https://cdn.fireflies.ai/bite_1.gif",
    "created_at": "2026-01-02T09:00:00.000Z",
}


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_10_actions(self) -> None:
        assert len(manifest.actions) == 10

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_list_transcripts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"transcripts": [_TRANSCRIPT_SUMMARY_NODE]}},
    )

    result_dict = await list_transcripts.ainvoke(
        _args(
            keyword="release",
            from_date="2026-01-01T00:00:00Z",
            to_date="2026-02-01T00:00:00Z",
            host_email="host@example.com",
            participants="ada@example.com, grace@example.com",
            limit=200,
            skip=10,
        )
    )
    assert isinstance(result_dict, dict)
    result = ListTranscriptsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.transcripts[0].id == "tr_1"
    assert result.transcripts[0].participants == [
        "host@example.com",
        "guest@example.com",
    ]

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"
    variables = _sent_variables(httpx_mock)
    assert variables["keyword"] == "release"
    assert variables["host_email"] == "host@example.com"
    assert variables["participants"] == ["ada@example.com", "grace@example.com"]
    # The API caps a page at 50 records.
    assert variables["limit"] == 50
    assert variables["skip"] == 10


@pytest.mark.asyncio
async def test_get_transcript(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=API, json={"data": {"transcript": _TRANSCRIPT_NODE}}
    )

    result_dict = await get_transcript.ainvoke(_args(transcript_id="tr_1"))
    assert isinstance(result_dict, dict)
    result = GetTranscriptOutput.model_validate(result_dict)
    assert result.success is True
    assert result.transcript is not None
    transcript = result.transcript
    assert transcript.date_string == "2026-01-01T00:00:00.000Z"
    assert transcript.audio_url == "https://cdn.fireflies.ai/tr_1.mp3"
    assert [speaker.name for speaker in transcript.speakers] == ["Ada", "Grace"]
    assert transcript.meeting_attendees[0].display_name == "Ada Lovelace"
    assert transcript.sentences[0].text == "Let's ship it on Friday."
    assert transcript.sentences[0].start_time == 12.5
    assert transcript.sentences[0].ai_filters is not None
    assert transcript.sentences[0].ai_filters.task is True
    assert transcript.summary is not None
    assert transcript.summary.keywords == ["release", "friday"]
    assert transcript.summary.topics_discussed == ["release", "qa"]
    assert transcript.summary.gist == "Ship on Friday"
    assert transcript.analytics is not None
    assert transcript.analytics.categories is not None
    assert transcript.analytics.categories.questions == 4
    assert transcript.analytics.speakers[0].words_per_minute == 120.0

    assert _sent_variables(httpx_mock) == {"id": "tr_1"}


@pytest.mark.asyncio
async def test_get_user_defaults_to_key_owner(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=API, json={"data": {"user": _USER_NODE}})

    result_dict = await get_user.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = GetUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user is not None
    assert result.user.user_id == "user_1"
    assert result.user.integrations == ["slack", "notion"]
    assert result.user.num_transcripts == 42
    assert result.user.minutes_consumed == 480.5

    # `id` is omitted entirely so the API falls back to the key owner.
    assert _sent_variables(httpx_mock) == {}


@pytest.mark.asyncio
async def test_get_user_by_id(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=API, json={"data": {"user": _USER_NODE}})

    result_dict = await get_user.ainvoke(_args(user_id="user_1"))
    result = GetUserOutput.model_validate(result_dict)
    assert result.success is True
    assert _sent_variables(httpx_mock) == {"id": "user_1"}


@pytest.mark.asyncio
async def test_list_users(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=API, json={"data": {"users": [_USER_NODE, {"user_id": "user_2"}]}}
    )

    result_dict = await list_users.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListUsersOutput.model_validate(result_dict)
    assert result.success is True
    assert [user.user_id for user in result.users] == ["user_1", "user_2"]
    assert result.users[1].integrations == []


@pytest.mark.asyncio
async def test_upload_audio(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "uploadAudio": {
                    "success": True,
                    "title": "Customer call",
                    "message": "Upload successful",
                }
            }
        },
    )

    result_dict = await upload_audio.ainvoke(
        _args(
            audio_url="https://cdn.example.com/call.mp3",
            title="Customer call",
            webhook="https://hooks.example.com/fireflies",
            language="es",
            attendees=[{"displayName": "Ada", "email": "ada@example.com"}],
            client_reference_id="ref-42",
        )
    )
    assert isinstance(result_dict, dict)
    result = UploadAudioOutput.model_validate(result_dict)
    assert result.success is True
    assert result.uploaded is True
    assert result.title == "Customer call"
    assert result.message == "Upload successful"

    audio_input = _sent_variables(httpx_mock)["input"]
    assert audio_input["url"] == "https://cdn.example.com/call.mp3"
    assert audio_input["custom_language"] == "es"
    assert audio_input["client_reference_id"] == "ref-42"
    assert audio_input["webhook"] == "https://hooks.example.com/fireflies"
    assert audio_input["attendees"] == [
        {"displayName": "Ada", "email": "ada@example.com"}
    ]


@pytest.mark.asyncio
async def test_upload_audio_accepts_attendees_as_json_string(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"uploadAudio": {"success": True, "title": None, "message": "ok"}}},
    )

    result_dict = await upload_audio.ainvoke(
        _args(
            audio_url="https://cdn.example.com/call.mp3",
            attendees='[{"displayName": "Grace", "email": "grace@example.com"}]',
        )
    )
    result = UploadAudioOutput.model_validate(result_dict)
    assert result.success is True

    audio_input = _sent_variables(httpx_mock)["input"]
    assert audio_input["attendees"] == [
        {"displayName": "Grace", "email": "grace@example.com"}
    ]


@pytest.mark.asyncio
async def test_delete_transcript(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "deleteTranscript": {
                    "id": "tr_1",
                    "title": "Weekly sync",
                    "date": 1767225600000,
                    "duration": 32.5,
                    "host_email": "host@example.com",
                    "organizer_email": "host@example.com",
                }
            }
        },
    )

    result_dict = await delete_transcript.ainvoke(_args(transcript_id="tr_1"))
    assert isinstance(result_dict, dict)
    result = DeleteTranscriptOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True
    assert result.transcript is not None
    assert result.transcript.id == "tr_1"
    assert result.transcript.organizer_email == "host@example.com"


@pytest.mark.asyncio
async def test_add_to_live_meeting(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=API, json={"data": {"addToLiveMeeting": {"success": True}}}
    )

    result_dict = await add_to_live_meeting.ainvoke(
        _args(
            meeting_link="https://zoom.us/j/123",
            title="Standup",
            meeting_password="hunter2",
            duration=500,
            language="en",
        )
    )
    assert isinstance(result_dict, dict)
    result = AddToLiveMeetingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.added is True

    variables = _sent_variables(httpx_mock)
    assert variables["meetingLink"] == "https://zoom.us/j/123"
    assert variables["meeting_password"] == "hunter2"
    # Duration is clamped into the supported 15-120 minute window.
    assert variables["duration"] == 120


@pytest.mark.asyncio
async def test_create_bite(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "createBite": {
                    "id": "bite_1",
                    "name": "Decision moment",
                    "status": "pending",
                }
            }
        },
    )

    result_dict = await create_bite.ainvoke(
        _args(
            transcript_id="tr_1",
            start_time=30,
            end_time=90,
            name="Decision moment",
            media_type="Video",
            summary="The team commits to Friday.",
        )
    )
    assert isinstance(result_dict, dict)
    result = CreateBiteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.bite is not None
    assert result.bite.id == "bite_1"
    assert result.bite.status == "pending"

    variables = _sent_variables(httpx_mock)
    assert variables["transcriptId"] == "tr_1"
    assert variables["startTime"] == 30.0
    assert variables["endTime"] == 90.0
    assert variables["media_type"] == "video"


@pytest.mark.asyncio
async def test_list_bites(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=API, json={"data": {"bites": [_BITE_NODE]}})

    result_dict = await list_bites.ainvoke(
        _args(transcript_id="tr_1", mine=False, limit=10, skip=5)
    )
    assert isinstance(result_dict, dict)
    result = ListBitesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.bites) == 1
    assert result.bites[0].name == "Decision moment"
    assert result.bites[0].end_time == 90.0
    assert result.bites[0].media_type == "video"

    variables = _sent_variables(httpx_mock)
    assert variables["mine"] is False
    assert variables["transcript_id"] == "tr_1"
    assert variables["limit"] == 10
    assert variables["skip"] == 5


@pytest.mark.asyncio
async def test_list_contacts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "contacts": [
                    {
                        "email": "ada@example.com",
                        "name": "Ada Lovelace",
                        "picture": None,
                        "last_meeting_date": "2026-01-01T00:00:00.000Z",
                    }
                ]
            }
        },
    )

    result_dict = await list_contacts.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListContactsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.contacts[0].email == "ada@example.com"
    assert result.contacts[0].picture is None


# --- No user input ever lands in the query document -------------------------


@pytest.mark.asyncio
async def test_user_input_travels_in_variables_only(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=API, json={"data": {"transcripts": []}})

    injection = '") { id } } query Evil { users { email'
    result_dict = await list_transcripts.ainvoke(_args(keyword=injection))
    result = ListTranscriptsOutput.model_validate(result_dict)
    assert result.success is True

    assert injection not in _sent_query(httpx_mock)
    assert _sent_variables(httpx_mock)["keyword"] == injection


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_top_level_graphql_errors_surface(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": None,
            "errors": [
                {"message": "Invalid API key", "extensions": {"code": "auth_failed"}}
            ],
        },
    )

    result_dict = await list_transcripts.ainvoke(_args())
    result = ListTranscriptsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Invalid API key" in result.error
    assert "auth_failed" in result.error
    assert result.transcripts == []


@pytest.mark.asyncio
async def test_add_to_live_meeting_rate_limit_code(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "errors": [
                {"message": "too many requests", "extensions": {"code": "too_many_requests"}}
            ]
        },
    )

    result_dict = await add_to_live_meeting.ainvoke(
        _args(meeting_link="https://zoom.us/j/123")
    )
    result = AddToLiveMeetingOutput.model_validate(result_dict)
    assert result.success is False
    assert result.added is False
    assert result.error == (
        "Rate limit exceeded. This endpoint allows 3 requests per 20 minutes."
    )


@pytest.mark.asyncio
async def test_upload_audio_reports_upstream_failure(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "uploadAudio": {
                    "success": False,
                    "title": None,
                    "message": "File is smaller than 50kb",
                }
            }
        },
    )

    result_dict = await upload_audio.ainvoke(
        _args(audio_url="https://cdn.example.com/tiny.mp3")
    )
    result = UploadAudioOutput.model_validate(result_dict)
    assert result.success is False
    assert result.uploaded is False
    assert result.error == "File is smaller than 50kb"


@pytest.mark.asyncio
async def test_get_transcript_missing_node(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=API, json={"data": {"transcript": None}})

    result_dict = await get_transcript.ainvoke(_args(transcript_id="missing"))
    result = GetTranscriptOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "missing" in result.error


@pytest.mark.asyncio
async def test_non_200_response(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=API, status_code=503, text="upstream unavailable"
    )

    result_dict = await list_contacts.ainvoke(_args())
    result = ListContactsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "503" in result.error
    assert result.contacts == []


@pytest.mark.asyncio
async def test_non_object_body_does_not_raise(httpx_mock):  # type: ignore[no-untyped-def]
    """A 200 carrying a bare JSON array must degrade to the error envelope."""
    httpx_mock.add_response(method="POST", url=API, json=["unexpected"])

    result_dict = await list_bites.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListBitesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert result.bites == []


@pytest.mark.asyncio
async def test_wrong_typed_scalar_degrades_instead_of_raising(httpx_mock):  # type: ignore[no-untyped-def]
    """A 200 whose field has the wrong TYPE must not escape the @tool boundary.

    Model construction happens after the `except` clauses, so an upstream
    scalar arriving as the wrong type would raise `ValidationError` past the
    tool boundary rather than returning an envelope. The `_as_*` coercers
    close that path.
    """
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "transcript": {
                    "id": 12345,
                    "title": {"unexpected": "object"},
                    "date": "not-a-number",
                    "duration": "45",
                    "participants": "ada@example.com",
                    "speakers": {"not": "a list"},
                }
            }
        },
    )

    result_dict = await get_transcript.ainvoke(_args(transcript_id="tr_1"))
    assert isinstance(result_dict, dict)
    result = GetTranscriptOutput.model_validate(result_dict)
    assert result.success is True
    assert result.transcript is not None
    assert result.transcript.id == "12345"
    # A nested object in a str field, a string in a float field, and a
    # non-array in a list field all degrade rather than raise.
    assert result.transcript.title is None
    assert result.transcript.date is None
    # A numeric string is read; the schema types several numeric fields String.
    assert result.transcript.duration == 45.0
    assert result.transcript.participants == []
    assert result.transcript.speakers == []


@pytest.mark.asyncio
async def test_wrong_typed_nested_scalar_degrades(httpx_mock):  # type: ignore[no-untyped-def]
    """The same guarantee holds for nested objects and list members."""
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "transcript": {
                    "id": "tr_1",
                    "sentences": [
                        {"index": "0", "text": 42, "start_time": "12.5", "ai_filters": []}
                    ],
                    "summary": {"keywords": "release", "action_items": ["a", 7]},
                    "analytics": {
                        "categories": {"questions": "four"},
                        "speakers": [{"speaker_id": 1.0, "word_count": 3.5}],
                    },
                }
            }
        },
    )

    result_dict = await get_transcript.ainvoke(_args(transcript_id="tr_1"))
    result = GetTranscriptOutput.model_validate(result_dict)
    assert result.success is True
    assert result.transcript is not None
    sentence = result.transcript.sentences[0]
    assert sentence.index == 0
    assert sentence.text == "42"
    assert sentence.start_time == 12.5
    assert sentence.ai_filters is None
    assert result.transcript.summary is not None
    # The vendor's schema page types `keywords` String while its own reference
    # types it string[]; both shapes are accepted rather than one being
    # guessed, exactly as for the other conflicting summary fields.
    assert result.transcript.summary.keywords == "release"
    assert result.transcript.summary.action_items == ["a", "7"]
    assert result.transcript.analytics is not None
    assert result.transcript.analytics.categories is not None
    assert result.transcript.analytics.categories.questions is None
    # A whole float still reads as a count; a fractional one degrades.
    assert result.transcript.analytics.speakers[0].speaker_id == 1
    assert result.transcript.analytics.speakers[0].word_count is None


# --- Local validation (no HTTP call is made) --------------------------------


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await list_transcripts.ainvoke({"api_key": "   "})
    result = ListTranscriptsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key is empty" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_upload_audio_requires_https_url(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await upload_audio.ainvoke(
        _args(audio_url="http://cdn.example.com/call.mp3")
    )
    result = UploadAudioOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "https://" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_upload_audio_rejects_bad_attendees_json(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await upload_audio.ainvoke(
        _args(audio_url="https://cdn.example.com/call.mp3", attendees="Ada and Grace")
    )
    result = UploadAudioOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "attendees" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_add_to_live_meeting_rejects_non_http_link(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await add_to_live_meeting.ainvoke(_args(meeting_link="zoom:123"))
    result = AddToLiveMeetingOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "meeting_link" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_create_bite_rejects_inverted_time_range(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await create_bite.ainvoke(
        _args(transcript_id="tr_1", start_time=90, end_time=30)
    )
    result = CreateBiteOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "start_time" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_create_bite_rejects_unknown_media_type(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await create_bite.ainvoke(
        _args(transcript_id="tr_1", start_time=30, end_time=90, media_type="gif")
    )
    result = CreateBiteOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "media_type must be one of" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_wrong_typed_bool_degrades_instead_of_raising(httpx_mock):  # type: ignore[no-untyped-def]
    """Boolean fields get the same guarantee as the other scalars.

    ``is_admin`` and the ``ai_filters`` flags are typed ``bool | None``; pydantic
    rejects a container outright and coerces a stray string, so both must be
    routed through ``_as_bool`` before model construction.
    """
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={"data": {"user": {"user_id": "user_1", "is_admin": {"unexpected": "object"}}}},
    )

    result_dict = await get_user.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = GetUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user is not None
    assert result.user.is_admin is None

    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            "data": {
                "transcript": {
                    "id": "tr_1",
                    "sentences": [
                        {
                            "text": "hi",
                            "ai_filters": {
                                "task": [],
                                "pricing": "maybe",
                                "question": 1,
                                "sentiment": 3,
                            },
                        }
                    ],
                }
            }
        },
    )

    result_dict = await get_transcript.ainvoke(_args(transcript_id="tr_1"))
    transcript = GetTranscriptOutput.model_validate(result_dict).transcript
    assert transcript is not None
    filters = transcript.sentences[0].ai_filters
    assert filters is not None
    assert filters.task is None
    assert filters.pricing is None
    assert filters.question is None
    # A non-bool scalar still coerces on the str-typed sibling field.
    assert filters.sentiment == "3"


@pytest.mark.asyncio
async def test_upload_audio_rejects_plaintext_webhook(httpx_mock):  # type: ignore[no-untyped-def]
    """The webhook receives the finished transcript, so it must be https.

    Plain http would have the vendor POST meeting content in cleartext. The
    same bar already applies to `audio_url`; this keeps the two consistent.
    """
    result_dict = await upload_audio.ainvoke(
        _args(
            audio_url="https://cdn.example.com/call.mp3",
            webhook="http://hooks.example.com/fireflies",
        )
    )
    result = UploadAudioOutput.model_validate(result_dict)
    assert result.success is False
    assert "https" in (result.error or "")
    # Rejected locally — nothing was sent upstream.
    assert httpx_mock.get_requests() == []
