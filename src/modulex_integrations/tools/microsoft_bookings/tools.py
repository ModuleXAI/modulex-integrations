"""Microsoft Bookings LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.microsoft_bookings.outputs import (
    AppointmentSummary,
    BusinessSummary,
    CancelAppointmentOutput,
    CreateAppointmentOutput,
    CreateBusinessOutput,
    CreateCustomerOutput,
    CreateServiceOutput,
    CreateStaffMemberOutput,
    CustomerSummary,
    ListAppointmentsOutput,
    ListBusinessesOutput,
    ListServicesOutput,
    ListStaffMembersOutput,
    ServiceSummary,
    StaffMemberSummary,
)

__all__ = [
    "cancel_appointment",
    "create_appointment",
    "create_business",
    "create_customer",
    "create_service",
    "create_staff_member",
    "list_appointments",
    "list_businesses",
    "list_services",
    "list_staff_members",
]

_BASE_URL = "https://graph.microsoft.com/v1.0"
_TIMEOUT = 30.0


# --- Helpers --------------------------------------------------------------


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build Microsoft Graph headers from the resolved credential."""
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if auth_type == "oauth2":
        token = auth_data.get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


def _appointment(item: dict[str, Any]) -> AppointmentSummary:
    return AppointmentSummary(
        id=item.get("id"),
        self_service_appointment_id=item.get("selfServiceAppointmentId"),
        service_id=item.get("serviceId"),
        service_name=item.get("serviceName"),
        customer_name=item.get("customerName"),
        customer_email_address=item.get("customerEmailAddress"),
        customer_time_zone=item.get("customerTimeZone"),
        start_date_time=item.get("startDateTime"),
        end_date_time=item.get("endDateTime"),
        duration=item.get("duration"),
        price=item.get("price"),
        price_type=item.get("priceType"),
        is_location_online=item.get("isLocationOnline"),
        join_web_url=item.get("joinWebUrl"),
        sms_notifications_enabled=item.get("smsNotificationsEnabled"),
        staff_member_ids=list(item.get("staffMemberIds") or []),
        customers=list(item.get("customers") or []),
    )


def _business(item: dict[str, Any]) -> BusinessSummary:
    return BusinessSummary(
        id=item.get("id"),
        display_name=item.get("displayName"),
        email=item.get("email"),
        phone=item.get("phone"),
        web_site_url=item.get("webSiteUrl"),
        default_currency_iso=item.get("defaultCurrencyIso"),
        business_type=item.get("businessType"),
        address=item.get("address"),
        is_published=item.get("isPublished"),
        public_url=item.get("publicUrl"),
    )


def _customer(item: dict[str, Any]) -> CustomerSummary:
    return CustomerSummary(
        id=item.get("id"),
        display_name=item.get("displayName"),
        email_address=item.get("emailAddress"),
        phones=list(item.get("phones") or []),
        addresses=list(item.get("addresses") or []),
    )


def _service(item: dict[str, Any]) -> ServiceSummary:
    return ServiceSummary(
        id=item.get("id"),
        display_name=item.get("displayName"),
        description=item.get("description"),
        default_duration=item.get("defaultDuration"),
        default_price=item.get("defaultPrice"),
        default_price_type=item.get("defaultPriceType"),
        is_location_online=item.get("isLocationOnline"),
        is_hidden_from_customers=item.get("isHiddenFromCustomers"),
        notes=item.get("notes"),
        staff_member_ids=list(item.get("staffMemberIds") or []),
        sms_notifications_enabled=item.get("smsNotificationsEnabled"),
    )


def _staff_member(item: dict[str, Any]) -> StaffMemberSummary:
    return StaffMemberSummary(
        id=item.get("id"),
        display_name=item.get("displayName"),
        email_address=item.get("emailAddress"),
        role=item.get("role"),
        time_zone=item.get("timeZone"),
        use_business_hours=item.get("useBusinessHours"),
        is_email_notification_enabled=item.get("isEmailNotificationEnabled"),
        availability_is_affected_by_personal_calendar=item.get(
            "availabilityIsAffectedByPersonalCalendar"
        ),
    )


# --- Input schemas --------------------------------------------------------


class CancelAppointmentInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing the OAuth access token")
    business_id: str = Field(description="ID of the Microsoft Bookings business that owns the appointment")
    appointment_id: str = Field(description="ID of the appointment to cancel")
    cancellation_message: str = Field(
        description="Message sent to the customer and staff members explaining the cancellation"
    )


class CreateAppointmentInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing the OAuth access token")
    business_id: str = Field(description="ID of the Microsoft Bookings business that will own the appointment")
    service_id: str = Field(description="ID of the booking service the customer is booking")
    customer_id: str = Field(description="ID of the existing customer the appointment is being booked for")
    start_date_time: str = Field(description="Appointment start time in ISO 8601 format")
    end_date_time: str = Field(description="Appointment end time in ISO 8601 format")
    time_zone: str = Field(description="IANA time zone for the appointment (e.g. UTC, America/Chicago)")
    customer_name: str | None = Field(default=None, description="Display name to record for the customer")
    customer_email_address: str | None = Field(
        default=None, description="SMTP email address for the customer"
    )
    customer_time_zone: str | None = Field(
        default=None, description="IANA time zone for the customer (falls back to time_zone if omitted)"
    )
    customer_phone: str | None = Field(default=None, description="Phone number for the customer")
    customer_notes: str | None = Field(
        default=None, description="Notes from the customer associated with this appointment"
    )
    is_location_online: bool | None = Field(
        default=None, description="True indicates that the appointment will be held online"
    )
    staff_member_ids: list[str] | None = Field(
        default=None, description="List of staff member IDs assigned to this appointment"
    )
    sms_notifications_enabled: bool | None = Field(
        default=None, description="If True, send SMS notifications to the customer for the appointment"
    )
    price: float | None = Field(default=None, description="Regular monetary price for the appointment")
    price_type: str | None = Field(
        default=None,
        description="Pricing structure: undefined, fixedPrice, startingAt, hourly, free, priceVaries, callUs, notSet",
    )
    duration: str | None = Field(
        default=None, description="Appointment length in ISO 8601 duration (e.g. PT1H, PT30M)"
    )
    maximum_attendees_count: int | None = Field(
        default=None, description="Maximum number of customers allowed in this appointment"
    )
    pre_buffer: str | None = Field(
        default=None, description="Time to reserve before the appointment in ISO 8601 duration"
    )
    post_buffer: str | None = Field(
        default=None, description="Time to reserve after the appointment in ISO 8601 duration"
    )
    service_notes: str | None = Field(
        default=None, description="Notes from the staff member about this appointment"
    )
    additional_information: str | None = Field(
        default=None,
        description="Additional information sent to the customer when the appointment is confirmed",
    )
    is_customer_allowed_to_manage_booking: bool | None = Field(
        default=None,
        description="True allows the customer to manage bookings created by the staff",
    )
    opt_out_of_customer_email: bool | None = Field(
        default=None,
        description="If True, the customer will not receive an email confirmation",
    )


class CreateBusinessInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing the OAuth access token")
    display_name: str = Field(description="Customer-facing name of the booking business")
    email: str | None = Field(default=None, description="Email address for the business")
    phone: str | None = Field(default=None, description="Telephone number for the business")
    web_site_url: str | None = Field(default=None, description="URL of the business web site")
    street: str | None = Field(default=None, description="Street address of the business")
    city: str | None = Field(default=None, description="City of the business")
    state: str | None = Field(default=None, description="State of the business")
    postal_code: str | None = Field(default=None, description="Postal code of the business")
    country_or_region: str | None = Field(default=None, description="Country or region of the business")
    default_currency_iso: str | None = Field(
        default=None, description="ISO currency code the business operates in (e.g. USD)"
    )
    business_type: str | None = Field(default=None, description="Free-form description of the type of business")


class CreateCustomerInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing the OAuth access token")
    business_id: str = Field(description="ID of the Microsoft Bookings business that will own the customer")
    display_name: str = Field(description="Customer's full name")
    email_address: str = Field(description="Customer's email address")
    phone_number: str | None = Field(default=None, description="Customer's phone number")
    phone_type: str = Field(default="home", description="Type of phone number: home, business, mobile")
    street: str | None = Field(default=None, description="Street address for the customer")
    city: str | None = Field(default=None, description="City for the customer")
    state: str | None = Field(default=None, description="State for the customer")
    postal_code: str | None = Field(default=None, description="Postal code for the customer")
    country_or_region: str | None = Field(default=None, description="Country or region for the customer")


class CreateServiceInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing the OAuth access token")
    business_id: str = Field(description="ID of the Microsoft Bookings business that will own the service")
    display_name: str = Field(description="Customer-facing name of the service")
    default_duration: str | None = Field(
        default=None, description="Default service length in ISO 8601 duration (e.g. PT1H30M)"
    )
    description: str | None = Field(default=None, description="Free-form description for the service")
    default_price: float | None = Field(default=None, description="Default monetary price for the service")
    default_price_type: str | None = Field(
        default=None,
        description="Default pricing structure: undefined, fixedPrice, startingAt, hourly, free, priceVaries, callUs, notSet",
    )
    is_location_online: bool | None = Field(
        default=None, description="True indicates the service will be held online"
    )
    staff_member_ids: list[str] | None = Field(
        default=None, description="List of staff member IDs allowed to provide this service"
    )
    is_hidden_from_customers: bool | None = Field(
        default=None, description="True hides this service from the customer-facing booking page"
    )
    notes: str | None = Field(default=None, description="Additional staff-facing notes about this service")
    sms_notifications_enabled: bool | None = Field(
        default=None, description="True enables SMS notifications to customers for this service"
    )


class CreateStaffMemberInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing the OAuth access token")
    business_id: str = Field(description="ID of the Microsoft Bookings business that will own the staff member")
    display_name: str = Field(description="Staff member's name as shown to customers")
    email_address: str = Field(description="Staff member's email address")
    role: str = Field(
        description="Staff member's role: guest, administrator, viewer, externalGuest, scheduler, teamMember"
    )
    time_zone: str | None = Field(
        default=None, description="IANA time zone for the staff member (e.g. America/Chicago)"
    )
    use_business_hours: bool | None = Field(
        default=None,
        description="True means the staff member follows the business' default hours; False uses workingHours",
    )
    is_email_notification_enabled: bool | None = Field(
        default=None, description="True to send email notifications to this staff member"
    )


class ListAppointmentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing the OAuth access token")
    business_id: str = Field(description="ID of the Microsoft Bookings business to query")
    start_date: str = Field(description="Calendar view start in ISO 8601 (e.g. 2024-05-01T00:00:00Z)")
    end_date: str = Field(description="Calendar view end in ISO 8601 (e.g. 2024-05-31T23:59:59Z)")


class ListBusinessesInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing the OAuth access token")


class ListServicesInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing the OAuth access token")
    business_id: str = Field(description="ID of the Microsoft Bookings business to query")


class ListStaffMembersInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing the OAuth access token")
    business_id: str = Field(description="ID of the Microsoft Bookings business to query")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CancelAppointmentInput)
@serialize_pydantic_return
async def cancel_appointment(
    auth_type: str,
    auth_data: dict[str, Any],
    business_id: str,
    appointment_id: str,
    cancellation_message: str,
) -> CancelAppointmentOutput:
    """Cancel an existing appointment in a Microsoft Bookings business with a customer-facing message."""
    if not auth_data.get("access_token"):
        return CancelAppointmentOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/solutions/bookingBusinesses/{business_id}/appointments/{appointment_id}/cancel",
                headers=headers,
                json={"cancellationMessage": cancellation_message},
            )
        if response.status_code not in (200, 204):
            return CancelAppointmentOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return CancelAppointmentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CancelAppointmentOutput(success=False, error=f"Call failed: {exc}")

    return CancelAppointmentOutput(success=True)


@tool(args_schema=CreateAppointmentInput)
@serialize_pydantic_return
async def create_appointment(
    auth_type: str,
    auth_data: dict[str, Any],
    business_id: str,
    service_id: str,
    customer_id: str,
    start_date_time: str,
    end_date_time: str,
    time_zone: str,
    customer_name: str | None = None,
    customer_email_address: str | None = None,
    customer_time_zone: str | None = None,
    customer_phone: str | None = None,
    customer_notes: str | None = None,
    is_location_online: bool | None = None,
    staff_member_ids: list[str] | None = None,
    sms_notifications_enabled: bool | None = None,
    price: float | None = None,
    price_type: str | None = None,
    duration: str | None = None,
    maximum_attendees_count: int | None = None,
    pre_buffer: str | None = None,
    post_buffer: str | None = None,
    service_notes: str | None = None,
    additional_information: str | None = None,
    is_customer_allowed_to_manage_booking: bool | None = None,
    opt_out_of_customer_email: bool | None = None,
) -> CreateAppointmentOutput:
    """Create a new appointment for a customer with a chosen service in a Microsoft Bookings business."""
    if not auth_data.get("access_token"):
        return CreateAppointmentOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)

    customer_entry: dict[str, Any] = {
        "@odata.type": "#microsoft.graph.bookingCustomerInformation",
        "customerId": customer_id,
        "timeZone": customer_time_zone or time_zone,
    }
    if customer_name:
        customer_entry["name"] = customer_name
    if customer_email_address:
        customer_entry["emailAddress"] = customer_email_address
    if customer_phone:
        customer_entry["phone"] = customer_phone

    content: dict[str, Any] = {
        "@odata.type": "#microsoft.graph.bookingAppointment",
        "serviceId": service_id,
        "customerTimeZone": customer_time_zone or time_zone,
        "startDateTime": {
            "@odata.type": "#microsoft.graph.dateTimeTimeZone",
            "dateTime": start_date_time,
            "timeZone": time_zone,
        },
        "endDateTime": {
            "@odata.type": "#microsoft.graph.dateTimeTimeZone",
            "dateTime": end_date_time,
            "timeZone": time_zone,
        },
        "customers": [customer_entry],
    }

    if customer_notes:
        content["customerNotes"] = customer_notes
    if is_location_online is not None:
        content["isLocationOnline"] = is_location_online
    if staff_member_ids:
        content["staffMemberIds"] = staff_member_ids
    if sms_notifications_enabled is not None:
        content["smsNotificationsEnabled"] = sms_notifications_enabled
    if price is not None:
        content["price"] = price
    if price_type:
        content["priceType"] = price_type
    if duration:
        content["duration"] = duration
    if maximum_attendees_count is not None:
        content["maximumAttendeesCount"] = maximum_attendees_count
    if pre_buffer:
        content["preBuffer"] = pre_buffer
    if post_buffer:
        content["postBuffer"] = post_buffer
    if service_notes:
        content["serviceNotes"] = service_notes
    if additional_information:
        content["additionalInformation"] = additional_information
    if is_customer_allowed_to_manage_booking is not None:
        content["isCustomerAllowedToManageBooking"] = is_customer_allowed_to_manage_booking
    if opt_out_of_customer_email is not None:
        content["optOutOfCustomerEmail"] = opt_out_of_customer_email

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/solutions/bookingBusinesses/{business_id}/appointments",
                headers=headers,
                json=content,
            )
        if response.status_code not in (200, 201):
            return CreateAppointmentOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateAppointmentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateAppointmentOutput(success=False, error=f"Call failed: {exc}")

    return CreateAppointmentOutput(success=True, appointment=_appointment(data))


@tool(args_schema=CreateBusinessInput)
@serialize_pydantic_return
async def create_business(
    auth_type: str,
    auth_data: dict[str, Any],
    display_name: str,
    email: str | None = None,
    phone: str | None = None,
    web_site_url: str | None = None,
    street: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country_or_region: str | None = None,
    default_currency_iso: str | None = None,
    business_type: str | None = None,
) -> CreateBusinessOutput:
    """Create a new Microsoft Bookings business."""
    if not auth_data.get("access_token"):
        return CreateBusinessOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)

    address: dict[str, Any] = {}
    if street:
        address["street"] = street
    if city:
        address["city"] = city
    if state:
        address["state"] = state
    if postal_code:
        address["postalCode"] = postal_code
    if country_or_region:
        address["countryOrRegion"] = country_or_region

    content: dict[str, Any] = {"displayName": display_name}
    if email:
        content["email"] = email
    if phone:
        content["phone"] = phone
    if web_site_url:
        content["webSiteUrl"] = web_site_url
    if address:
        content["address"] = address
    if default_currency_iso:
        content["defaultCurrencyIso"] = default_currency_iso
    if business_type:
        content["businessType"] = business_type

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/solutions/bookingBusinesses",
                headers=headers,
                json=content,
            )
        if response.status_code not in (200, 201):
            return CreateBusinessOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateBusinessOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateBusinessOutput(success=False, error=f"Call failed: {exc}")

    return CreateBusinessOutput(success=True, business=_business(data))


@tool(args_schema=CreateCustomerInput)
@serialize_pydantic_return
async def create_customer(
    auth_type: str,
    auth_data: dict[str, Any],
    business_id: str,
    display_name: str,
    email_address: str,
    phone_number: str | None = None,
    phone_type: str = "home",
    street: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country_or_region: str | None = None,
) -> CreateCustomerOutput:
    """Create a new customer record in a Microsoft Bookings business."""
    if not auth_data.get("access_token"):
        return CreateCustomerOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)

    content: dict[str, Any] = {
        "@odata.type": "#microsoft.graph.bookingCustomer",
        "displayName": display_name,
        "emailAddress": email_address,
    }
    if phone_number:
        content["phones"] = [{"number": phone_number, "type": phone_type or "home"}]

    address: dict[str, Any] = {}
    if street:
        address["street"] = street
    if city:
        address["city"] = city
    if state:
        address["state"] = state
    if postal_code:
        address["postalCode"] = postal_code
    if country_or_region:
        address["countryOrRegion"] = country_or_region
    if address:
        address["type"] = "home"
        content["addresses"] = [address]

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/solutions/bookingBusinesses/{business_id}/customers",
                headers=headers,
                json=content,
            )
        if response.status_code not in (200, 201):
            return CreateCustomerOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateCustomerOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateCustomerOutput(success=False, error=f"Call failed: {exc}")

    return CreateCustomerOutput(success=True, customer=_customer(data))


@tool(args_schema=CreateServiceInput)
@serialize_pydantic_return
async def create_service(
    auth_type: str,
    auth_data: dict[str, Any],
    business_id: str,
    display_name: str,
    default_duration: str | None = None,
    description: str | None = None,
    default_price: float | None = None,
    default_price_type: str | None = None,
    is_location_online: bool | None = None,
    staff_member_ids: list[str] | None = None,
    is_hidden_from_customers: bool | None = None,
    notes: str | None = None,
    sms_notifications_enabled: bool | None = None,
) -> CreateServiceOutput:
    """Create a new bookable service in a Microsoft Bookings business."""
    if not auth_data.get("access_token"):
        return CreateServiceOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)

    content: dict[str, Any] = {
        "@odata.type": "#microsoft.graph.bookingService",
        "displayName": display_name,
    }
    if default_duration:
        content["defaultDuration"] = default_duration
    if description:
        content["description"] = description
    if default_price is not None:
        content["defaultPrice"] = default_price
    if default_price_type:
        content["defaultPriceType"] = default_price_type
    if is_location_online is not None:
        content["isLocationOnline"] = is_location_online
    if staff_member_ids:
        content["staffMemberIds"] = staff_member_ids
    if is_hidden_from_customers is not None:
        content["isHiddenFromCustomers"] = is_hidden_from_customers
    if notes:
        content["notes"] = notes
    if sms_notifications_enabled is not None:
        content["smsNotificationsEnabled"] = sms_notifications_enabled

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/solutions/bookingBusinesses/{business_id}/services",
                headers=headers,
                json=content,
            )
        if response.status_code not in (200, 201):
            return CreateServiceOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateServiceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateServiceOutput(success=False, error=f"Call failed: {exc}")

    return CreateServiceOutput(success=True, service=_service(data))


@tool(args_schema=CreateStaffMemberInput)
@serialize_pydantic_return
async def create_staff_member(
    auth_type: str,
    auth_data: dict[str, Any],
    business_id: str,
    display_name: str,
    email_address: str,
    role: str,
    time_zone: str | None = None,
    use_business_hours: bool | None = None,
    is_email_notification_enabled: bool | None = None,
) -> CreateStaffMemberOutput:
    """Create a new staff member in a Microsoft Bookings business."""
    if not auth_data.get("access_token"):
        return CreateStaffMemberOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)

    content: dict[str, Any] = {
        "@odata.type": "#microsoft.graph.bookingStaffMember",
        "displayName": display_name,
        "emailAddress": email_address,
        "role": role,
    }
    if time_zone:
        content["timeZone"] = time_zone
    if use_business_hours is not None:
        content["useBusinessHours"] = use_business_hours
    if is_email_notification_enabled is not None:
        content["isEmailNotificationEnabled"] = is_email_notification_enabled

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/solutions/bookingBusinesses/{business_id}/staffMembers",
                headers=headers,
                json=content,
            )
        if response.status_code not in (200, 201):
            return CreateStaffMemberOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateStaffMemberOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateStaffMemberOutput(success=False, error=f"Call failed: {exc}")

    return CreateStaffMemberOutput(success=True, staff_member=_staff_member(data))


@tool(args_schema=ListAppointmentsInput)
@serialize_pydantic_return
async def list_appointments(
    auth_type: str,
    auth_data: dict[str, Any],
    business_id: str,
    start_date: str,
    end_date: str,
) -> ListAppointmentsOutput:
    """List appointments within a date range for a Microsoft Bookings business via calendarView."""
    if not auth_data.get("access_token"):
        return ListAppointmentsOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/solutions/bookingBusinesses/{business_id}/calendarView",
                headers=headers,
                params={"start": start_date, "end": end_date},
            )
        if response.status_code != 200:
            return ListAppointmentsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListAppointmentsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAppointmentsOutput(success=False, error=f"Call failed: {exc}")

    items = [_appointment(item) for item in data.get("value") or []]
    return ListAppointmentsOutput(success=True, appointments=items, total=len(items))


@tool(args_schema=ListBusinessesInput)
@serialize_pydantic_return
async def list_businesses(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListBusinessesOutput:
    """List all Microsoft Bookings businesses accessible to the authenticated user."""
    if not auth_data.get("access_token"):
        return ListBusinessesOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/solutions/bookingBusinesses",
                headers=headers,
            )
        if response.status_code != 200:
            return ListBusinessesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListBusinessesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListBusinessesOutput(success=False, error=f"Call failed: {exc}")

    items = [_business(item) for item in data.get("value") or []]
    return ListBusinessesOutput(success=True, businesses=items, total=len(items))


@tool(args_schema=ListServicesInput)
@serialize_pydantic_return
async def list_services(
    auth_type: str,
    auth_data: dict[str, Any],
    business_id: str,
) -> ListServicesOutput:
    """List all bookable services for a Microsoft Bookings business."""
    if not auth_data.get("access_token"):
        return ListServicesOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/solutions/bookingBusinesses/{business_id}/services",
                headers=headers,
            )
        if response.status_code != 200:
            return ListServicesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListServicesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListServicesOutput(success=False, error=f"Call failed: {exc}")

    items = [_service(item) for item in data.get("value") or []]
    return ListServicesOutput(success=True, services=items, total=len(items))


@tool(args_schema=ListStaffMembersInput)
@serialize_pydantic_return
async def list_staff_members(
    auth_type: str,
    auth_data: dict[str, Any],
    business_id: str,
) -> ListStaffMembersOutput:
    """List all staff members for a Microsoft Bookings business."""
    if not auth_data.get("access_token"):
        return ListStaffMembersOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/solutions/bookingBusinesses/{business_id}/staffMembers",
                headers=headers,
            )
        if response.status_code != 200:
            return ListStaffMembersOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListStaffMembersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListStaffMembersOutput(success=False, error=f"Call failed: {exc}")

    items = [_staff_member(item) for item in data.get("value") or []]
    return ListStaffMembersOutput(success=True, staff_members=items, total=len(items))
