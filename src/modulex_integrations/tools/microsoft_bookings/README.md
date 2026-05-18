# Microsoft Bookings

Create and manage Microsoft Bookings businesses, services, staff members, customers, and appointments through the Microsoft Graph API (`graph.microsoft.com/v1.0`).

## Authentication

Authentication is via Microsoft (Azure AD / Entra ID) OAuth 2.0. ModuleX brokers the consent dance and injects the resolved access token at tool-call time.

### OAuth2 Authentication

- Register an application at the [Azure portal](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) under **App registrations**.
- Add `https://api.modulex.dev/credentials/oauth2/callback` as a redirect URI on the app registration.
- Grant the following delegated Microsoft Graph permissions on the app registration's **API permissions** blade:
  - `offline_access`
  - `Bookings.Read.All`
  - `BookingsAppointment.ReadWrite.All`
  - `Bookings.ReadWrite.All`
  - `Bookings.Manage.All`
- Required env vars:
  - `MICROSOFT_BOOKINGS_OAUTH2_CLIENT_ID` (format: `00000000-0000-0000-0000-000000000000`)
  - `MICROSOFT_BOOKINGS_OAUTH2_CLIENT_SECRET`
- The signed-in account must have a Microsoft 365 license that includes Bookings and must be a Bookings business owner or admin.

## Tools

| name | description | required params |
| --- | --- | --- |
| `cancel_appointment` | Cancel an existing appointment in a Microsoft Bookings business with a customer-facing message. | `business_id`, `appointment_id`, `cancellation_message` |
| `create_appointment` | Create a new appointment for a customer with a chosen service in a Microsoft Bookings business. | `business_id`, `service_id`, `customer_id`, `start_date_time`, `end_date_time`, `time_zone` |
| `create_business` | Create a new Microsoft Bookings business. | `display_name` |
| `create_customer` | Create a new customer record in a Microsoft Bookings business. | `business_id`, `display_name`, `email_address` |
| `create_service` | Create a new bookable service in a Microsoft Bookings business. | `business_id`, `display_name` |
| `create_staff_member` | Create a new staff member in a Microsoft Bookings business. | `business_id`, `display_name`, `email_address`, `role` |
| `list_appointments` | List appointments within a date range for a Microsoft Bookings business via calendarView. | `business_id`, `start_date`, `end_date` |
| `list_businesses` | List all Microsoft Bookings businesses accessible to the authenticated user. | _none_ |
| `list_services` | List all bookable services for a Microsoft Bookings business. | `business_id` |
| `list_staff_members` | List all staff members for a Microsoft Bookings business. | `business_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential.

## Limits & Quotas

- Microsoft Graph enforces a per-app and per-user throttling envelope; Bookings endpoints typically allow a few thousand requests per 10-minute window per app+tenant. See the [Microsoft Graph throttling guidance](https://learn.microsoft.com/en-us/graph/throttling) for current limits.
- Creating appointments requires that the referenced `customer_id` already exists in the business; the tool will surface the underlying Graph error if it does not.
- **Error model**: non-2xx Graph responses and timeouts are caught and returned as `success=False` + `error` rather than raising. Plan for retries on the agent side based on the error string.
- Dynamic ID dropdowns (business/staff/service/customer/appointment pickers) are not part of this integration; the LLM must supply IDs directly. Use the `list_*` tools to enumerate available IDs first.

## Maintainer

ModuleX core team.
