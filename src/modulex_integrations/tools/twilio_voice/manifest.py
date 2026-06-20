"""Twilio Voice integration manifest.

Twilio uses HTTP Basic authentication: the Account SID is the username
and the Auth Token is the password. In modulex terms this is the
``api_key`` convention — the Auth Token is injected as ``api_key`` while
the Account SID is carried in the credential data and passed to each
action as ``account_sid``. The credential test endpoint validates both
halves via declarative Basic Auth synthesis (``BasicAuthSpec``).
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    BasicAuthSpec,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="twilio_voice",
    display_name="Twilio Voice",
    description=(
        "Make and manage phone calls with Twilio Programmable Voice. "
        "Place outbound calls with TwiML instructions, list call logs, and "
        "retrieve call recordings."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:twilio",
    app_url="https://www.twilio.com",
    categories=["Communication", "messaging", "text-to-speech"],
    actions=[
        ActionDefinition(
            name="make_call",
            description="Make an outbound phone call using the Twilio Voice API.",
            parameters={
                "to": ParameterDef(
                    type="string",
                    description="Phone number to call in E.164 format (e.g., +14155551234)",
                    required=True,
                ),
                "from_": ParameterDef(
                    type="string",
                    description=(
                        "Your Twilio phone number to call from in E.164 format "
                        "(e.g., +14155559876)"
                    ),
                    required=True,
                ),
                "account_sid": ParameterDef(
                    type="string",
                    description="Twilio Account SID (starts with 'AC')",
                    required=True,
                ),
                "url": ParameterDef(
                    type="string",
                    description="Webhook URL that returns TwiML instructions for the call",
                ),
                "twiml": ParameterDef(
                    type="string",
                    description=(
                        "TwiML instructions to execute (raw XML, e.g. "
                        "'<Response><Say>Hello</Say></Response>'). Provide this or 'url'."
                    ),
                ),
                "status_callback": ParameterDef(
                    type="string",
                    description="Webhook URL for call status updates",
                ),
                "status_callback_method": ParameterDef(
                    type="string",
                    description="HTTP method for the status callback (GET or POST)",
                ),
                "record": ParameterDef(
                    type="boolean",
                    description="Whether to record the call",
                    default=False,
                ),
                "recording_status_callback": ParameterDef(
                    type="string",
                    description="Webhook URL for recording status updates",
                ),
                "timeout": ParameterDef(
                    type="integer",
                    description="Seconds to wait for an answer before giving up (default: 60)",
                ),
                "machine_detection": ParameterDef(
                    type="string",
                    description="Answering machine detection: 'Enable' or 'DetectMessageEnd'",
                ),
            },
        ),
        ActionDefinition(
            name="list_calls",
            description="Retrieve a list of calls made to and from a Twilio account.",
            parameters={
                "account_sid": ParameterDef(
                    type="string",
                    description="Twilio Account SID (starts with 'AC')",
                    required=True,
                ),
                "to": ParameterDef(
                    type="string",
                    description="Filter by calls to this phone number (E.164 format)",
                ),
                "from_": ParameterDef(
                    type="string",
                    description="Filter by calls from this phone number (E.164 format)",
                ),
                "status": ParameterDef(
                    type="string",
                    description=(
                        "Filter by call status (queued, ringing, in-progress, "
                        "completed, busy, failed, no-answer, canceled)"
                    ),
                ),
                "start_time_after": ParameterDef(
                    type="string",
                    description="Filter calls that started on or after this date (YYYY-MM-DD)",
                ),
                "start_time_before": ParameterDef(
                    type="string",
                    description="Filter calls that started on or before this date (YYYY-MM-DD)",
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of records to return (max 1000, default 50)",
                ),
                "include_recordings": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether to fetch recording SIDs for each returned call "
                        "(adds one extra request per call that has recordings)"
                    ),
                    default=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_recording",
            description="Retrieve call recording information by recording SID.",
            parameters={
                "recording_sid": ParameterDef(
                    type="string",
                    description=(
                        "Recording SID to retrieve "
                        "(e.g., RExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)"
                    ),
                    required=True,
                ),
                "account_sid": ParameterDef(
                    type="string",
                    description="Twilio Account SID (starts with 'AC')",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Account SID & Auth Token",
            description=(
                "Authenticate with your Twilio Account SID and Auth Token "
                "using HTTP Basic authentication"
            ),
            setup_instructions=[
                "Sign in to the Twilio Console at https://console.twilio.com",
                "On the dashboard, find your Account SID (starts with 'AC')",
                "Reveal and copy your Auth Token",
                "Provide the Account SID and Auth Token below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="TWILIO_ACCOUNT_SID",
                    display_name="Twilio Account SID",
                    description="Your Twilio Account SID from the Twilio Console",
                    required=True,
                    sensitive=False,
                    inject_into_auth_data=True,
                    sample_format="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://console.twilio.com",
                ),
                EnvVar(
                    name="TWILIO_AUTH_TOKEN",
                    display_name="Twilio Auth Token",
                    description="Your Twilio Auth Token from the Twilio Console",
                    required=True,
                    sensitive=True,
                    sample_format="your_auth_token",
                    about_url="https://console.twilio.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}.json",
                method="GET",
                auth=BasicAuthSpec(
                    username_placeholder="TWILIO_ACCOUNT_SID",
                    password_placeholder="TWILIO_AUTH_TOKEN",
                ),
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["sid"],
                ),
                cost_level="free",
                description="Validates the Account SID and Auth Token by fetching the account.",
            ),
        ),
    ],
)
