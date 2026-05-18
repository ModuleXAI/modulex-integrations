"""Happy-path tests for every microsoft_bookings @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.microsoft_bookings import (
    TOOLS,
    cancel_appointment,
    create_appointment,
    create_business,
    create_customer,
    create_service,
    create_staff_member,
    list_appointments,
    list_businesses,
    list_services,
    list_staff_members,
    manifest,
)
from modulex_integrations.tools.microsoft_bookings.outputs import (
    CancelAppointmentOutput,
    CreateAppointmentOutput,
    CreateBusinessOutput,
    CreateCustomerOutput,
    CreateServiceOutput,
    CreateStaffMemberOutput,
    ListAppointmentsOutput,
    ListBusinessesOutput,
    ListServicesOutput,
    ListStaffMembersOutput,
)

API = "https://graph.microsoft.com/v1.0"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_10_actions(self) -> None:
        assert len(manifest.actions) == 10

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_list_businesses(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/solutions/bookingBusinesses",
        json={
            # TODO: fill in a representative Microsoft Graph response shape
            "value": [
                {"id": "biz-1", "displayName": "Acme Bookings", "email": "ops@acme.test"},
            ],
        },
    )

    result_dict = await list_businesses.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListBusinessesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1
    assert result.businesses[0].id == "biz-1"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"


@pytest.mark.asyncio
async def test_list_staff_members(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/solutions/bookingBusinesses/biz-1/staffMembers",
        json={
            # TODO: fill in a representative Microsoft Graph response shape
            "value": [
                {"id": "staff-1", "displayName": "Jane Doe", "role": "administrator"},
            ],
        },
    )

    result_dict = await list_staff_members.ainvoke(_args(business_id="biz-1"))

    assert isinstance(result_dict, dict)
    result = ListStaffMembersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.staff_members[0].display_name == "Jane Doe"


@pytest.mark.asyncio
async def test_list_services(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/solutions/bookingBusinesses/biz-1/services",
        json={
            # TODO: fill in a representative Microsoft Graph response shape
            "value": [
                {"id": "svc-1", "displayName": "Consultation", "defaultDuration": "PT30M"},
            ],
        },
    )

    result_dict = await list_services.ainvoke(_args(business_id="biz-1"))

    assert isinstance(result_dict, dict)
    result = ListServicesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.services[0].display_name == "Consultation"


@pytest.mark.asyncio
async def test_list_appointments(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/solutions/bookingBusinesses/biz-1/calendarView?start=2024-05-01T00%3A00%3A00Z&end=2024-05-31T23%3A59%3A59Z",
        json={
            # TODO: fill in a representative Microsoft Graph response shape
            "value": [
                {"id": "appt-1", "customerName": "John", "serviceId": "svc-1"},
            ],
        },
    )

    result_dict = await list_appointments.ainvoke(
        _args(
            business_id="biz-1",
            start_date="2024-05-01T00:00:00Z",
            end_date="2024-05-31T23:59:59Z",
        )
    )

    assert isinstance(result_dict, dict)
    result = ListAppointmentsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.appointments[0].id == "appt-1"


@pytest.mark.asyncio
async def test_create_business(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/solutions/bookingBusinesses",
        status_code=201,
        json={
            # TODO: fill in a representative Microsoft Graph response shape
            "id": "biz-new",
            "displayName": "New Biz",
        },
    )

    result_dict = await create_business.ainvoke(_args(display_name="New Biz"))

    assert isinstance(result_dict, dict)
    result = CreateBusinessOutput.model_validate(result_dict)
    assert result.success is True
    assert result.business is not None
    assert result.business.display_name == "New Biz"


@pytest.mark.asyncio
async def test_create_customer(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/solutions/bookingBusinesses/biz-1/customers",
        status_code=201,
        json={
            # TODO: fill in a representative Microsoft Graph response shape
            "id": "cust-1",
            "displayName": "John Doe",
            "emailAddress": "john@example.com",
        },
    )

    result_dict = await create_customer.ainvoke(
        _args(business_id="biz-1", display_name="John Doe", email_address="john@example.com")
    )

    assert isinstance(result_dict, dict)
    result = CreateCustomerOutput.model_validate(result_dict)
    assert result.success is True
    assert result.customer is not None
    assert result.customer.id == "cust-1"


@pytest.mark.asyncio
async def test_create_service(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/solutions/bookingBusinesses/biz-1/services",
        status_code=201,
        json={
            # TODO: fill in a representative Microsoft Graph response shape
            "id": "svc-new",
            "displayName": "Yoga Class",
        },
    )

    result_dict = await create_service.ainvoke(
        _args(business_id="biz-1", display_name="Yoga Class")
    )

    assert isinstance(result_dict, dict)
    result = CreateServiceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.service is not None
    assert result.service.display_name == "Yoga Class"


@pytest.mark.asyncio
async def test_create_staff_member(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/solutions/bookingBusinesses/biz-1/staffMembers",
        status_code=201,
        json={
            # TODO: fill in a representative Microsoft Graph response shape
            "id": "staff-new",
            "displayName": "Jane Smith",
            "emailAddress": "jane@example.com",
            "role": "scheduler",
        },
    )

    result_dict = await create_staff_member.ainvoke(
        _args(
            business_id="biz-1",
            display_name="Jane Smith",
            email_address="jane@example.com",
            role="scheduler",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateStaffMemberOutput.model_validate(result_dict)
    assert result.success is True
    assert result.staff_member is not None
    assert result.staff_member.role == "scheduler"


@pytest.mark.asyncio
async def test_create_appointment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/solutions/bookingBusinesses/biz-1/appointments",
        status_code=201,
        json={
            # TODO: fill in a representative Microsoft Graph response shape
            "id": "appt-new",
            "serviceId": "svc-1",
            "customerName": "John Doe",
        },
    )

    result_dict = await create_appointment.ainvoke(
        _args(
            business_id="biz-1",
            service_id="svc-1",
            customer_id="cust-1",
            start_date_time="2024-05-01T12:00:00",
            end_date_time="2024-05-01T13:00:00",
            time_zone="UTC",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateAppointmentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.appointment is not None
    assert result.appointment.id == "appt-new"


@pytest.mark.asyncio
async def test_cancel_appointment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/solutions/bookingBusinesses/biz-1/appointments/appt-1/cancel",
        status_code=204,
    )

    result_dict = await cancel_appointment.ainvoke(
        _args(
            business_id="biz-1",
            appointment_id="appt-1",
            cancellation_message="Sorry, we need to reschedule",
        )
    )

    assert isinstance(result_dict, dict)
    result = CancelAppointmentOutput.model_validate(result_dict)
    assert result.success is True


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_list_businesses_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/solutions/bookingBusinesses",
        status_code=401,
        text="Unauthorized",
    )

    result_dict = await list_businesses.ainvoke(_args())
    result = ListBusinessesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error
