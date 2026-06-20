"""Loops integration manifest.

Loops uses the modulex *api_key* runtime convention: each ``@tool``
takes ``api_key: str`` directly and presents it as
``Authorization: Bearer <api_key>``. Exactly one auth schema is
shipped — ``ApiKeyAuthSchema`` (bring-your-own-key).
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


# Shared parameter definitions reused across multiple actions.
_EMAIL_OPTIONAL = ParameterDef(
    type="string",
    description="The contact email address (at least one of email or user_id is required)",
)
_USER_ID_OPTIONAL = ParameterDef(
    type="string",
    description="The contact userId (at least one of email or user_id is required)",
)
_FIRST_NAME = ParameterDef(type="string", description="The contact first name")
_LAST_NAME = ParameterDef(type="string", description="The contact last name")
_SOURCE = ParameterDef(
    type="string", description='Custom source value replacing the default "API"'
)
_USER_GROUP = ParameterDef(
    type="string", description="Group to segment the contact into (one group per contact)"
)
_MAILING_LISTS = ParameterDef(
    type="object",
    description=(
        "Mailing list IDs mapped to boolean values "
        "(true to subscribe, false to unsubscribe)"
    ),
)


manifest = IntegrationManifest(
    name="loops",
    display_name="Loops",
    description=(
        "Integrate Loops into the workflow. Create and manage contacts, send "
        "transactional emails, and trigger event-based automations."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:loops",
    app_url="https://loops.so",
    categories=["Marketing & Advertising", "email-marketing", "automation"],
    actions=[
        ActionDefinition(
            name="create_contact",
            description=(
                "Create a new contact in your Loops audience with an email address "
                "and optional properties like name, user group, and mailing list "
                "subscriptions."
            ),
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="The email address for the new contact",
                    required=True,
                ),
                "first_name": _FIRST_NAME,
                "last_name": _LAST_NAME,
                "source": _SOURCE,
                "subscribed": ParameterDef(
                    type="boolean",
                    description="Whether the contact receives campaign emails (defaults to true)",
                ),
                "user_group": _USER_GROUP,
                "user_id": ParameterDef(
                    type="string",
                    description="Unique user identifier from your application",
                ),
                "mailing_lists": _MAILING_LISTS,
                "custom_properties": ParameterDef(
                    type="object",
                    description=(
                        "Custom contact properties as key-value pairs "
                        "(string, number, boolean, or date values)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="update_contact",
            description=(
                "Update an existing contact in Loops by email or userId. Creates a new "
                "contact if no match is found (upsert). Can update name, subscription "
                "status, user group, mailing lists, and custom properties."
            ),
            parameters={
                "email": _EMAIL_OPTIONAL,
                "user_id": _USER_ID_OPTIONAL,
                "first_name": _FIRST_NAME,
                "last_name": _LAST_NAME,
                "source": _SOURCE,
                "subscribed": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether the contact receives campaign emails "
                        "(sending true re-subscribes unsubscribed contacts)"
                    ),
                ),
                "user_group": _USER_GROUP,
                "mailing_lists": _MAILING_LISTS,
                "custom_properties": ParameterDef(
                    type="object",
                    description=(
                        "Custom contact properties as key-value pairs "
                        "(send null to reset a property)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="find_contact",
            description=(
                "Find a contact in Loops by email address or userId. Returns an array of "
                "matching contacts with all their properties including name, subscription "
                "status, user group, and mailing lists."
            ),
            parameters={
                "email": ParameterDef(
                    type="string",
                    description=(
                        "The contact email address to search for "
                        "(at least one of email or user_id is required)"
                    ),
                ),
                "user_id": ParameterDef(
                    type="string",
                    description=(
                        "The contact userId to search for "
                        "(at least one of email or user_id is required)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="delete_contact",
            description=(
                "Delete a contact from Loops by email address or userId. At least one "
                "identifier must be provided."
            ),
            parameters={
                "email": ParameterDef(
                    type="string",
                    description=(
                        "The email address of the contact to delete "
                        "(at least one of email or user_id is required)"
                    ),
                ),
                "user_id": ParameterDef(
                    type="string",
                    description=(
                        "The userId of the contact to delete "
                        "(at least one of email or user_id is required)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="send_transactional_email",
            description=(
                "Send a transactional email to a recipient using a Loops template. "
                "Supports dynamic data variables for personalization and optionally adds "
                "the recipient to your audience."
            ),
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="The email address of the recipient",
                    required=True,
                ),
                "transactional_id": ParameterDef(
                    type="string",
                    description="The ID of the transactional email template to send",
                    required=True,
                ),
                "data_variables": ParameterDef(
                    type="object",
                    description=(
                        "Template data variables as key-value pairs "
                        "(string or number values)"
                    ),
                ),
                "add_to_audience": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether to create the recipient as a contact if they do not "
                        "already exist (default: false)"
                    ),
                ),
                "attachments": ParameterDef(
                    type="array",
                    description=(
                        "Array of file attachments. Each object must have filename "
                        "(string), contentType (MIME type string), and data "
                        "(base64-encoded string)."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="send_event",
            description=(
                "Send an event to Loops to trigger automated email sequences for a "
                "contact. Identify the contact by email or userId and include optional "
                "event properties and mailing list changes."
            ),
            parameters={
                "event_name": ParameterDef(
                    type="string",
                    description="The name of the event to trigger",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description=(
                        "The email address of the contact "
                        "(at least one of email or user_id is required)"
                    ),
                ),
                "user_id": ParameterDef(
                    type="string",
                    description=(
                        "The userId of the contact "
                        "(at least one of email or user_id is required)"
                    ),
                ),
                "event_properties": ParameterDef(
                    type="object",
                    description=(
                        "Event data as key-value pairs "
                        "(string, number, boolean, or date values)"
                    ),
                ),
                "mailing_lists": _MAILING_LISTS,
            },
        ),
        ActionDefinition(
            name="list_mailing_lists",
            description=(
                "Retrieve all mailing lists from your Loops account. Returns each list "
                "with its ID, name, description, and public/private status."
            ),
            parameters={},
        ),
        ActionDefinition(
            name="list_transactional_emails",
            description=(
                "Retrieve a list of published transactional email templates from your "
                "Loops account. Returns each template with its ID, name, last updated "
                "timestamp, and data variables."
            ),
            parameters={
                "per_page": ParameterDef(
                    type="string",
                    description="Number of results per page (10-50, default: 20)",
                ),
                "cursor": ParameterDef(
                    type="string",
                    description=(
                        "Pagination cursor from a previous response to fetch the next page"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="create_contact_property",
            description=(
                "Create a new custom contact property in your Loops account. The property "
                "name must be in camelCase format."
            ),
            parameters={
                "name": ParameterDef(
                    type="string",
                    description='The property name in camelCase format (e.g., "favoriteColor")',
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description=(
                        'The property data type (e.g., "string", "number", '
                        '"boolean", "date")'
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_contact_properties",
            description=(
                "Retrieve a list of contact properties from your Loops account. Returns "
                "each property with its key, label, and data type. Can filter to show all "
                "properties or only custom ones."
            ),
            parameters={
                "list": ParameterDef(
                    type="string",
                    description=(
                        'Filter type: "all" for all properties (default) or '
                        '"custom" for custom properties only'
                    ),
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Loops API key",
            setup_instructions=[
                "Log in to your Loops account at https://app.loops.so",
                "Go to Settings > API",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="LOOPS_API_KEY",
                    display_name="Loops API Key",
                    description="Your Loops API key from Settings > API",
                    required=True,
                    sensitive=True,
                    about_url="https://loops.so/docs/api-reference",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://app.loops.so/api/v1/lists",
                method="GET",
                headers={"Authorization": "Bearer {api_key}"},
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description="Validates the API key by listing mailing lists",
            ),
        ),
    ],
)
