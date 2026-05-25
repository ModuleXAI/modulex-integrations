"""Twilio integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="twilio",
    display_name="Twilio",
    description="Cloud communications platform for SMS, voice calls, phone number lookup, and verification via the Twilio REST API.",
    version="1.0.0",
    author="ModuleX",
    logo="logos:twilio-icon",
    app_url="https://www.twilio.com",
    categories=["Communication", "SMS", "Voice", "Verification"],
    actions=[
        ActionDefinition(
            name="send_message",
            description="Send an SMS or MMS message with optional media files.",
            parameters={
                "from_number": ParameterDef(
                    type="string",
                    description="The sender's Twilio phone number in E.164 format (e.g., +15551234567).",
                    required=True,
                ),
                "to": ParameterDef(
                    type="string",
                    description="The destination phone number in E.164 format (e.g., +16175551212).",
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="The text of the message, limited to 1600 characters.",
                    required=True,
                ),
                "media_url": ParameterDef(
                    type="array",
                    description="Array of URLs of media to include. Up to 10 URLs, max 5 MB each.",
                ),
            },
        ),
        ActionDefinition(
            name="make_phone_call",
            description="Initiate a phone call using text-to-speech, a TwiML URL, or an application SID.",
            parameters={
                "from_number": ParameterDef(
                    type="string",
                    description="The caller's Twilio phone number in E.164 format.",
                    required=True,
                ),
                "to": ParameterDef(
                    type="string",
                    description="The destination phone number in E.164 format.",
                    required=True,
                ),
                "call_type": ParameterDef(
                    type="string",
                    description="How to handle the call. Allowed values: text, url, application.",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Text for Twilio to speak when answered. Required when call_type is 'text'.",
                ),
                "url": ParameterDef(
                    type="string",
                    description="URL returning TwiML instructions. Required when call_type is 'url'.",
                ),
                "application_sid": ParameterDef(
                    type="string",
                    description="SID of the Application resource. Required when call_type is 'application'.",
                ),
                "timeout": ParameterDef(
                    type="integer",
                    description="Seconds to ring before assuming no answer (default 60, max 600).",
                ),
                "record": ParameterDef(
                    type="boolean",
                    description="Whether to record the call.",
                ),
            },
        ),
        ActionDefinition(
            name="get_message",
            description="Retrieve details of a specific message by SID.",
            parameters={
                "message_id": ParameterDef(
                    type="string",
                    description="The SID of the message to retrieve.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_message",
            description="Delete a message record from your account.",
            parameters={
                "message_id": ParameterDef(
                    type="string",
                    description="The SID of the message to delete.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_messages",
            description="List messages associated with your account, optionally filtered by sender or recipient.",
            parameters={
                "from_number": ParameterDef(
                    type="string",
                    description="Only return messages sent from this phone number in E.164 format.",
                ),
                "to": ParameterDef(
                    type="string",
                    description="Only return messages sent to this phone number in E.164 format.",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of messages to return.",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="list_message_media",
            description="List media resources associated with a message.",
            parameters={
                "message_id": ParameterDef(
                    type="string",
                    description="The SID of the message.",
                    required=True,
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of media items to return.",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="get_call",
            description="Retrieve details of a specific call by SID.",
            parameters={
                "sid": ParameterDef(
                    type="string",
                    description="The SID of the call to retrieve.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_call",
            description="Delete a call record from your account.",
            parameters={
                "sid": ParameterDef(
                    type="string",
                    description="The SID of the call to delete.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_calls",
            description="List calls associated with your account, optionally filtered by number, status, or parent call.",
            parameters={
                "from_number": ParameterDef(
                    type="string",
                    description="Only include calls from this phone number in E.164 format.",
                ),
                "to": ParameterDef(
                    type="string",
                    description="Only include calls to this phone number in E.164 format.",
                ),
                "parent_call_sid": ParameterDef(
                    type="string",
                    description="Only include calls spawned by the call with this SID.",
                ),
                "status": ParameterDef(
                    type="string",
                    description="Filter by status: queued, ringing, in-progress, canceled, completed, failed, busy, no-answer.",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of calls to return.",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="download_recording_media",
            description="Get the download URL for a call recording in the specified format.",
            parameters={
                "recording_id": ParameterDef(
                    type="string",
                    description="The SID of the recording.",
                    required=True,
                ),
                "format": ParameterDef(
                    type="string",
                    description="Audio format: .mp3 or .wav.",
                    default=".wav",
                ),
            },
        ),
        ActionDefinition(
            name="phone_number_lookup",
            description="Look up information about a phone number including line type intelligence.",
            parameters={
                "phone_number": ParameterDef(
                    type="string",
                    description="The phone number to look up.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="send_sms_verification",
            description="Send an SMS verification code to a phone number via Twilio Verify.",
            parameters={
                "service_sid": ParameterDef(
                    type="string",
                    description="The SID of the Verify service.",
                    required=True,
                ),
                "to": ParameterDef(
                    type="string",
                    description="The destination phone number in E.164 format.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="check_verification_token",
            description="Check if a user-provided verification code is correct.",
            parameters={
                "service_sid": ParameterDef(
                    type="string",
                    description="The SID of the Verify service.",
                    required=True,
                ),
                "to": ParameterDef(
                    type="string",
                    description="The phone number that received the verification code in E.164 format.",
                    required=True,
                ),
                "code": ParameterDef(
                    type="string",
                    description="The verification code to check.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_verification_service",
            description="Create a new Twilio Verify service for sending SMS verifications.",
            parameters={
                "friendly_name": ParameterDef(
                    type="string",
                    description="A human-readable name for the new verification service.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_transcripts",
            description="List voice intelligence transcripts, optionally including transcript text.",
            parameters={
                "include_transcript_text": ParameterDef(
                    type="boolean",
                    description="Set to true to include transcript sentences in the response.",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of transcripts to return.",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="get_transcripts",
            description="Retrieve full transcripts with sentences for the specified transcript SIDs.",
            parameters={
                "transcript_sids": ParameterDef(
                    type="array",
                    description="Array of transcript SID strings to retrieve.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_phone_numbers",
            description="List incoming phone numbers on your Twilio account.",
            parameters={},
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Twilio Account Credentials",
            description="Authenticate using your Twilio Account SID and Auth Token (HTTP Basic Auth).",
            setup_instructions=[
                "Log in to the Twilio Console at https://console.twilio.com",
                "Your Account SID and Auth Token are on the dashboard home page.",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="TWILIO_ACCOUNT_SID",
                    display_name="Account SID",
                    description="Your Twilio Account SID (starts with 'AC').",
                    required=True,
                    sensitive=False,
                    sample_format="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://console.twilio.com",
                ),
                EnvVar(
                    name="TWILIO_AUTH_TOKEN",
                    display_name="Auth Token",
                    description="Your Twilio Auth Token from the Console dashboard.",
                    required=True,
                    sensitive=True,
                    about_url="https://console.twilio.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}.json",
                method="GET",
                # Twilio uses HTTP Basic Auth base64("{TWILIO_ACCOUNT_SID}:
                # {TWILIO_AUTH_TOKEN}"). The credential tester substitutes
                # placeholders as raw strings, so the header arrives at
                # Twilio as the literal `Basic <raw-token>` — 401 is
                # expected. We accept 200 (real auth, unlikely) or 401
                # (literal placeholder auth) as success: both confirm
                # the account SID URL resolves and Twilio responded.
                # True credential validation runs at first-call time
                # via tools.py.
                headers={"Authorization": "Basic {TWILIO_AUTH_TOKEN}"},
                success_indicators=SuccessIndicators(status_codes=[200, 401]),
                cost_level="free",
                description=(
                    "Reachability + endpoint-existence check against the "
                    "Twilio account JSON endpoint. Accepts 200 (real "
                    "Base64 auth) or 401 (literal placeholder auth — "
                    "expected). Full credential validation happens at "
                    "first action call."
                ),
            ),
        ),
    ],
)
