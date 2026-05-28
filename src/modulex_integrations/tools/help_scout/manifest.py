"""Help Scout integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="help_scout",
    display_name="Help Scout",
    description="Customer support helpdesk platform with shared inboxes, knowledge base, and live chat",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:help_scout-themed",
    app_url="https://www.helpscout.com",
    categories=["Customer Support", "Communication"],
    actions=[
        ActionDefinition(
            name="add_note",
            description="Adds a note to an existing conversation in Help Scout",
            parameters={
                "conversation_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the conversation",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="The content of the note",
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the user creating the note",
                ),
            },
        ),
        ActionDefinition(
            name="create_customer",
            description="Creates a new customer record in Help Scout",
            parameters={
                "first_name": ParameterDef(
                    type="string",
                    description="First name of the customer (1-40 characters)",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Last name of the customer (1-40 characters)",
                ),
                "phone": ParameterDef(
                    type="string",
                    description="Phone number for the new customer",
                ),
                "photo_url": ParameterDef(
                    type="string",
                    description="URL of the customer's photo (max 200 characters)",
                ),
                "job_title": ParameterDef(
                    type="string",
                    description="Job title (max 60 characters)",
                ),
                "photo_type": ParameterDef(
                    type="string",
                    description="Type of photo: unknown, gravatar, twitter, facebook, googleprofile, googleplus, linkedin, instagram",
                ),
                "background": ParameterDef(
                    type="string",
                    description="Notes field content (max 200 characters)",
                ),
                "location": ParameterDef(
                    type="string",
                    description="Location of the customer (max 60 characters)",
                ),
                "organization": ParameterDef(
                    type="string",
                    description="Organization name (max 60 characters)",
                ),
                "gender": ParameterDef(
                    type="string",
                    description="Gender: male, female, unknown",
                ),
                "age": ParameterDef(
                    type="string",
                    description="Customer's age",
                ),
                "emails": ParameterDef(
                    type="array",
                    description="List of email entries as JSON objects with 'type' and 'value' fields",
                ),
                "phones": ParameterDef(
                    type="array",
                    description="List of phone entries as JSON objects with 'type' and 'value' fields",
                ),
                "chats": ParameterDef(
                    type="array",
                    description="List of chat entries as JSON objects with 'type' and 'value' fields",
                ),
                "social_profiles": ParameterDef(
                    type="array",
                    description="List of social profile entries as JSON objects with 'type' and 'value' fields",
                ),
                "websites": ParameterDef(
                    type="array",
                    description="List of website entries as JSON objects with 'value' field",
                ),
                "address_city": ParameterDef(
                    type="string",
                    description="City of the customer's address",
                ),
                "address_state": ParameterDef(
                    type="string",
                    description="State of the customer's address",
                ),
                "address_postal_code": ParameterDef(
                    type="string",
                    description="Postal code of the customer's address",
                ),
                "address_country": ParameterDef(
                    type="string",
                    description="ISO 3166 Alpha-2 country code for the customer's address",
                ),
                "address_lines": ParameterDef(
                    type="array",
                    description="List of address line strings",
                ),
                "properties": ParameterDef(
                    type="array",
                    description="List of property entries as JSON objects",
                ),
            },
        ),
        ActionDefinition(
            name="get_conversation_details",
            description="Retrieves the details of a specific conversation",
            parameters={
                "conversation_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the conversation",
                    required=True,
                ),
                "embed": ParameterDef(
                    type="boolean",
                    description="If true, the response will include the threads of the conversation",
                ),
            },
        ),
        ActionDefinition(
            name="get_conversation_threads",
            description="Retrieves the threads of a specific conversation",
            parameters={
                "conversation_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the conversation",
                    required=True,
                ),
                "page": ParameterDef(
                    type="integer",
                    description="Page number to retrieve (25 threads per page)",
                    default=1,
                ),
            },
        ),
        ActionDefinition(
            name="get_tag_by_id",
            description="Gets a tag by its ID",
            parameters={
                "tag_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the tag",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_tags",
            description="Lists all tags in Help Scout",
            parameters={
                "page": ParameterDef(
                    type="integer",
                    description="The page number to return (defaults to 1)",
                    default=1,
                ),
            },
        ),
        ActionDefinition(
            name="send_reply",
            description="Sends a reply to a conversation (sends an actual email to the customer)",
            parameters={
                "conversation_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the conversation",
                    required=True,
                ),
                "customer_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the customer",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="The content of the reply",
                    required=True,
                ),
                "draft": ParameterDef(
                    type="boolean",
                    description="If true, a draft reply is created instead of sending",
                    default=False,
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_conversation",
            description="Updates a conversation using a specified operation",
            parameters={
                "conversation_id": ParameterDef(
                    type="string",
                    description="The unique identifier of the conversation",
                    required=True,
                ),
                "operation": ParameterDef(
                    type="string",
                    description="Operation to perform: Change subject, Change customer, Publish draft, Move conversation to another inbox, Change conversation status, Change conversation owner, Un-assign conversation",
                    required=True,
                ),
                "value": ParameterDef(
                    type="string",
                    description="Value for the operation (string for subject/status, number for customer/mailboxId/assignTo, 'true'/'false' for draft)",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Help Scout OAuth2 (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="HELP_SCOUT_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Help Scout OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://developer.helpscout.com/mailbox-api/overview/authentication/",
                ),
                EnvVar(
                    name="HELP_SCOUT_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Help Scout OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://developer.helpscout.com/mailbox-api/overview/authentication/",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://secure.helpscout.net/authentication/authorizeClientApplication",
                token_url="https://api.helpscout.net/v2/oauth2/token",
                scopes=[],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.helpscout.net/v2/users/me",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching the authenticated user",
            ),
        ),
    ],
)
