"""Lemlist integration manifest.

Declares the Lemlist tool's actions, parameters, and the single
API-key (BYOK) credential schema the modulex runtime uses to drive
credential UI, validation, and tool discovery.
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
    name="lemlist",
    display_name="Lemlist",
    description=(
        "Integrate Lemlist into your workflow. Retrieve campaign activities "
        "and replies, get lead information, and send emails through the "
        "Lemlist inbox."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:lemlist-themed",
    app_url="https://www.lemlist.com",
    categories=["Sales", "email-marketing", "sales-engagement"],
    actions=[
        ActionDefinition(
            name="get_activities",
            description=(
                "Retrieves campaign activities and steps performed, including "
                "email opens, clicks, replies, and other events."
            ),
            parameters={
                "type": ParameterDef(
                    type="string",
                    description=(
                        "Filter by activity type (e.g., emailOpened, emailClicked, "
                        "emailReplied, paused)"
                    ),
                ),
                "campaign_id": ParameterDef(
                    type="string",
                    description='Filter by campaign ID (e.g., "cam_abc123def456")',
                ),
                "lead_id": ParameterDef(
                    type="string",
                    description='Filter by lead ID (e.g., "lea_abc123def456")',
                ),
                "is_first": ParameterDef(
                    type="boolean",
                    description="Filter for first activity only",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Number of results per request (max 100, default 100)",
                ),
                "offset": ParameterDef(
                    type="integer",
                    description="Number of records to skip for pagination (e.g., 0, 100, 200)",
                ),
            },
        ),
        ActionDefinition(
            name="get_lead",
            description="Retrieves lead information by email address or lead ID.",
            parameters={
                "lead_identifier": ParameterDef(
                    type="string",
                    description=(
                        'Lead email address (e.g., "john@example.com") or lead ID '
                        '(e.g., "lea_abc123def456")'
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="send_email",
            description="Sends an email to a contact through the Lemlist inbox.",
            parameters={
                "send_user_id": ParameterDef(
                    type="string",
                    description=(
                        'Identifier for the user sending the message '
                        '(e.g., "usr_abc123def456")'
                    ),
                    required=True,
                ),
                "send_user_email": ParameterDef(
                    type="string",
                    description='Email address of the sender (e.g., "sales@company.com")',
                    required=True,
                ),
                "send_user_mailbox_id": ParameterDef(
                    type="string",
                    description='Mailbox identifier for the sender (e.g., "mbx_abc123def456")',
                    required=True,
                ),
                "contact_id": ParameterDef(
                    type="string",
                    description='Recipient contact identifier (e.g., "con_abc123def456")',
                    required=True,
                ),
                "lead_id": ParameterDef(
                    type="string",
                    description='Associated lead identifier (e.g., "lea_abc123def456")',
                    required=True,
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Email subject line",
                    required=True,
                ),
                "message": ParameterDef(
                    type="string",
                    description="Email message body in HTML format",
                    required=True,
                ),
                "cc": ParameterDef(
                    type="array",
                    description="Array of CC email addresses",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Lemlist API key",
            setup_instructions=[
                "Sign in to Lemlist and open Settings -> Team Settings -> Integrations",
                "Generate an API key (it is shown only once — copy it immediately)",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="LEMLIST_API_KEY",
                    display_name="Lemlist API Key",
                    description="Your Lemlist API key from Team Settings -> Integrations",
                    required=True,
                    sensitive=True,
                    about_url="https://help.lemlist.com/en/articles/4452694-find-and-use-the-lemlist-api",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.lemlist.com/api/team",
                method="GET",
                auth=BasicAuthSpec(
                    username_placeholder="",
                    password_placeholder="api_key",
                ),
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description="Validates the API key by fetching the authenticated team",
            ),
        ),
    ],
)
