"""AgentPhone integration manifest.

AgentPhone is an API-first voice and messaging platform for AI agents:
provision real phone numbers, place outbound voice calls, send SMS /
MMS / iMessage, manage conversations and contacts, and track usage.

Auth is a single account-level API key sent as
``Authorization: Bearer <api_key>``, so this integration uses the
key-based runtime convention (``api_key`` is injected directly into each
``@tool`` function rather than an ``auth_type``/``auth_data`` pair).
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]

_API_BASE = "https://api.agentphone.ai/v1"
_TEST_HEADERS = {"Authorization": "Bearer {api_key}"}
_TEST_SUCCESS = SuccessIndicators(status_codes=[200], response_fields=["plan"])


# --- Reusable parameter definitions ----------------------------------------


def _limit(description: str) -> ParameterDef:
    return ParameterDef(type="integer", description=description)


def _offset() -> ParameterDef:
    return ParameterDef(type="integer", description="Number of results to skip (min 0)")


def _before() -> ParameterDef:
    return ParameterDef(
        type="string",
        description="Return messages received before this ISO 8601 timestamp",
    )


def _after() -> ParameterDef:
    return ParameterDef(
        type="string",
        description="Return messages received after this ISO 8601 timestamp",
    )


def _conversation_id() -> ParameterDef:
    return ParameterDef(type="string", description="Conversation ID", required=True)


def _contact_id() -> ParameterDef:
    return ParameterDef(type="string", description="Contact ID", required=True)


def _call_id(description: str) -> ParameterDef:
    return ParameterDef(type="string", description=description, required=True)


manifest = IntegrationManifest(
    name="agentphone",
    display_name="AgentPhone",
    description=(
        "Give your workflow a phone. Provision SMS- and voice-enabled numbers, "
        "send messages and tapback reactions, place outbound voice calls, manage "
        "conversations and contacts, and track usage — all through a single "
        "AgentPhone API key."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:agentphone-themed",
    app_url="https://agentphone.ai",
    categories=["Communication", "messaging", "voice", "telephony"],
    actions=[
        # --- Phone numbers -------------------------------------------------
        ActionDefinition(
            name="create_number",
            description="Provision a new SMS- and voice-enabled phone number.",
            parameters={
                "country": ParameterDef(
                    type="string",
                    description="Two-letter country code: 'US' or 'CA'. Defaults to US.",
                ),
                "area_code": ParameterDef(
                    type="string",
                    description=(
                        "Preferred area code (US/CA only, e.g. '415'). Best-effort — "
                        "may be ignored if unavailable."
                    ),
                ),
                "agent_id": ParameterDef(
                    type="string",
                    description="Optionally attach the number to an agent immediately",
                ),
            },
        ),
        ActionDefinition(
            name="list_numbers",
            description="List all phone numbers provisioned for this AgentPhone account.",
            parameters={
                "limit": _limit("Number of results to return (default 20, max 100)"),
                "offset": _offset(),
            },
        ),
        ActionDefinition(
            name="release_number",
            description="Release (delete) a phone number. This action is irreversible.",
            parameters={
                "number_id": ParameterDef(
                    type="string",
                    description="ID of the phone number to release",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_number_messages",
            description="Fetch messages received on a specific phone number.",
            parameters={
                "number_id": ParameterDef(
                    type="string",
                    description="ID of the phone number",
                    required=True,
                ),
                "limit": _limit("Number of messages to return (default 50, max 200)"),
                "before": _before(),
                "after": _after(),
            },
        ),
        # --- Calls ----------------------------------------------------------
        ActionDefinition(
            name="create_call",
            description="Initiate an outbound voice call from an AgentPhone agent.",
            parameters={
                "agent_id": ParameterDef(
                    type="string",
                    description="Agent that will handle the call",
                    required=True,
                ),
                "to_number": ParameterDef(
                    type="string",
                    description="Phone number to call in E.164 format (e.g. +14155551234)",
                    required=True,
                ),
                "from_number_id": ParameterDef(
                    type="string",
                    description=(
                        "Phone number ID to use as caller ID. Must belong to the agent. "
                        "If omitted, the agent's first assigned number is used."
                    ),
                ),
                "initial_greeting": ParameterDef(
                    type="string",
                    description="Greeting spoken when the recipient answers",
                ),
                "voice": ParameterDef(
                    type="string",
                    description=(
                        "Voice ID override for this call (defaults to the agent's "
                        "configured voice)"
                    ),
                ),
                "system_prompt": ParameterDef(
                    type="string",
                    description=(
                        "When provided, uses a built-in LLM for the conversation instead "
                        "of forwarding to your webhook"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="list_calls",
            description="List voice calls for this AgentPhone account.",
            parameters={
                "limit": _limit("Number of results to return (default 20, max 100)"),
                "offset": _offset(),
                "status": ParameterDef(
                    type="string",
                    description="Filter by status: completed, in-progress, or failed",
                ),
                "direction": ParameterDef(
                    type="string",
                    description="Filter by direction: inbound or outbound",
                ),
                "type": ParameterDef(
                    type="string",
                    description="Filter by call type: pstn or web",
                ),
                "search": ParameterDef(
                    type="string",
                    description="Search by phone number (matches fromNumber or toNumber)",
                ),
            },
        ),
        ActionDefinition(
            name="get_call",
            description="Fetch a call and its full transcript.",
            parameters={"call_id": _call_id("ID of the call to retrieve")},
        ),
        ActionDefinition(
            name="get_call_transcript",
            description="Get the full ordered transcript for a call.",
            parameters={
                "call_id": _call_id("ID of the call to retrieve the transcript for"),
            },
        ),
        # --- Conversations --------------------------------------------------
        ActionDefinition(
            name="list_conversations",
            description="List conversations (message threads) for this AgentPhone account.",
            parameters={
                "limit": _limit("Number of results to return (default 20, max 100)"),
                "offset": _offset(),
            },
        ),
        ActionDefinition(
            name="get_conversation",
            description="Get a conversation along with its recent messages.",
            parameters={
                "conversation_id": _conversation_id(),
                "message_limit": _limit(
                    "Number of recent messages to include (default 50, max 100)"
                ),
            },
        ),
        ActionDefinition(
            name="update_conversation",
            description=(
                "Update the custom metadata stored on a conversation. Set "
                "clear_metadata to erase the existing metadata."
            ),
            parameters={
                "conversation_id": _conversation_id(),
                "metadata": ParameterDef(
                    type="object",
                    description="Custom key-value metadata to store on the conversation",
                ),
                "clear_metadata": ParameterDef(
                    type="boolean",
                    description=(
                        "Set to true to erase the conversation's stored metadata "
                        "(takes precedence over 'metadata')"
                    ),
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_conversation_messages",
            description="Get paginated messages for a conversation.",
            parameters={
                "conversation_id": _conversation_id(),
                "limit": _limit("Number of messages to return (default 50, max 200)"),
                "before": _before(),
                "after": _after(),
            },
        ),
        # --- Messages -------------------------------------------------------
        ActionDefinition(
            name="send_message",
            description="Send an outbound SMS or iMessage from an AgentPhone agent.",
            parameters={
                "agent_id": ParameterDef(
                    type="string",
                    description="Agent sending the message",
                    required=True,
                ),
                "to_number": ParameterDef(
                    type="string",
                    description=(
                        "Recipient phone number in E.164 format (e.g. +14155551234)"
                    ),
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="Message text to send",
                    required=True,
                ),
                "media_url": ParameterDef(
                    type="string",
                    description=(
                        "Deprecated by the vendor — prefer media_urls. URL of a "
                        "single image, video, or file to attach"
                    ),
                ),
                "media_urls": ParameterDef(
                    type="array",
                    description=(
                        "Public HTTPS URLs to attach (2-20 URLs sends an iMessage "
                        "carousel; body must be empty for a carousel)"
                    ),
                ),
                "number_id": ParameterDef(
                    type="string",
                    description=(
                        "Phone number ID to send from. If omitted, the agent's first "
                        "assigned number is used."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="react_to_message",
            description="Send an iMessage tapback reaction to a message (iMessage only).",
            parameters={
                "message_id": ParameterDef(
                    type="string",
                    description="ID of the message to react to",
                    required=True,
                ),
                "reaction": ParameterDef(
                    type="string",
                    description=(
                        "Reaction type: love, like, dislike, laugh, emphasize, or question"
                    ),
                    required=True,
                ),
            },
        ),
        # --- Contacts -------------------------------------------------------
        ActionDefinition(
            name="create_contact",
            description="Create a new contact in AgentPhone.",
            parameters={
                "phone_number": ParameterDef(
                    type="string",
                    description="Phone number in E.164 format (e.g. +14155551234)",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Contact's full name",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="Contact's email address",
                ),
                "notes": ParameterDef(
                    type="string",
                    description="Freeform notes stored on the contact",
                ),
            },
        ),
        ActionDefinition(
            name="list_contacts",
            description="List contacts for this AgentPhone account.",
            parameters={
                "search": ParameterDef(
                    type="string",
                    description=(
                        "Filter by name or phone number (case-insensitive contains)"
                    ),
                ),
                "limit": _limit("Number of results to return (default 50, max 200)"),
                "offset": _offset(),
            },
        ),
        ActionDefinition(
            name="get_contact",
            description="Fetch a single contact by ID.",
            parameters={"contact_id": _contact_id()},
        ),
        ActionDefinition(
            name="update_contact",
            description="Update a contact's fields.",
            parameters={
                "contact_id": _contact_id(),
                "phone_number": ParameterDef(
                    type="string",
                    description="New phone number in E.164 format",
                ),
                "name": ParameterDef(type="string", description="New contact name"),
                "email": ParameterDef(type="string", description="New email address"),
                "notes": ParameterDef(type="string", description="New freeform notes"),
            },
        ),
        ActionDefinition(
            name="delete_contact",
            description="Delete a contact by ID.",
            parameters={"contact_id": _contact_id()},
        ),
        # --- Usage ----------------------------------------------------------
        ActionDefinition(
            name="get_usage",
            description="Retrieve current usage statistics for the AgentPhone account.",
            parameters={},
        ),
        ActionDefinition(
            name="get_usage_daily",
            description=(
                "Get a daily breakdown of usage (messages, calls, webhooks) for the "
                "last N days."
            ),
            parameters={
                "days": ParameterDef(
                    type="integer",
                    description="Number of days to return (1-365, default 30)",
                ),
            },
        ),
        ActionDefinition(
            name="get_usage_monthly",
            description=(
                "Get monthly usage aggregation (messages, calls, webhooks) for the "
                "last N months."
            ),
            parameters={
                "months": ParameterDef(
                    type="integer",
                    description="Number of months to return (1-24, default 6)",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your AgentPhone API key",
            setup_instructions=[
                "Sign up or log in at https://agentphone.ai",
                "Open the dashboard and navigate to the API Keys section",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="AGENTPHONE_API_KEY",
                    display_name="AgentPhone API Key",
                    description="Your AgentPhone account API key",
                    required=True,
                    sensitive=True,
                    about_url="https://docs.agentphone.ai/api-reference",
                ),
            ],
            test_endpoint=TestEndpoint(
                url=f"{_API_BASE}/usage",
                method="GET",
                headers=_TEST_HEADERS,
                success_indicators=_TEST_SUCCESS,
                cost_level="free",
                description="Validates the API key by reading account usage.",
            ),
        ),
    ],
)
