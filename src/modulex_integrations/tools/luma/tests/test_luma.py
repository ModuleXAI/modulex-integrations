"""Happy-path tests for every luma @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.luma import (
    TOOLS,
    add_guests,
    create_event,
    get_event,
    get_guest,
    get_guests,
    list_events,
    list_ticket_types,
    manifest,
    send_invites,
)
from modulex_integrations.tools.luma.outputs import (
    AddGuestsOutput,
    CreateEventOutput,
    GetEventOutput,
    GetGuestOutput,
    GetGuestsOutput,
    ListEventsOutput,
    ListTicketTypesOutput,
    SendInvitesOutput,
)

API = "https://public-api.luma.com/v1"

_API_KEY = "fake-luma-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_8_actions(self) -> None:
        assert len(manifest.actions) == 8

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_event(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/event/create",
        json={
            # TODO: fill in a representative response from the Luma API
            "event": {"api_id": "evt-abc123", "name": "Test Event"},
        },
    )

    result_dict = await create_event.ainvoke(
        _args(name="Test Event", start_at="2026-06-01T18:00:00Z", timezone="America/New_York")
    )

    assert isinstance(result_dict, dict)
    result = CreateEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.event is not None


@pytest.mark.asyncio
async def test_get_event(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/event/get?id=evt-abc123",
        json={
            # TODO: fill in a representative response from the Luma API
            "event": {"api_id": "evt-abc123", "name": "Test Event"},
        },
    )

    result_dict = await get_event.ainvoke(_args(event_id="evt-abc123"))

    assert isinstance(result_dict, dict)
    result = GetEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.event is not None


@pytest.mark.asyncio
async def test_list_events(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calendar/list-events?pagination_limit=50",
        json={
            # TODO: fill in a representative response from the Luma API
            "entries": [{"event": {"api_id": "evt-1", "name": "Event 1"}}],
            "has_more": False,
            "next_cursor": None,
        },
    )

    result_dict = await list_events.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListEventsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.events) >= 1


@pytest.mark.asyncio
async def test_get_guest(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/event/get-guest?event_id=evt-abc123&id=gst-xyz",
        json={
            # TODO: fill in a representative response from the Luma API
            "guest": {"api_id": "gst-xyz", "name": "Jane Doe", "email": "jane@example.com"},
        },
    )

    result_dict = await get_guest.ainvoke(_args(event_id="evt-abc123", guest_id="gst-xyz"))

    assert isinstance(result_dict, dict)
    result = GetGuestOutput.model_validate(result_dict)
    assert result.success is True
    assert result.guest is not None


@pytest.mark.asyncio
async def test_get_guests(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/event/get-guests?event_id=evt-abc123&pagination_limit=50",
        json={
            # TODO: fill in a representative response from the Luma API
            "entries": [{"guest": {"api_id": "gst-1", "name": "John"}}],
            "has_more": False,
            "next_cursor": None,
        },
    )

    result_dict = await get_guests.ainvoke(_args(event_id="evt-abc123"))

    assert isinstance(result_dict, dict)
    result = GetGuestsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.guests) >= 1


@pytest.mark.asyncio
async def test_add_guests(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/event/add-guests",
        json={
            # TODO: fill in a representative response from the Luma API
            "guests": [{"email": "jane@example.com", "name": "Jane Doe"}],
        },
    )

    result_dict = await add_guests.ainvoke(
        _args(
            event_id="evt-abc123",
            guests_json='[{"email":"jane@example.com","name":"Jane Doe"}]',
        )
    )

    assert isinstance(result_dict, dict)
    result = AddGuestsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_ticket_types(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/event/ticket-types/list?event_id=evt-abc123",
        json={
            # TODO: fill in a representative response from the Luma API
            "ticket_types": [{"id": "tt-1", "name": "General Admission"}],
        },
    )

    result_dict = await list_ticket_types.ainvoke(_args(event_id="evt-abc123"))

    assert isinstance(result_dict, dict)
    result = ListTicketTypesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.ticket_types) >= 1


@pytest.mark.asyncio
async def test_send_invites(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/event/send-invites",
        json={},
    )

    result_dict = await send_invites.ainvoke(
        _args(
            event_id="evt-abc123",
            guests_json='[{"email":"jane@example.com","name":"Jane Doe"}]',
        )
    )

    assert isinstance(result_dict, dict)
    result = SendInvitesOutput.model_validate(result_dict)
    assert result.success is True


# --- Failure-path tests -----------------------------------------------------


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits() -> None:
    """Empty credential returns success=False without hitting the wire."""
    result_dict = await create_event.ainvoke(
        {"api_key": "", "name": "X", "start_at": "2026-06-01T00:00:00Z", "timezone": "UTC"}
    )
    assert isinstance(result_dict, dict)
    result = CreateEventOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
