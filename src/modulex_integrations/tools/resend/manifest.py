"""Resend integration manifest.

Resend is a developer-focused email API for sending transactional and
marketing email and managing contacts and domains. Authentication uses a
single Resend API key sent as ``Authorization: Bearer <api_key>``.
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


manifest = IntegrationManifest(
    name="resend",
    display_name="Resend",
    description=(
        "Send transactional and marketing emails, retrieve email status, "
        "manage contacts, and view domains with Resend."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:resend-themed",
    app_url="https://resend.com",
    categories=["Communication", "email", "email-marketing"],
    actions=[
        ActionDefinition(
            name="send",
            description="Send an email using your Resend API key and from address.",
            parameters={
                "from_address": ParameterDef(
                    type="string",
                    description=(
                        'Email address to send from (e.g. "sender@example.com" or '
                        '"Sender Name <sender@example.com>")'
                    ),
                    required=True,
                ),
                "to": ParameterDef(
                    type="string",
                    description=(
                        'Recipient email address (e.g. "recipient@example.com" or '
                        '"Recipient Name <recipient@example.com>")'
                    ),
                    required=True,
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Email subject line",
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="Email body content (plain text or HTML based on content_type)",
                    required=True,
                ),
                "content_type": ParameterDef(
                    type="string",
                    description='Content type for the body: "text" for plain text or "html"',
                    default="text",
                ),
                "cc": ParameterDef(
                    type="string",
                    description="Carbon copy recipient email address",
                ),
                "bcc": ParameterDef(
                    type="string",
                    description="Blind carbon copy recipient email address",
                ),
                "reply_to": ParameterDef(
                    type="string",
                    description="Reply-to email address",
                ),
                "scheduled_at": ParameterDef(
                    type="string",
                    description="Schedule email to be sent later in ISO 8601 format",
                ),
                "tags": ParameterDef(
                    type="string",
                    description=(
                        'Comma-separated key:value pairs for email tags '
                        '(e.g. "category:welcome,type:onboarding")'
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="get_email",
            description="Retrieve details of a previously sent email by its ID.",
            parameters={
                "email_id": ParameterDef(
                    type="string",
                    description="The ID of the email to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_contact",
            description="Create a new contact in Resend.",
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Email address of the contact",
                    required=True,
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="First name of the contact",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Last name of the contact",
                ),
                "unsubscribed": ParameterDef(
                    type="boolean",
                    description="Whether the contact is unsubscribed from all broadcasts",
                ),
            },
        ),
        ActionDefinition(
            name="list_contacts",
            description="List all contacts in Resend.",
            parameters={},
        ),
        ActionDefinition(
            name="get_contact",
            description="Retrieve details of a contact by ID or email.",
            parameters={
                "contact_id": ParameterDef(
                    type="string",
                    description="The contact ID or email address to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_contact",
            description="Update an existing contact in Resend.",
            parameters={
                "contact_id": ParameterDef(
                    type="string",
                    description="The contact ID or email address to update",
                    required=True,
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="Updated first name",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Updated last name",
                ),
                "unsubscribed": ParameterDef(
                    type="boolean",
                    description="Whether the contact should be unsubscribed from all broadcasts",
                ),
            },
        ),
        ActionDefinition(
            name="delete_contact",
            description="Delete a contact from Resend by ID or email.",
            parameters={
                "contact_id": ParameterDef(
                    type="string",
                    description="The contact ID or email address to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_domains",
            description="List all domains in your Resend account.",
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Resend API key",
            setup_instructions=[
                "Go to https://resend.com and sign up or log in",
                "Navigate to the 'API Keys' section in the dashboard",
                "Create a new API key (it starts with 're_')",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="RESEND_API_KEY",
                    display_name="Resend API Key",
                    description="Your Resend API key from resend.com/api-keys",
                    required=True,
                    sensitive=True,
                    sample_format="re_xxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://resend.com/api-keys",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.resend.com/domains",
                method="GET",
                headers={"Authorization": "Bearer {api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates the API key by listing domains.",
            ),
        ),
    ],
)
