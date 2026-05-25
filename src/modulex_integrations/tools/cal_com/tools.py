"""Cal.com LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.cal_com.outputs import (
    BookingItem,
    CreateBookingOutput,
    DeleteBookingOutput,
    EventTypeOption,
    GetAllBookingsOutput,
    GetBookableSlot,
    GetBookableSlotsOutput,
    GetBookingOutput,
    ListEventTypeIdOptionsOutput,
)

__all__ = [
    "create_booking",
    "delete_booking",
    "get_all_bookings",
    "get_bookable_slots",
    "get_booking",
    "list_event_type_id_options",
]

_BASE_URL = "https://api.cal.com/v2"
_TIMEOUT = 30.0


def _headers(api_key: str, api_version: str = "2026-02-25") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "cal-api-version": api_version,
    }


def _parse_booking(data: dict[str, Any]) -> BookingItem:
    return BookingItem(
        uid=data.get("uid"),
        title=data.get("title"),
        status=data.get("status"),
        start=data.get("start"),
        end=data.get("end"),
        attendees=data.get("attendees") or [],
        hosts=data.get("hosts") or [],
        event_type_id=data.get("eventTypeId"),
        meeting_url=data.get("meetingUrl"),
        location=data.get("location"),
    )


# --- Input schemas --------------------------------------------------------


class CreateBookingInput(BaseModel):
    booking_type: str = Field(description="Type of booking: booking, instant, or recurring")
    attendee_name: str = Field(description="Full name of the attendee")
    attendee_time_zone: str = Field(description="Time zone of the attendee, e.g. America/New_York")
    start: str = Field(description="Booking start time in ISO 8601 UTC format, e.g. 2024-08-13T09:00:00Z")
    api_key: str = Field(description="Cal.com API key")
    attendee_email: str | None = Field(default=None, description="Email address of the attendee")
    attendee_phone_number: str | None = Field(default=None, description="Phone number in international format")
    attendee_language: str | None = Field(default=None, description="Language for the booking confirmation")
    event_type_id: int | None = Field(default=None, description="ID of the event type")
    event_type_slug: str | None = Field(default=None, description="Slug of the event type")
    username: str | None = Field(default=None, description="Username of the individual event owner")
    team_slug: str | None = Field(default=None, description="Team slug for team event type")
    organization_slug: str | None = Field(default=None, description="Organization slug")
    end_time: str | None = Field(default=None, description="Booking end time in ISO 8601 format")
    length_in_minutes: int | None = Field(default=None, description="Override event type duration in minutes")
    guests: list[str] | None = Field(default=None, description="Additional guest email addresses")
    location: str | None = Field(default=None, description="Meeting location type")
    location_address: str | None = Field(default=None, description="Physical address if location is attendeeAddress")
    location_value: str | None = Field(default=None, description="Location string if location is attendeeDefined")
    location_phone: str | None = Field(default=None, description="Phone number if location is attendeePhone")
    location_integration: str | None = Field(default=None, description="Video conferencing integration")
    recurrence_count: int | None = Field(default=None, description="Number of occurrences for recurring booking")
    metadata: dict[str, Any] | None = Field(default=None, description="Custom key-value metadata")
    booking_fields_responses: dict[str, Any] | None = Field(default=None, description="Responses to custom booking form fields")
    allow_conflicts: bool | None = Field(default=None, description="Bypass availability checks")
    allow_booking_out_of_bounds: bool | None = Field(default=None, description="Allow booking outside scheduling window")
    email_verification_code: str | None = Field(default=None, description="Email verification code if required")


class DeleteBookingInput(BaseModel):
    booking_id: str = Field(description="The UID of the booking to cancel")
    api_key: str = Field(description="Cal.com API key")
    cancellation_reason: str | None = Field(default=None, description="Reason for cancelling the booking")
    cancel_subsequent_bookings: bool | None = Field(default=None, description="Cancel all subsequent recurring occurrences")


class GetAllBookingsInput(BaseModel):
    api_key: str = Field(description="Cal.com API key")
    max_pages: int = Field(default=50, description="Maximum number of pages to fetch (1-500)", ge=1, le=500)
    status: list[str] | None = Field(default=None, description="Filter by status: upcoming, recurring, past, cancelled, unconfirmed")
    after_start: str | None = Field(default=None, description="Return bookings that start after this time (ISO 8601)")
    before_end: str | None = Field(default=None, description="Return bookings that end before this time (ISO 8601)")
    after_created_at: str | None = Field(default=None, description="Return bookings created after this time (ISO 8601)")
    before_created_at: str | None = Field(default=None, description="Return bookings created before this time (ISO 8601)")
    attendee_email: str | None = Field(default=None, description="Filter by attendee email")
    attendee_name: str | None = Field(default=None, description="Filter by attendee name")
    booking_uid: str | None = Field(default=None, description="Filter by booking UID")
    event_type_id: int | None = Field(default=None, description="Filter by event type ID")
    sort_start: str | None = Field(default=None, description="Sort by start time: asc or desc")
    sort_end: str | None = Field(default=None, description="Sort by end time: asc or desc")
    sort_created: str | None = Field(default=None, description="Sort by creation time: asc or desc")


class GetBookableSlotsInput(BaseModel):
    start: str = Field(description="Start date/time in ISO 8601 format (UTC)")
    end: str = Field(description="End date/time in ISO 8601 format (UTC)")
    api_key: str = Field(description="Cal.com API key")
    event_type_id: int | None = Field(default=None, description="ID of the event type to get slots for")
    event_type_slug: str | None = Field(default=None, description="Slug of the event type")
    username: str | None = Field(default=None, description="Username of the individual event owner")
    usernames: list[str] | None = Field(default=None, description="List of usernames for a dynamic event")
    team_slug: str | None = Field(default=None, description="Team slug for team event type slot lookup")
    organization_slug: str | None = Field(default=None, description="Organization slug")
    time_zone: str | None = Field(default=None, description="Time zone for the slot lookup")
    duration: int | None = Field(default=None, description="Override default slot duration in minutes")
    format: str | None = Field(default=None, description="Response format: range or time")
    booking_uid_to_reschedule: str | None = Field(default=None, description="UID of booking being rescheduled")


class GetBookingInput(BaseModel):
    booking_id: str = Field(description="The UID of the booking to retrieve")
    api_key: str = Field(description="Cal.com API key")


class ListEventTypeIdOptionsInput(BaseModel):
    api_key: str = Field(description="Cal.com API key")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateBookingInput)
@serialize_pydantic_return
async def create_booking(
    booking_type: str,
    attendee_name: str,
    attendee_time_zone: str,
    start: str,
    api_key: str,
    attendee_email: str | None = None,
    attendee_phone_number: str | None = None,
    attendee_language: str | None = None,
    event_type_id: int | None = None,
    event_type_slug: str | None = None,
    username: str | None = None,
    team_slug: str | None = None,
    organization_slug: str | None = None,
    end_time: str | None = None,
    length_in_minutes: int | None = None,
    guests: list[str] | None = None,
    location: str | None = None,
    location_address: str | None = None,
    location_value: str | None = None,
    location_phone: str | None = None,
    location_integration: str | None = None,
    recurrence_count: int | None = None,
    metadata: dict[str, Any] | None = None,
    booking_fields_responses: dict[str, Any] | None = None,
    allow_conflicts: bool | None = None,
    allow_booking_out_of_bounds: bool | None = None,
    email_verification_code: str | None = None,
) -> CreateBookingOutput:
    """Create a new booking on Cal.com."""
    if not api_key or not api_key.strip():
        return CreateBookingOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    attendee: dict[str, Any] = {
        "name": attendee_name,
        "timeZone": attendee_time_zone,
    }
    if attendee_email:
        attendee["email"] = attendee_email
    if attendee_phone_number:
        attendee["phoneNumber"] = attendee_phone_number
    if attendee_language:
        attendee["language"] = attendee_language

    body: dict[str, Any] = {
        "start": start,
        "attendee": attendee,
    }

    if event_type_id is not None:
        body["eventTypeId"] = event_type_id
    if event_type_slug:
        body["eventTypeSlug"] = event_type_slug
    if username:
        body["username"] = username
    if team_slug:
        body["teamSlug"] = team_slug
    if organization_slug:
        body["organizationSlug"] = organization_slug
    if end_time:
        body["end"] = end_time
    if length_in_minutes is not None:
        body["lengthInMinutes"] = length_in_minutes
    if guests:
        body["guests"] = guests
    if metadata:
        body["metadata"] = metadata
    if booking_fields_responses:
        body["bookingFieldsResponses"] = booking_fields_responses
    if allow_conflicts is not None:
        body["allowConflicts"] = allow_conflicts
    if allow_booking_out_of_bounds is not None:
        body["allowBookingOutOfBounds"] = allow_booking_out_of_bounds
    if email_verification_code:
        body["emailVerificationCode"] = email_verification_code
    if recurrence_count is not None:
        body["recurrenceCount"] = recurrence_count

    if location:
        loc: dict[str, Any] = {"type": location}
        if location == "attendeeAddress" and location_address:
            loc["address"] = location_address
        elif location == "attendeeDefined" and location_value:
            loc["value"] = location_value
        elif location == "attendeePhone" and location_phone:
            loc["phone"] = location_phone
        elif location == "integration" and location_integration:
            loc["integration"] = location_integration
        body["location"] = loc

    endpoint = f"{_BASE_URL}/bookings"
    if booking_type == "instant":
        endpoint = f"{_BASE_URL}/bookings/instant"
    elif booking_type == "recurring":
        endpoint = f"{_BASE_URL}/bookings/recurring"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                endpoint,
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateBookingOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateBookingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateBookingOutput(success=False, error=f"Call failed: {exc}")

    booking_data = data.get("data", data)
    booking = _parse_booking(booking_data) if isinstance(booking_data, dict) else None
    return CreateBookingOutput(
        success=True,
        status=data.get("status"),
        booking=booking,
    )


@tool(args_schema=DeleteBookingInput)
@serialize_pydantic_return
async def delete_booking(
    booking_id: str,
    api_key: str,
    cancellation_reason: str | None = None,
    cancel_subsequent_bookings: bool | None = None,
) -> DeleteBookingOutput:
    """Cancel an existing booking by its UID."""
    if not api_key or not api_key.strip():
        return DeleteBookingOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    body: dict[str, Any] = {}
    if cancellation_reason:
        body["cancellationReason"] = cancellation_reason
    if cancel_subsequent_bookings is not None:
        body["cancelSubsequentBookings"] = cancel_subsequent_bookings

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/bookings/{booking_id}/cancel",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return DeleteBookingOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return DeleteBookingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteBookingOutput(success=False, error=f"Call failed: {exc}")

    return DeleteBookingOutput(
        success=True,
        status=data.get("status"),
    )


@tool(args_schema=GetAllBookingsInput)
@serialize_pydantic_return
async def get_all_bookings(
    api_key: str,
    max_pages: int = 50,
    status: list[str] | None = None,
    after_start: str | None = None,
    before_end: str | None = None,
    after_created_at: str | None = None,
    before_created_at: str | None = None,
    attendee_email: str | None = None,
    attendee_name: str | None = None,
    booking_uid: str | None = None,
    event_type_id: int | None = None,
    sort_start: str | None = None,
    sort_end: str | None = None,
    sort_created: str | None = None,
) -> GetAllBookingsOutput:
    """Retrieve all bookings from Cal.com with optional filters."""
    if not api_key or not api_key.strip():
        return GetAllBookingsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    params: dict[str, Any] = {"take": 100}
    if status:
        params["status"] = status
    if after_start:
        params["afterStart"] = after_start
    if before_end:
        params["beforeEnd"] = before_end
    if after_created_at:
        params["afterCreatedAt"] = after_created_at
    if before_created_at:
        params["beforeCreatedAt"] = before_created_at
    if attendee_email:
        params["attendeeEmail"] = attendee_email
    if attendee_name:
        params["attendeeName"] = attendee_name
    if booking_uid:
        params["bookingUid"] = booking_uid
    if event_type_id is not None:
        params["eventTypeId"] = event_type_id
    if sort_start:
        params["sortStart"] = sort_start
    if sort_end:
        params["sortEnd"] = sort_end
    if sort_created:
        params["sortCreated"] = sort_created

    all_bookings: list[BookingItem] = []
    skip = 0
    pages_seen = 0

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while pages_seen < max_pages:
                pages_seen += 1
                params["skip"] = skip
                response = await client.get(
                    f"{_BASE_URL}/bookings",
                    headers=_headers(api_key),
                    params=params,
                )
                if response.status_code != 200:
                    return GetAllBookingsOutput(
                        success=False,
                        error=f"API error ({response.status_code}): {response.text}",
                    )
                data = response.json()
                items = data.get("data", [])
                for item in items:
                    all_bookings.append(_parse_booking(item))
                if not data.get("hasNextPage", False):
                    break
                skip += len(items)
    except httpx.TimeoutException:
        return GetAllBookingsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetAllBookingsOutput(success=False, error=f"Call failed: {exc}")

    return GetAllBookingsOutput(
        success=True,
        bookings=all_bookings,
        total=len(all_bookings),
    )


@tool(args_schema=GetBookableSlotsInput)
@serialize_pydantic_return
async def get_bookable_slots(
    start: str,
    end: str,
    api_key: str,
    event_type_id: int | None = None,
    event_type_slug: str | None = None,
    username: str | None = None,
    usernames: list[str] | None = None,
    team_slug: str | None = None,
    organization_slug: str | None = None,
    time_zone: str | None = None,
    duration: int | None = None,
    format: str | None = None,
    booking_uid_to_reschedule: str | None = None,
) -> GetBookableSlotsOutput:
    """Retrieve available bookable slots between a datetime range."""
    if not api_key or not api_key.strip():
        return GetBookableSlotsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    params: dict[str, Any] = {"start": start, "end": end}
    if event_type_id is not None:
        params["eventTypeId"] = event_type_id
    if event_type_slug:
        params["eventTypeSlug"] = event_type_slug
    if username:
        params["username"] = username
    if usernames:
        params["usernames"] = ",".join(usernames)
    if team_slug:
        params["teamSlug"] = team_slug
    if organization_slug:
        params["organizationSlug"] = organization_slug
    if time_zone:
        params["timeZone"] = time_zone
    if duration is not None:
        params["duration"] = duration
    if format:
        params["format"] = format
    if booking_uid_to_reschedule:
        params["bookingUidToReschedule"] = booking_uid_to_reschedule

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/slots",
                headers=_headers(api_key, api_version="2024-09-04"),
                params=params,
            )
        if response.status_code != 200:
            return GetBookableSlotsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetBookableSlotsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetBookableSlotsOutput(success=False, error=f"Call failed: {exc}")

    raw_slots = data.get("data", {})
    slots: dict[str, list[GetBookableSlot]] = {}
    for date_key, slot_list in raw_slots.items():
        slots[date_key] = [
            GetBookableSlot(
                time=s.get("time"),
                start=s.get("start"),
                end=s.get("end"),
            )
            for s in slot_list
        ]

    return GetBookableSlotsOutput(success=True, slots=slots)


@tool(args_schema=GetBookingInput)
@serialize_pydantic_return
async def get_booking(
    booking_id: str,
    api_key: str,
) -> GetBookingOutput:
    """Retrieve a booking by its UID."""
    if not api_key or not api_key.strip():
        return GetBookingOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/bookings/{booking_id}",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return GetBookingOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetBookingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetBookingOutput(success=False, error=f"Call failed: {exc}")

    booking_data = data.get("data", data)
    booking = _parse_booking(booking_data) if isinstance(booking_data, dict) else None
    return GetBookingOutput(
        success=True,
        status=data.get("status"),
        booking=booking,
    )


@tool(args_schema=ListEventTypeIdOptionsInput)
@serialize_pydantic_return
async def list_event_type_id_options(
    api_key: str,
) -> ListEventTypeIdOptionsOutput:
    """Retrieve available event types with their IDs."""
    if not api_key or not api_key.strip():
        return ListEventTypeIdOptionsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/event-types",
                headers=_headers(api_key, api_version="2024-06-14"),
            )
        if response.status_code != 200:
            return ListEventTypeIdOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListEventTypeIdOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListEventTypeIdOptionsOutput(success=False, error=f"Call failed: {exc}")

    event_types_data = data.get("data", [])
    event_types = [
        EventTypeOption(
            label=et.get("title") or et.get("slug", ""),
            value=et.get("id"),
        )
        for et in event_types_data
        if isinstance(et, dict)
    ]

    return ListEventTypeIdOptionsOutput(success=True, event_types=event_types)
