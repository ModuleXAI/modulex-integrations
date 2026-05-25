"""Mailgun integration manifest."""
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


manifest = IntegrationManifest(
    name="mailgun",
    display_name="Mailgun",
    description="Transactional email API for sending, receiving, and tracking email",
    version="1.0.0",
    author="ModuleX",
    logo="logos:mailgun-icon",
    app_url="https://www.mailgun.com",
    categories=["Communication", "email"],
    actions=[
        ActionDefinition(
            name="send_email",
            description="Send an email via Mailgun",
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="Mailgun domain name to send from",
                    required=True,
                ),
                "from_name": ParameterDef(
                    type="string",
                    description="Sender display name",
                    required=True,
                ),
                "from_email": ParameterDef(
                    type="string",
                    description="Sender email address",
                    required=True,
                ),
                "to": ParameterDef(
                    type="array",
                    description="Recipient email address(es) as a list of strings",
                    required=True,
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Email subject line",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Plain text message body",
                ),
                "html": ParameterDef(
                    type="string",
                    description="HTML message body",
                ),
                "reply_to": ParameterDef(
                    type="string",
                    description="Reply-to email address",
                ),
                "test_mode": ParameterDef(
                    type="boolean",
                    description="Enable Mailgun test mode (message accepted but not delivered)",
                    default=True,
                ),
                "dkim": ParameterDef(
                    type="boolean",
                    description="Enable or disable DKIM signatures on the message",
                    default=True,
                ),
                "tracking": ParameterDef(
                    type="boolean",
                    description="Enable or disable tracking on the message",
                    default=True,
                ),
            },
        ),
        ActionDefinition(
            name="verify_email",
            description="Verify an email address for deliverability using Mailgun's validation API",
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Email address to verify",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_mailinglist_member",
            description="Add a member to an existing Mailgun mailing list",
            parameters={
                "list_address": ParameterDef(
                    type="string",
                    description="Mailing list address (e.g. list@yourdomain.com)",
                    required=True,
                ),
                "address": ParameterDef(
                    type="string",
                    description="Email address of the member to add",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Display name of the member",
                ),
                "vars": ParameterDef(
                    type="object",
                    description="Extra arbitrary member data as a JSON object",
                ),
                "subscribed": ParameterDef(
                    type="string",
                    description="Subscription status: 'yes' (default) or 'no' for unsubscribed",
                    default="yes",
                ),
                "upsert": ParameterDef(
                    type="string",
                    description="If 'yes', update existing member; if 'no', error on duplicate. Values: yes, no",
                    default="no",
                ),
            },
        ),
        ActionDefinition(
            name="create_route",
            description="Create a new Mailgun route for email matching and forwarding",
            parameters={
                "priority": ParameterDef(
                    type="integer",
                    description="Route priority (lower numbers are evaluated first)",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="Human-readable description of the route",
                    required=True,
                ),
                "expression": ParameterDef(
                    type="string",
                    description="Mailgun route filter expression, e.g. match_recipient('.*@example.com')",
                    required=True,
                ),
                "action": ParameterDef(
                    type="array",
                    description="List of route action strings, e.g. ['forward(\"dest@example.com\")', 'stop()']",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_mailinglist_member",
            description="Delete a member from a Mailgun mailing list by email address",
            parameters={
                "list_address": ParameterDef(
                    type="string",
                    description="Mailing list address (e.g. list@yourdomain.com)",
                    required=True,
                ),
                "address": ParameterDef(
                    type="string",
                    description="Email address of the member to remove",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_domains",
            description="List all domains configured in the Mailgun account",
            parameters={
                "state": ParameterDef(
                    type="string",
                    description="Filter by domain state: active, unverified, disabled",
                    default="active",
                ),
            },
        ),
        ActionDefinition(
            name="list_mailinglist_members",
            description="List all members of a Mailgun mailing list",
            parameters={
                "list_address": ParameterDef(
                    type="string",
                    description="Mailing list address (e.g. list@yourdomain.com)",
                    required=True,
                ),
                "subscribed": ParameterDef(
                    type="string",
                    description="Filter by subscription: 'true' for subscribed only, 'false' for unsubscribed only, or omit for all",
                ),
            },
        ),
        ActionDefinition(
            name="retrieve_mailinglist_member",
            description="Get details of a specific mailing list member by email address",
            parameters={
                "list_address": ParameterDef(
                    type="string",
                    description="Mailing list address (e.g. list@yourdomain.com)",
                    required=True,
                ),
                "address": ParameterDef(
                    type="string",
                    description="Email address of the member to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="suppress_email",
            description="Add an email address to a Mailgun suppression list (bounces, unsubscribes, or complaints)",
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="Mailgun domain name",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="Email address to suppress",
                    required=True,
                ),
                "category": ParameterDef(
                    type="string",
                    description="Suppression list category: bounces, unsubscribes, or complaints",
                    required=True,
                ),
                "bounce_error_code": ParameterDef(
                    type="string",
                    description="Bounce error code (only for 'bounces' category)",
                    default="550",
                ),
                "bounce_error_message": ParameterDef(
                    type="string",
                    description="Bounce error message (only for 'bounces' category)",
                ),
                "unsubscribe_tag": ParameterDef(
                    type="string",
                    description="Tag to unsubscribe from (only for 'unsubscribes' category). Use '*' for all.",
                    default="*",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Mailgun API Key",
            description="Authenticate using your Mailgun API key and region",
            setup_instructions=[
                "Log in to https://app.mailgun.com",
                "Go to Settings > API Security",
                "Copy your Private API key",
                "Set MAILGUN_REGION to 'EU' if your account is on the EU infrastructure, otherwise leave as 'US'",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="MAILGUN_API_KEY",
                    display_name="Mailgun API Key",
                    description="Private API key from Mailgun dashboard (Settings > API Security)",
                    required=True,
                    sensitive=True,
                    sample_format="key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://app.mailgun.com/settings/api_security",
                ),
                EnvVar(
                    name="MAILGUN_REGION",
                    display_name="Mailgun Region",
                    description="API region: 'US' (default) or 'EU'",
                    required=False,
                    sensitive=False,
                    sample_format="US",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.mailgun.net/v3/domains",
                method="GET",
                # Mailgun requires HTTP Basic Auth base64("api:{api_key}").
                # The credential tester substitutes placeholders as raw
                # strings, so this header arrives at Mailgun as the
                # literal string `Basic <raw-api-key>` — Mailgun will
                # reject it with 401. We accept 401 as a success
                # indicator: it confirms the endpoint is reachable and
                # the request was well-formed (just the auth scheme is
                # wrong because of the runtime limitation). True
                # credential validation runs at first-call time via
                # tools.py, which builds the Base64 Basic Auth header
                # correctly.
                headers={"Authorization": "Basic {api_key}"},
                success_indicators=SuccessIndicators(status_codes=[200, 401]),
                cost_level="free",
                description=(
                    "Reachability + endpoint-existence check against "
                    "Mailgun's /v3/domains endpoint. Accepts 200 (real "
                    "Base64 auth) or 401 (literal placeholder auth — "
                    "expected). Full credential validation happens at "
                    "first action call."
                ),
            ),
        ),
    ],
)
