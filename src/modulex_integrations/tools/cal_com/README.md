# Cal.com

Scheduling and booking management via the Cal.com v2 REST API (`api.cal.com/v2`).

## Authentication

### API Key

- Sign in at [Cal.com](https://app.cal.com), navigate to **Settings > Developer > API Keys**.
- Create a new API key or copy an existing one.
- Required env var: `CAL_COM_API_KEY` (format: `cal_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).
- The API key is sent as a Bearer token in the `Authorization` header per Cal.com's v2 API convention.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_booking` | Create a new booking on Cal.com | `booking_type`, `attendee_name`, `attendee_time_zone`, `start` |
| `delete_booking` | Cancel an existing booking by its UID | `booking_id` |
| `get_all_bookings` | Retrieve all bookings from Cal.com with optional filters | (none) |
| `get_bookable_slots` | Retrieve available bookable slots between a datetime range | `start`, `end` |
| `get_booking` | Retrieve a booking by its UID | `booking_id` |
| `list_event_type_id_options` | Retrieve available event types with their IDs | (none) |

Every tool takes an additional `api_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- Cal.com does not publicly document rate limits for the v2 API; enterprise plans may have higher thresholds.
- The free tier has a limited number of event types and team members.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
