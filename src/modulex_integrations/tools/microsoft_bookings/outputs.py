"""Pydantic response models for the microsoft_bookings integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AppointmentSummary",
    "BusinessSummary",
    "CancelAppointmentOutput",
    "CreateAppointmentOutput",
    "CreateBusinessOutput",
    "CreateCustomerOutput",
    "CreateServiceOutput",
    "CreateStaffMemberOutput",
    "CustomerSummary",
    "ListAppointmentsOutput",
    "ListBusinessesOutput",
    "ListServicesOutput",
    "ListStaffMembersOutput",
    "ServiceSummary",
    "StaffMemberSummary",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class AppointmentSummary(_Base):
    id: str | None = None
    self_service_appointment_id: str | None = None
    service_id: str | None = None
    service_name: str | None = None
    customer_name: str | None = None
    customer_email_address: str | None = None
    customer_time_zone: str | None = None
    start_date_time: dict[str, Any] | None = None
    end_date_time: dict[str, Any] | None = None
    duration: str | None = None
    price: float | None = None
    price_type: str | None = None
    is_location_online: bool | None = None
    join_web_url: str | None = None
    sms_notifications_enabled: bool | None = None
    staff_member_ids: list[str] = Field(default_factory=list)
    customers: list[dict[str, Any]] = Field(default_factory=list)


class BusinessSummary(_Base):
    id: str | None = None
    display_name: str | None = None
    email: str | None = None
    phone: str | None = None
    web_site_url: str | None = None
    default_currency_iso: str | None = None
    business_type: str | None = None
    address: dict[str, Any] | None = None
    is_published: bool | None = None
    public_url: str | None = None


class CustomerSummary(_Base):
    id: str | None = None
    display_name: str | None = None
    email_address: str | None = None
    phones: list[dict[str, Any]] = Field(default_factory=list)
    addresses: list[dict[str, Any]] = Field(default_factory=list)


class ServiceSummary(_Base):
    id: str | None = None
    display_name: str | None = None
    description: str | None = None
    default_duration: str | None = None
    default_price: float | None = None
    default_price_type: str | None = None
    is_location_online: bool | None = None
    is_hidden_from_customers: bool | None = None
    notes: str | None = None
    staff_member_ids: list[str] = Field(default_factory=list)
    sms_notifications_enabled: bool | None = None


class StaffMemberSummary(_Base):
    id: str | None = None
    display_name: str | None = None
    email_address: str | None = None
    role: str | None = None
    time_zone: str | None = None
    use_business_hours: bool | None = None
    is_email_notification_enabled: bool | None = None
    availability_is_affected_by_personal_calendar: bool | None = None


# --- Per-action output models ---------------------------------------------


class CancelAppointmentOutput(_Base):
    success: bool
    error: str | None = None


class CreateAppointmentOutput(_Base):
    success: bool
    error: str | None = None
    appointment: AppointmentSummary | None = None


class CreateBusinessOutput(_Base):
    success: bool
    error: str | None = None
    business: BusinessSummary | None = None


class CreateCustomerOutput(_Base):
    success: bool
    error: str | None = None
    customer: CustomerSummary | None = None


class CreateServiceOutput(_Base):
    success: bool
    error: str | None = None
    service: ServiceSummary | None = None


class CreateStaffMemberOutput(_Base):
    success: bool
    error: str | None = None
    staff_member: StaffMemberSummary | None = None


class ListAppointmentsOutput(_Base):
    success: bool
    error: str | None = None
    appointments: list[AppointmentSummary] = Field(default_factory=list)
    total: int = 0


class ListBusinessesOutput(_Base):
    success: bool
    error: str | None = None
    businesses: list[BusinessSummary] = Field(default_factory=list)
    total: int = 0


class ListServicesOutput(_Base):
    success: bool
    error: str | None = None
    services: list[ServiceSummary] = Field(default_factory=list)
    total: int = 0


class ListStaffMembersOutput(_Base):
    success: bool
    error: str | None = None
    staff_members: list[StaffMemberSummary] = Field(default_factory=list)
    total: int = 0
