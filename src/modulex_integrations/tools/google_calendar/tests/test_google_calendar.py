"""Happy-path tests for every google_calendar @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_calendar import (
    TOOLS,
    add_attendees_to_event,
    create_event,
    delete_event,
    get_calendar,
    get_current_user,
    get_date_time,
    get_event,
    list_calendars,
    list_color_id_options,
    list_event_instances,
    list_events,
    manifest,
    query_free_busy_calendars,
    quick_add_event,
    update_event,
    update_event_instance,
    update_following_instances,
)
from modulex_integrations.tools.google_calendar.outputs import (
    AddAttendeesToEventOutput,
    CreateEventOutput,
    DeleteEventOutput,
    GetCalendarOutput,
    GetCurrentUserOutput,
    GetDateTimeOutput,
    GetEventOutput,
    ListCalendarsOutput,
    ListColorIdOptionsOutput,
    ListEventInstancesOutput,
    ListEventsOutput,
    QueryFreeBusyCalendarsOutput,
    QuickAddEventOutput,
    UpdateEventInstanceOutput,
    UpdateEventOutput,
    UpdateFollowingInstancesOutput,
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
    def test_manifest_exposes_16_actions(self) -> None:
        assert len(manifest.actions) == 16

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_add_attendees_to_event(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    existing_event = {
        "id": "evt_1",
        "summary": "Standup",
        "attendees": [{"email": "alice@example.com"}],
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calendars/primary/events/evt_1",
        json=existing_event,
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/calendars/primary/events/evt_1",
        json={
            **existing_event,
            "attendees": [
                {"email": "bob@example.com"},
                {"email": "alice@example.com"},
            ],
        },
    )

    result_dict = await add_attendees_to_event.ainvoke(
        _args(event_id="evt_1", attendees=["bob@example.com"]),
    )

    assert isinstance(result_dict, dict)
    result = AddAttendeesToEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.event is not None
    assert any(a.get("email") == "bob@example.com" for a in (result.event.attendees or []))


@pytest.mark.asyncio
async def test_create_event(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/calendars/primary/events",
        json={
            "id": "evt_new",
            "summary": "Lunch",
            "start": {"dateTime": "2025-01-15T12:00:00-05:00"},
            "end": {"dateTime": "2025-01-15T13:00:00-05:00"},
        },
    )

    result_dict = await create_event.ainvoke(
        _args(
            summary="Lunch",
            event_start_date="2025-01-15T12:00:00-05:00",
            event_end_date="2025-01-15T13:00:00-05:00",
        ),
    )

    assert isinstance(result_dict, dict)
    result = CreateEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.event is not None
    assert result.event.id == "evt_new"


@pytest.mark.asyncio
async def test_delete_event(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/calendars/primary/events/evt_x",
        status_code=204,
    )

    result_dict = await delete_event.ainvoke(_args(event_id="evt_x"))

    assert isinstance(result_dict, dict)
    result = DeleteEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.eventId == "evt_x"


@pytest.mark.asyncio
async def test_get_calendar(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calendars/primary",
        json={
            "id": "primary",
            "summary": "Primary",
            "timeZone": "America/New_York",
        },
    )

    result_dict = await get_calendar.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetCalendarOutput.model_validate(result_dict)
    assert result.success is True
    assert result.calendar is not None
    assert result.calendar.timeZone == "America/New_York"


@pytest.mark.asyncio
async def test_get_current_user(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calendars/primary",
        json={"id": "primary", "summary": "Primary", "timeZone": "America/New_York"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me/calendarList?maxResults=25",
        json={"items": [{"id": "primary", "summary": "Primary"}]},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me/settings",
        json={"items": [{"id": "timezone", "value": "America/New_York"}, {"id": "locale", "value": "en"}]},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/colors",
        json={"event": {"1": {"background": "#ac725e", "foreground": "#1d1d1d"}}},
    )

    result_dict = await get_current_user.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetCurrentUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.timezone == "America/New_York"
    assert result.locale == "en"


@pytest.mark.asyncio
async def test_get_date_time() -> None:
    result_dict = await get_date_time.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetDateTimeOutput.model_validate(result_dict)
    assert result.success is True
    assert result.date is not None
    assert result.rfc3339 is not None


@pytest.mark.asyncio
async def test_get_event(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calendars/primary/events/evt_2",
        json={"id": "evt_2", "summary": "Sync"},
    )

    result_dict = await get_event.ainvoke(_args(event_id="evt_2"))

    assert isinstance(result_dict, dict)
    result = GetEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.event is not None
    assert result.event.id == "evt_2"


@pytest.mark.asyncio
async def test_list_calendars(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me/calendarList",
        json={
            "items": [
                {"id": "primary", "summary": "Primary"},
                {"id": "work@example.com", "summary": "Work"},
            ],
        },
    )

    result_dict = await list_calendars.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListCalendarsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.calendars) == 2


@pytest.mark.asyncio
async def test_list_color_id_options(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/colors",
        json={
            "event": {
                "1": {"background": "#ac725e", "foreground": "#1d1d1d"},
                "2": {"background": "#d06b64", "foreground": "#1d1d1d"},
            },
        },
    )

    result_dict = await list_color_id_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListColorIdOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.options) == 2


@pytest.mark.asyncio
async def test_list_event_instances(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calendars/primary/events/rec_1/instances",
        json={
            "items": [
                {"id": "rec_1_20250101T120000Z"},
                {"id": "rec_1_20250108T120000Z"},
            ],
        },
    )

    result_dict = await list_event_instances.ainvoke(_args(event_id="rec_1"))

    assert isinstance(result_dict, dict)
    result = ListEventInstancesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.instances) == 2


@pytest.mark.asyncio
async def test_list_events(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calendars/primary/events",
        json={
            "items": [
                {"id": "evt_a", "summary": "A"},
                {"id": "evt_b"},
            ],
        },
    )

    result_dict = await list_events.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListEventsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.events) == 2
    assert result.events[1].summary == "Event ID: evt_b"


@pytest.mark.asyncio
async def test_query_free_busy_calendars(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/freeBusy",
        json={
            "timeMin": "2025-01-15T00:00:00Z",
            "timeMax": "2025-01-15T23:59:59Z",
            "calendars": {
                "primary": {
                    "busy": [
                        {"start": "2025-01-15T12:00:00Z", "end": "2025-01-15T13:00:00Z"},
                    ],
                },
            },
        },
    )

    result_dict = await query_free_busy_calendars.ainvoke(
        _args(
            time_min="2025-01-15T00:00:00Z",
            time_max="2025-01-15T23:59:59Z",
        ),
    )

    assert isinstance(result_dict, dict)
    result = QueryFreeBusyCalendarsOutput.model_validate(result_dict)
    assert result.success is True
    assert "primary" in result.calendars
    assert len(result.calendars["primary"].busy) == 1


@pytest.mark.asyncio
async def test_quick_add_event(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/calendars/primary/events/quickAdd?text=Lunch+at+noon",
        json={"id": "evt_q", "summary": "Lunch at noon"},
    )

    result_dict = await quick_add_event.ainvoke(_args(text="Lunch at noon"))

    assert isinstance(result_dict, dict)
    result = QuickAddEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.event is not None
    assert result.event.id == "evt_q"


@pytest.mark.asyncio
async def test_update_event(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calendars/primary/events/evt_u",
        json={
            "id": "evt_u",
            "summary": "Old",
            "start": {"dateTime": "2025-01-15T10:00:00-05:00", "timeZone": "America/New_York"},
            "end": {"dateTime": "2025-01-15T11:00:00-05:00", "timeZone": "America/New_York"},
        },
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/calendars/primary/events/evt_u",
        json={
            "id": "evt_u",
            "summary": "New",
            "start": {"dateTime": "2025-01-15T10:00:00-05:00", "timeZone": "America/New_York"},
            "end": {"dateTime": "2025-01-15T11:00:00-05:00", "timeZone": "America/New_York"},
        },
    )

    result_dict = await update_event.ainvoke(
        _args(event_id="evt_u", summary="New"),
    )

    assert isinstance(result_dict, dict)
    result = UpdateEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.event is not None
    assert result.event.summary == "New"


@pytest.mark.asyncio
async def test_update_event_instance(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    instance = {
        "id": "rec_1_20250108T120000Z",
        "summary": "Old",
        "start": {"dateTime": "2025-01-08T12:00:00Z", "timeZone": "UTC"},
        "end": {"dateTime": "2025-01-08T13:00:00Z", "timeZone": "UTC"},
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calendars/primary/events/{instance['id']}",
        json=instance,
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/calendars/primary/events/{instance['id']}",
        json={**instance, "summary": "New"},
    )

    result_dict = await update_event_instance.ainvoke(
        _args(instance_id=instance["id"], summary="New"),
    )

    assert isinstance(result_dict, dict)
    result = UpdateEventInstanceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.event is not None
    assert result.event.summary == "New"


@pytest.mark.asyncio
async def test_update_following_instances(httpx_mock):  # type: ignore[no-untyped-def]
    # TODO: fill in a representative response shape from the upstream API docs
    recurring_event = {
        "id": "rec_1",
        "summary": "Old",
        "recurrence": ["RRULE:FREQ=WEEKLY;COUNT=10"],
    }
    target_instance = {
        "id": "rec_1_20250108T120000Z",
        "summary": "Old",
        "start": {"dateTime": "2025-01-08T12:00:00Z", "timeZone": "UTC"},
        "end": {"dateTime": "2025-01-08T13:00:00Z", "timeZone": "UTC"},
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calendars/primary/events/rec_1",
        json=recurring_event,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calendars/primary/events/{target_instance['id']}",
        json=target_instance,
    )
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/calendars/primary/events/{target_instance['id']}",
        status_code=204,
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/calendars/primary/events/rec_1",
        json={**recurring_event, "recurrence": ["RRULE:FREQ=WEEKLY;UNTIL=20250108T115959Z"]},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/calendars/primary/events",
        json={"id": "rec_2", "summary": "New"},
    )

    result_dict = await update_following_instances.ainvoke(
        _args(
            recurring_event_id="rec_1",
            instance_id=target_instance["id"],
            summary="New",
        ),
    )

    assert isinstance(result_dict, dict)
    result = UpdateFollowingInstancesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.newEvent is not None
    assert result.newEvent.id == "rec_2"
