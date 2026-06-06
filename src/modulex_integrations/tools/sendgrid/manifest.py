"""SendGrid integration manifest."""
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


def _email_param(description: str) -> ParameterDef:
    return ParameterDef(type="string", description=description, required=True)


def _common_email_compose() -> dict[str, ParameterDef]:
    return {
        "from_email": _email_param("Sender email address (must be verified)"),
        "subject": ParameterDef(
            type="string", description="Email subject line", required=True
        ),
        "content": ParameterDef(
            type="string",
            description="Email body content (plain text or HTML)",
            required=True,
        ),
        "content_type": ParameterDef(
            type="string",
            description="Content type ('text/plain' or 'text/html')",
            default="text/plain",
        ),
        "from_name": ParameterDef(
            type="string", description="Sender display name"
        ),
    }


def _time_window_params() -> dict[str, ParameterDef]:
    return {
        "start_time": ParameterDef(
            type="integer", description="Start time as Unix timestamp"
        ),
        "end_time": ParameterDef(
            type="integer", description="End time as Unix timestamp"
        ),
    }


def _bulk_delete_params(item: str) -> dict[str, ParameterDef]:
    return {
        "emails": ParameterDef(
            type="array", description=f"Email addresses to remove from {item}"
        ),
        "delete_all": ParameterDef(
            type="boolean",
            description=f"Delete every {item} (use with caution)",
            default=False,
        ),
    }


manifest = IntegrationManifest(
    name="sendgrid",
    display_name="SendGrid",
    description=(
        "Email delivery and marketing platform for transactional and "
        "marketing emails. Send emails, manage contacts, create lists, "
        "and handle email suppressions."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:sendgrid-icon",
    app_url="https://sendgrid.com",
    categories=["Marketing & Advertising", "Marketing & Email", "email", "automation"],
    actions=[
        ActionDefinition(
            name="send_email",
            description="Send a single transactional email to one recipient",
            parameters={
                "to_email": _email_param("Recipient email address"),
                **_common_email_compose(),
                "to_name": ParameterDef(
                    type="string", description="Recipient display name"
                ),
                "reply_to_email": ParameterDef(
                    type="string", description="Reply-to email address"
                ),
                "cc_emails": ParameterDef(
                    type="array", description="CC email addresses"
                ),
                "bcc_emails": ParameterDef(
                    type="array", description="BCC email addresses"
                ),
            },
        ),
        ActionDefinition(
            name="send_email_multiple_recipients",
            description=(
                "Send the same email to multiple recipients individually "
                "(each recipient gets a separate copy)"
            ),
            parameters={
                "to_emails": ParameterDef(
                    type="array",
                    description="List of recipient email addresses",
                    required=True,
                ),
                **_common_email_compose(),
            },
        ),
        ActionDefinition(
            name="add_or_update_contact",
            description=(
                "Create a new contact or update an existing one (matched "
                "by email). Optionally adds to specified lists."
            ),
            parameters={
                "email": _email_param("Contact email address"),
                "first_name": ParameterDef(
                    type="string", description="Contact's first name"
                ),
                "last_name": ParameterDef(
                    type="string", description="Contact's last name"
                ),
                "address_line_1": ParameterDef(
                    type="string", description="First line of address"
                ),
                "address_line_2": ParameterDef(
                    type="string", description="Second line of address"
                ),
                "city": ParameterDef(
                    type="string", description="Contact's city"
                ),
                "state_province_region": ParameterDef(
                    type="string", description="State, province, or region"
                ),
                "postal_code": ParameterDef(
                    type="string", description="ZIP or postal code"
                ),
                "country": ParameterDef(
                    type="string", description="Contact's country"
                ),
                "alternate_emails": ParameterDef(
                    type="array", description="Additional email addresses"
                ),
                "list_ids": ParameterDef(
                    type="array", description="List IDs to add the contact to"
                ),
                "custom_fields": ParameterDef(
                    type="object", description="Custom field values"
                ),
            },
        ),
        ActionDefinition(
            name="search_contacts",
            description="Search contacts using SendGrid Query Language (SGQL)",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description=(
                        "SGQL query (e.g. \"email LIKE 'test%'\" or "
                        "\"first_name='John'\")"
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_contact_list",
            description="Create a new contact list",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Name for the new list (max 100 characters)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_contact_lists",
            description="Get all contact lists with their IDs and counts",
            parameters={
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of lists to return (max 1000)",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="remove_contact_from_list",
            description="Remove contacts from a list (does not delete them)",
            parameters={
                "list_id": ParameterDef(
                    type="string",
                    description="ID of the list",
                    required=True,
                ),
                "contact_ids": ParameterDef(
                    type="array",
                    description="Contact IDs to remove",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_contacts",
            description="Permanently delete specified contacts (or all)",
            parameters={
                "contact_ids": ParameterDef(
                    type="array", description="Contact IDs to delete"
                ),
                "delete_all": ParameterDef(
                    type="boolean",
                    description="Delete every contact (use with caution)",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="add_email_to_global_suppression",
            description="Add emails to the global suppression group",
            parameters={
                "recipient_emails": ParameterDef(
                    type="array",
                    description="Email addresses to suppress",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_global_suppression",
            description="Remove an email from the global suppression group",
            parameters={
                "email": _email_param("Email address to remove"),
            },
        ),
        ActionDefinition(
            name="list_global_suppressions",
            description="List all globally suppressed (unsubscribed) emails",
            parameters={
                **_time_window_params(),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="get_all_bounces",
            description="Get all bounced email addresses",
            parameters=_time_window_params(),
        ),
        ActionDefinition(
            name="delete_bounces",
            description="Remove emails from the bounces list",
            parameters=_bulk_delete_params("bounce"),
        ),
        ActionDefinition(
            name="list_blocks",
            description="List all blocked email addresses",
            parameters={
                **_time_window_params(),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="delete_blocks",
            description="Remove emails from the blocks list",
            parameters=_bulk_delete_params("block"),
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description=(
                "Authenticate using your SendGrid API key. Create one in "
                "Settings > API Keys."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="SENDGRID_API_KEY",
                    display_name="SendGrid API Key",
                    description="Your SendGrid API key for API authentication",
                    required=True,
                    sensitive=True,
                    sample_format="SG.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                    about_url="https://app.sendgrid.com/settings/api_keys",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.sendgrid.com/v3/marketing/lists",
                method="GET",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "Accept": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["result"]
                ),
                cost_level="minimal",
                description="Validates API Key by listing marketing lists",
            ),
        ),
    ],
)
