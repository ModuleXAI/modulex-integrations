# Twilio

Cloud communications platform for SMS messaging, voice calls, phone number lookup, and phone verification via the Twilio REST API (`api.twilio.com`).

## Authentication

### Twilio Account Credentials

Authenticate using your Twilio Account SID and Auth Token (HTTP Basic Auth).

- Log in to the [Twilio Console](https://console.twilio.com). Your Account SID and Auth Token are on the dashboard home page.
- Required env vars:
  - `TWILIO_ACCOUNT_SID` (format: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`) — not sensitive (used as the HTTP Basic Auth username).
  - `TWILIO_AUTH_TOKEN` — sensitive; the Auth Token from your Console dashboard.

## Tools

| name | description | required params |
| --- | --- | --- |
| `send_message` | Send an SMS or MMS message with optional media files. | `from_number`, `to`, `body` |
| `make_phone_call` | Initiate a phone call using text-to-speech, a TwiML URL, or an application SID. | `from_number`, `to`, `call_type` |
| `get_message` | Retrieve details of a specific message by SID. | `message_id` |
| `delete_message` | Delete a message record from your account. | `message_id` |
| `list_messages` | List messages associated with your account, optionally filtered by sender or recipient. | |
| `list_message_media` | List media resources associated with a message. | `message_id` |
| `get_call` | Retrieve details of a specific call by SID. | `sid` |
| `delete_call` | Delete a call record from your account. | `sid` |
| `list_calls` | List calls associated with your account, optionally filtered by number, status, or parent call. | |
| `download_recording_media` | Get the download URL for a call recording in the specified format. | `recording_id` |
| `phone_number_lookup` | Look up information about a phone number including line type intelligence. | `phone_number` |
| `send_sms_verification` | Send an SMS verification code to a phone number via Twilio Verify. | `service_sid`, `to` |
| `check_verification_token` | Check if a user-provided verification code is correct. | `service_sid`, `to`, `code` |
| `create_verification_service` | Create a new Twilio Verify service for sending SMS verifications. | `friendly_name` |
| `list_transcripts` | List voice intelligence transcripts, optionally including transcript text. | |
| `get_transcripts` | Retrieve full transcripts with sentences for the specified transcript SIDs. | `transcript_sids` |
| `list_phone_numbers` | List incoming phone numbers on your Twilio account. | |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential.

## Limits & Quotas

- **SMS**: Throughput varies by number type. Long codes: 1 SMS/sec (US/Canada). Toll-free: 3 SMS/sec. Short codes: 30+ SMS/sec.
- **Voice**: Concurrent call limits depend on your account type and phone numbers provisioned.
- **Lookup**: Charged per lookup. Standard rate lookup is included in the monthly fee; carrier/line-type lookups are billed per query.
- **Verify**: Each verification attempt is billed. See [Twilio Verify pricing](https://www.twilio.com/verify/pricing).
- **Voice Intelligence**: Charged per minute of audio transcribed.
- **Error model**: Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
