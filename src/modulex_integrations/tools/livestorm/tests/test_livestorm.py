"""Happy-path tests for every livestorm @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.livestorm import (
    TOOLS,
    create_event,
    get_event,
    list_attendees_from_event,
    list_events,
    list_sessions,
    manifest,
    register_someone_for_session,
    update_event,
)
from modulex_integrations.tools.livestorm.outputs import (
    CreateEventOutput,
    GetEventOutput,
    ListAttendeesFromEventOutput,
    ListEventsOutput,
    ListSessionsOutput,
    RegisterSomeoneForSessionOutput,
    UpdateEventOutput,
)

API = "https://api.livestorm.co/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "bearer_token",
    "auth_data": {"token": "fake_api_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity ----------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_7_actions(self) -> None:
        assert len(manifest.actions) == 7

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_bearer_token_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"bearer_token"}


# --- Per-action happy-path tests ----------------------------------------------


@pytest.mark.asyncio
async def test_create_event(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/events",
        status_code=201,
        json={
            "data": {
                "id": "evt_123",
                "type": "events",
                "attributes": {"title": "My Webinar"},
            }
        },
    )

    result_dict = await create_event.ainvoke(
        _args(owner_id="user_1", title="My Webinar")
    )

    assert isinstance(result_dict, dict)
    result = CreateEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None
    assert result.data["id"] == "evt_123"


@pytest.mark.asyncio
async def test_get_event(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/events/evt_123",
        json={
            "data": {
                "id": "evt_123",
                "type": "events",
                "attributes": {"title": "My Webinar"},
            }
        },
    )

    result_dict = await get_event.ainvoke(_args(event_id="evt_123"))

    assert isinstance(result_dict, dict)
    result = GetEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None
    assert result.data["id"] == "evt_123"


@pytest.mark.asyncio
async def test_list_attendees_from_event(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/events/evt_123/people?page%5Bnumber%5D=1",
        json={
            "data": [
                {"id": "person_1", "type": "people", "attributes": {"email": "a@b.com"}}
            ],
            "meta": {"page_count": 1},
        },
    )

    result_dict = await list_attendees_from_event.ainvoke(
        _args(event_id="evt_123")
    )

    assert isinstance(result_dict, dict)
    result = ListAttendeesFromEventOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_list_events(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/events?page%5Bnumber%5D=1",
        json={
            "data": [
                {"id": "evt_1", "type": "events", "attributes": {"title": "Event 1"}}
            ],
            "meta": {"page_count": 1},
        },
    )

    result_dict = await list_events.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListEventsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_list_sessions(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sessions?page%5Bnumber%5D=1",
        json={
            "data": [
                {"id": "ses_1", "type": "sessions", "attributes": {"status": "upcoming"}}
            ],
            "meta": {"page_count": 1},
        },
    )

    result_dict = await list_sessions.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListSessionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_register_someone_for_session(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sessions/ses_1/people",
        status_code=201,
        json={
            "data": {
                "id": "person_new",
                "type": "people",
                "attributes": {"email": "new@example.com"},
            }
        },
    )

    result_dict = await register_someone_for_session.ainvoke(
        _args(session_id="ses_1")
    )

    assert isinstance(result_dict, dict)
    result = RegisterSomeoneForSessionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None
    assert result.data["id"] == "person_new"


@pytest.mark.asyncio
async def test_update_event(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/events/evt_123",
        json={
            "data": {
                "id": "evt_123",
                "type": "events",
                "attributes": {"title": "Updated Title"},
            }
        },
    )

    result_dict = await update_event.ainvoke(
        _args(
            event_id="evt_123",
            owner_id="user_1",
            title="Updated Title",
            slug="updated-title",
            status="published",
            description="<h1>Updated</h1>",
            recording_enabled=True,
            chat_enabled=True,
            everyone_can_speak=False,
            detailed_registration_page_enabled=True,
            light_registration_page_enabled=False,
            recording_public=False,
            show_in_company_page=True,
            polls_enabled=True,
            questions_enabled=True,
        )
    )

    assert isinstance(result_dict, dict)
    result = UpdateEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None
    assert result.data["id"] == "evt_123"


# --- Failure-path test --------------------------------------------------------


@pytest.mark.asyncio
async def test_create_event_missing_credentials() -> None:
    """Empty credentials should return an error without hitting the API."""
    result_dict = await create_event.ainvoke(
        _args(owner_id="user_1", title="Test", auth_data={})
    )

    assert isinstance(result_dict, dict)
    result = CreateEventOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "token" in result.error
