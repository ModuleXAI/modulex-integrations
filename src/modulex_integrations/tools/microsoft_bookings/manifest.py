"""Microsoft Bookings integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="microsoft_bookings",
    display_name="Microsoft Bookings",
    description=(
        "Create and manage Microsoft Bookings businesses, services, staff "
        "members, customers, and appointments via the Microsoft Graph API."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:microsoft_bookings",
    app_url="https://www.microsoft.com/en-us/microsoft-365/business/scheduling-and-booking-app",
    categories=["Productivity & Collaboration", "Scheduling", "Business Services"],
    actions=[
        ActionDefinition(
            name="cancel_appointment",
            description="Cancel an existing appointment in a Microsoft Bookings business with a customer-facing message.",
            parameters={
                "business_id": ParameterDef(
                    type="string",
                    description="ID of the Microsoft Bookings business that owns the appointment.",
                    required=True,
                ),
                "appointment_id": ParameterDef(
                    type="string",
                    description="ID of the appointment to cancel.",
                    required=True,
                ),
                "cancellation_message": ParameterDef(
                    type="string",
                    description="Message sent to the customer and staff members explaining the cancellation.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_appointment",
            description="Create a new appointment for a customer with a chosen service in a Microsoft Bookings business.",
            parameters={
                "business_id": ParameterDef(
                    type="string",
                    description="ID of the Microsoft Bookings business that will own the appointment.",
                    required=True,
                ),
                "service_id": ParameterDef(
                    type="string",
                    description="ID of the booking service the customer is booking.",
                    required=True,
                ),
                "customer_id": ParameterDef(
                    type="string",
                    description="ID of the existing customer the appointment is being booked for.",
                    required=True,
                ),
                "start_date_time": ParameterDef(
                    type="string",
                    description="Appointment start time in ISO 8601 format (e.g. 2024-05-01T12:00:00).",
                    required=True,
                ),
                "end_date_time": ParameterDef(
                    type="string",
                    description="Appointment end time in ISO 8601 format (e.g. 2024-05-01T13:00:00).",
                    required=True,
                ),
                "time_zone": ParameterDef(
                    type="string",
                    description="IANA time zone for the appointment (e.g. UTC, America/Chicago).",
                    required=True,
                ),
                "customer_name": ParameterDef(
                    type="string",
                    description="Display name to record for the customer on this appointment.",
                ),
                "customer_email_address": ParameterDef(
                    type="string",
                    description="SMTP email address for the customer on this appointment.",
                ),
                "customer_time_zone": ParameterDef(
                    type="string",
                    description="IANA time zone for the customer (falls back to time_zone if omitted).",
                ),
                "customer_phone": ParameterDef(
                    type="string",
                    description="Phone number to record for the customer on this appointment.",
                ),
                "customer_notes": ParameterDef(
                    type="string",
                    description="Notes from the customer associated with this appointment.",
                ),
                "is_location_online": ParameterDef(
                    type="boolean",
                    description="True indicates that the appointment will be held online.",
                ),
                "staff_member_ids": ParameterDef(
                    type="array",
                    description="List of staff member IDs assigned to this appointment.",
                ),
                "sms_notifications_enabled": ParameterDef(
                    type="boolean",
                    description="If True, send SMS notifications to the customer for the appointment.",
                ),
                "price": ParameterDef(
                    type="number",
                    description="Regular monetary price for the appointment.",
                ),
                "price_type": ParameterDef(
                    type="string",
                    description="Pricing structure: undefined, fixedPrice, startingAt, hourly, free, priceVaries, callUs, notSet.",
                ),
                "duration": ParameterDef(
                    type="string",
                    description="Appointment length in ISO 8601 duration (e.g. PT1H, PT30M).",
                ),
                "maximum_attendees_count": ParameterDef(
                    type="integer",
                    description="Maximum number of customers allowed in this appointment.",
                ),
                "pre_buffer": ParameterDef(
                    type="string",
                    description="Time to reserve before the appointment in ISO 8601 duration (e.g. PT15M).",
                ),
                "post_buffer": ParameterDef(
                    type="string",
                    description="Time to reserve after the appointment in ISO 8601 duration (e.g. PT15M).",
                ),
                "service_notes": ParameterDef(
                    type="string",
                    description="Notes from the staff member about this appointment.",
                ),
                "additional_information": ParameterDef(
                    type="string",
                    description="Additional information sent to the customer when the appointment is confirmed.",
                ),
                "is_customer_allowed_to_manage_booking": ParameterDef(
                    type="boolean",
                    description="True allows the customer to manage bookings created by the staff.",
                ),
                "opt_out_of_customer_email": ParameterDef(
                    type="boolean",
                    description="If True, the customer will not receive an email confirmation for this appointment.",
                ),
            },
        ),
        ActionDefinition(
            name="create_business",
            description="Create a new Microsoft Bookings business.",
            parameters={
                "display_name": ParameterDef(
                    type="string",
                    description="Customer-facing name of the booking business.",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="Email address for the business.",
                ),
                "phone": ParameterDef(
                    type="string",
                    description="Telephone number for the business.",
                ),
                "web_site_url": ParameterDef(
                    type="string",
                    description="URL of the business web site.",
                ),
                "street": ParameterDef(
                    type="string",
                    description="Street address of the business.",
                ),
                "city": ParameterDef(
                    type="string",
                    description="City of the business.",
                ),
                "state": ParameterDef(
                    type="string",
                    description="State of the business.",
                ),
                "postal_code": ParameterDef(
                    type="string",
                    description="Postal code of the business.",
                ),
                "country_or_region": ParameterDef(
                    type="string",
                    description="Country or region of the business.",
                ),
                "default_currency_iso": ParameterDef(
                    type="string",
                    description="ISO currency code the business operates in (e.g. USD).",
                ),
                "business_type": ParameterDef(
                    type="string",
                    description="Free-form description of the type of business.",
                ),
            },
        ),
        ActionDefinition(
            name="create_customer",
            description="Create a new customer record in a Microsoft Bookings business.",
            parameters={
                "business_id": ParameterDef(
                    type="string",
                    description="ID of the Microsoft Bookings business that will own the customer.",
                    required=True,
                ),
                "display_name": ParameterDef(
                    type="string",
                    description="Customer's full name.",
                    required=True,
                ),
                "email_address": ParameterDef(
                    type="string",
                    description="Customer's email address.",
                    required=True,
                ),
                "phone_number": ParameterDef(
                    type="string",
                    description="Customer's phone number.",
                ),
                "phone_type": ParameterDef(
                    type="string",
                    description="Type of phone number: home, business, mobile.",
                    default="home",
                ),
                "street": ParameterDef(
                    type="string",
                    description="Street address for the customer.",
                ),
                "city": ParameterDef(
                    type="string",
                    description="City for the customer.",
                ),
                "state": ParameterDef(
                    type="string",
                    description="State for the customer.",
                ),
                "postal_code": ParameterDef(
                    type="string",
                    description="Postal code for the customer.",
                ),
                "country_or_region": ParameterDef(
                    type="string",
                    description="Country or region for the customer.",
                ),
            },
        ),
        ActionDefinition(
            name="create_service",
            description="Create a new bookable service in a Microsoft Bookings business.",
            parameters={
                "business_id": ParameterDef(
                    type="string",
                    description="ID of the Microsoft Bookings business that will own the service.",
                    required=True,
                ),
                "display_name": ParameterDef(
                    type="string",
                    description="Customer-facing name of the service.",
                    required=True,
                ),
                "default_duration": ParameterDef(
                    type="string",
                    description="Default service length in ISO 8601 duration (e.g. PT1H30M).",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Free-form description for the service.",
                ),
                "default_price": ParameterDef(
                    type="number",
                    description="Default monetary price for the service.",
                ),
                "default_price_type": ParameterDef(
                    type="string",
                    description="Default pricing structure: undefined, fixedPrice, startingAt, hourly, free, priceVaries, callUs, notSet.",
                ),
                "is_location_online": ParameterDef(
                    type="boolean",
                    description="True indicates the service will be held online.",
                ),
                "staff_member_ids": ParameterDef(
                    type="array",
                    description="List of staff member IDs allowed to provide this service.",
                ),
                "is_hidden_from_customers": ParameterDef(
                    type="boolean",
                    description="True hides this service from the customer-facing booking page.",
                ),
                "notes": ParameterDef(
                    type="string",
                    description="Additional notes about this service (staff-facing).",
                ),
                "sms_notifications_enabled": ParameterDef(
                    type="boolean",
                    description="True enables SMS notifications to customers for this service.",
                ),
            },
        ),
        ActionDefinition(
            name="create_staff_member",
            description="Create a new staff member in a Microsoft Bookings business.",
            parameters={
                "business_id": ParameterDef(
                    type="string",
                    description="ID of the Microsoft Bookings business that will own the staff member.",
                    required=True,
                ),
                "display_name": ParameterDef(
                    type="string",
                    description="Staff member's name as shown to customers.",
                    required=True,
                ),
                "email_address": ParameterDef(
                    type="string",
                    description="Staff member's email address.",
                    required=True,
                ),
                "role": ParameterDef(
                    type="string",
                    description="Staff member's role: guest, administrator, viewer, externalGuest, scheduler, teamMember.",
                    required=True,
                ),
                "time_zone": ParameterDef(
                    type="string",
                    description="IANA time zone for the staff member (e.g. America/Chicago).",
                ),
                "use_business_hours": ParameterDef(
                    type="boolean",
                    description="True means the staff member follows the business' default hours; False uses workingHours.",
                ),
                "is_email_notification_enabled": ParameterDef(
                    type="boolean",
                    description="True to send email notifications to this staff member.",
                ),
            },
        ),
        ActionDefinition(
            name="list_appointments",
            description="List appointments within a date range for a Microsoft Bookings business via calendarView.",
            parameters={
                "business_id": ParameterDef(
                    type="string",
                    description="ID of the Microsoft Bookings business to query.",
                    required=True,
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="Calendar view start in ISO 8601 (e.g. 2024-05-01T00:00:00Z).",
                    required=True,
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="Calendar view end in ISO 8601 (e.g. 2024-05-31T23:59:59Z).",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_businesses",
            description="List all Microsoft Bookings businesses accessible to the authenticated user.",
            parameters={},
        ),
        ActionDefinition(
            name="list_services",
            description="List all bookable services for a Microsoft Bookings business.",
            parameters={
                "business_id": ParameterDef(
                    type="string",
                    description="ID of the Microsoft Bookings business to query.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_staff_members",
            description="List all staff members for a Microsoft Bookings business.",
            parameters={
                "business_id": ParameterDef(
                    type="string",
                    description="ID of the Microsoft Bookings business to query.",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using a Microsoft (Azure AD / Entra ID) OAuth app with Bookings scopes.",
            setup_environment_variables=[
                EnvVar(
                    name="MICROSOFT_BOOKINGS_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Application (client) ID of the Azure AD app registration.",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="00000000-0000-0000-0000-000000000000",
                    about_url="https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                ),
                EnvVar(
                    name="MICROSOFT_BOOKINGS_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Client secret value from the Azure AD app registration.",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="x" * 40,
                    about_url="https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                scopes=[
                    "offline_access",
                    "Bookings.Read.All",
                    "BookingsAppointment.ReadWrite.All",
                    "Bookings.ReadWrite.All",
                    "Bookings.Manage.All",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://graph.microsoft.com/v1.0/solutions/bookingBusinesses",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["value"],
                ),
                cost_level="free",
                description="Validates the OAuth token by listing booking businesses.",
            ),
        ),
    ],
)
