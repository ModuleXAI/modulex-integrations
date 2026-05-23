"""Happy-path tests for every cal_com @tool, plus a manifest sanity check."""
from __future__ import annotations

import re
from typing import Any

import pytest

from modulex_integrations.tools.cal_com import (
    TOOLS,
    create_booking,
    delete_booking,
    get_all_bookings,
    get_bookable_slots,
    get_booking,
    list_event_type_id_options,
    manifest,
)
from modulex_integrations.tools.cal_com.outputs import (
    CreateBookingOutput,
    DeleteBookingOutput,
    GetAllBookingsOutput,
    GetBookableSlotsOutput,
    GetBookingOutput,
    ListEventTypeIdOptionsOutput,
)

API = "https://api.cal.com/v2"

_API_KEY = "fake-cal-api-key"


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


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_booking(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/bookings",
        json={
            # TODO: fill in a representative response shape from the Cal.com API docs
            "status": "success",
            "data": {
                "uid": "booking-uid-123",
                "title": "Test Meeting",
                "status": "accepted",
                "start": "2024-08-13T09:00:00Z",
                "end": "2024-08-13T09:30:00Z",
                "attendees": [{"name": "Test User", "email": "test@example.com"}],
                "hosts": [],
                "eventTypeId": 1,
                "meetingUrl": None,
                "location": None,
            },
        },
    )

    result_dict = await create_booking.ainvoke(
        _args(
            booking_type="booking",
            attendee_name="Test User",
            attendee_time_zone="America/New_York",
            start="2024-08-13T09:00:00Z",
            attendee_email="test@example.com",
            event_type_id=1,
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateBookingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.booking is not None
    assert result.booking.uid == "booking-uid-123"


@pytest.mark.asyncio
async def test_delete_booking(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/bookings/uid-to-cancel/cancel",
        json={
            "status": "success",
            "data": {},
        },
    )

    result_dict = await delete_booking.ainvoke(
        _args(booking_id="uid-to-cancel")
    )

    assert isinstance(result_dict, dict)
    result = DeleteBookingOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_get_all_bookings(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"^{re.escape(API)}/bookings"),
        json={
            "status": "success",
            "data": [
                {
                    "uid": "booking-1",
                    "title": "Meeting 1",
                    "status": "accepted",
                    "start": "2024-08-13T09:00:00Z",
                    "end": "2024-08-13T09:30:00Z",
                    "attendees": [],
                    "hosts": [],
                    "eventTypeId": 1,
                    "meetingUrl": None,
                    "location": None,
                }
            ],
            "hasNextPage": False,
        },
    )

    result_dict = await get_all_bookings.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetAllBookingsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1
    assert result.bookings[0].uid == "booking-1"


@pytest.mark.asyncio
async def test_get_bookable_slots(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=re.compile(rf"^{re.escape(API)}/slots"),
        json={
            "status": "success",
            "data": {
                "2024-08-13": [
                    {"time": "2024-08-13T09:00:00Z"},
                    {"time": "2024-08-13T10:00:00Z"},
                ]
            },
        },
    )

    result_dict = await get_bookable_slots.ainvoke(
        _args(start="2024-08-13T00:00:00Z", end="2024-08-14T00:00:00Z")
    )

    assert isinstance(result_dict, dict)
    result = GetBookableSlotsOutput.model_validate(result_dict)
    assert result.success is True
    assert "2024-08-13" in result.slots
    assert len(result.slots["2024-08-13"]) == 2


@pytest.mark.asyncio
async def test_get_booking(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/bookings/uid-123",
        json={
            "status": "success",
            "data": {
                "uid": "uid-123",
                "title": "Test Meeting",
                "status": "accepted",
                "start": "2024-08-13T09:00:00Z",
                "end": "2024-08-13T09:30:00Z",
                "attendees": [],
                "hosts": [],
                "eventTypeId": 1,
                "meetingUrl": None,
                "location": None,
            },
        },
    )

    result_dict = await get_booking.ainvoke(_args(booking_id="uid-123"))

    assert isinstance(result_dict, dict)
    result = GetBookingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.booking is not None
    assert result.booking.uid == "uid-123"


@pytest.mark.asyncio
async def test_list_event_type_id_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/event-types",
        json={
            "status": "success",
            "data": [
                {"id": 1, "title": "30 Minute Meeting", "slug": "30min"},
                {"id": 2, "title": "60 Minute Meeting", "slug": "60min"},
            ],
        },
    )

    result_dict = await list_event_type_id_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListEventTypeIdOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.event_types) == 2
    assert result.event_types[0].value == 1


@pytest.mark.asyncio
async def test_create_booking_validates_empty_api_key() -> None:
    result_dict = await create_booking.ainvoke(
        {
            "booking_type": "booking",
            "attendee_name": "X",
            "attendee_time_zone": "UTC",
            "start": "2024-01-01T00:00:00Z",
            "api_key": "",
        }
    )
    result = CreateBookingOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")
