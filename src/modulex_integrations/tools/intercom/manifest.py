"""Intercom integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    BearerTokenAuthSchema,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


def _me_test_endpoint(
    placeholder: str, description: str, url: str = "https://api.intercom.io/me"
) -> TestEndpoint:
    # The credential test uses the US default endpoint
    # (api.intercom.io/me) regardless of the user's eventual data region.
    # Reason: INTERCOM_API_BASE_URL is now optional and may be empty —
    # in which case the placeholder substitution would leave a broken
    # URL. The OAuth token validates against any Intercom region, and
    # tools.py uses the user-supplied base URL at action call time, so
    # this hardcoded test URL is purely for credential validation.
    return TestEndpoint(
        url=url,
        method="GET",
        headers={
            "Authorization": f"Bearer {{{placeholder}}}",
            "Accept": "application/json",
            "Intercom-Version": "2.12",
        },
        success_indicators=SuccessIndicators(
            status_codes=[200], response_fields=["id", "type"]
        ),
        cost_level="free",
        description=description,
    )


manifest = IntegrationManifest(
    name="intercom",
    display_name="Intercom",
    description=(
        "Customer communication platform for support, engagement, and "
        "marketing automation."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:intercom-themed",
    app_url="https://www.intercom.com",
    categories=["Customer Support", "CRM & Customer", "communication", "automation", "development"],
    actions=[
        ActionDefinition(
            name="get_contact",
            description="Get a contact by their unique Intercom ID",
            parameters={
                "contact_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the contact",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_contacts",
            description="Search for contacts using various fields and operators",
            parameters={
                "query_field": ParameterDef(
                    type="string",
                    description="Field to search by (email, name, phone, role, external_id, etc.)",
                    default="email",
                ),
                "query_operator": ParameterDef(
                    type="string",
                    description="Query operator (=, !=, >, <, ~, !~, IN, NIN)",
                    default="=",
                ),
                "query_value": ParameterDef(
                    type="string",
                    description="Value to search for",
                    required=True,
                ),
                "per_page": ParameterDef(
                    type="integer",
                    description="Results per page (max 150)",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="upsert_contact",
            description=(
                "Create a new contact or update an existing one by email. "
                "Searches first; on match it PUTs, otherwise it POSTs."
            ),
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="The contact's email address",
                    required=True,
                ),
                "role": ParameterDef(
                    type="string", description="Role of the contact ('user' or 'lead')"
                ),
                "external_id": ParameterDef(
                    type="string",
                    description="A unique identifier from your system",
                ),
                "phone": ParameterDef(
                    type="string", description="The contact's phone number"
                ),
                "name": ParameterDef(
                    type="string", description="The contact's name"
                ),
                "avatar": ParameterDef(
                    type="string", description="URL of the avatar image"
                ),
                "unsubscribed_from_emails": ParameterDef(
                    type="boolean",
                    description="Whether the contact is unsubscribed from emails",
                ),
                "custom_attributes": ParameterDef(
                    type="object", description="Custom attributes for the contact"
                ),
            },
        ),
        ActionDefinition(
            name="create_note",
            description=(
                "Create a note on a contact's record. Auto-attributes the "
                "note to the authenticated admin (via a side GET to /me)."
            ),
            parameters={
                "contact_id": ParameterDef(
                    type="string",
                    description="The contact's unique Intercom identifier",
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="The note content (supports HTML)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="add_tag_to_contact",
            description="Add a tag to a contact",
            parameters={
                "contact_id": ParameterDef(
                    type="string",
                    description="The contact's unique Intercom identifier",
                    required=True,
                ),
                "tag_id": ParameterDef(
                    type="string",
                    description="The tag's unique identifier",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_tags",
            description="List all tags in the Intercom workspace",
            parameters={},
        ),
        ActionDefinition(
            name="list_admins",
            description="List all admins/teammates in the Intercom workspace",
            parameters={},
        ),
        ActionDefinition(
            name="get_conversation",
            description="Get a conversation by its unique ID",
            parameters={
                "conversation_id": ParameterDef(
                    type="string",
                    description="The conversation's unique identifier",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_conversations",
            description="List conversations in the Intercom workspace",
            parameters={
                "per_page": ParameterDef(
                    type="integer",
                    description="Conversations per page (max 150)",
                    default=20,
                ),
                "starting_after": ParameterDef(
                    type="string",
                    description="Pagination cursor from previous response",
                ),
            },
        ),
        ActionDefinition(
            name="search_conversations",
            description="Search for conversations using various fields and operators",
            parameters={
                "query_field": ParameterDef(
                    type="string",
                    description="Field to search by (created_at, state, source.type, etc.)",
                    default="created_at",
                ),
                "query_operator": ParameterDef(
                    type="string",
                    description="Query operator (=, !=, >, <, IN, NIN)",
                    default=">",
                ),
                "query_value": ParameterDef(
                    type="string",
                    description="Value to search for (timestamp for date fields)",
                    required=True,
                ),
                "per_page": ParameterDef(
                    type="integer",
                    description="Results per page (max 150)",
                    default=20,
                ),
            },
        ),
        ActionDefinition(
            name="send_incoming_message",
            description=(
                "Send a message from a user to start a conversation. "
                "Auto-detects the contact's role via a side GET."
            ),
            parameters={
                "contact_id": ParameterDef(
                    type="string",
                    description="The contact's unique Intercom identifier",
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="The message content",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="send_message_to_contact",
            description="Send a message from an admin to a contact",
            parameters={
                "from_admin_id": ParameterDef(
                    type="string",
                    description="The admin's unique identifier",
                    required=True,
                ),
                "to_contact_id": ParameterDef(
                    type="string",
                    description="The contact's unique identifier",
                    required=True,
                ),
                "to_type": ParameterDef(
                    type="string",
                    description="Recipient type ('user' or 'lead')",
                    default="user",
                ),
                "message_type": ParameterDef(
                    type="string",
                    description="Message type ('in_app' or 'email')",
                    default="in_app",
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Subject/title of the message",
                    required=True,
                ),
                "body": ParameterDef(
                    type="string",
                    description="Message content (HTML and plaintext supported)",
                    required=True,
                ),
                "template": ParameterDef(
                    type="string",
                    description="Template style ('plain' or 'personal')",
                    default="personal",
                ),
            },
        ),
        ActionDefinition(
            name="reply_to_conversation",
            description="Reply to an existing conversation",
            parameters={
                "conversation_id": ParameterDef(
                    type="string",
                    description="The conversation's unique identifier",
                    required=True,
                ),
                "reply_type": ParameterDef(
                    type="string",
                    description="Type of reply ('user' or 'admin')",
                    required=True,
                ),
                "message_type": ParameterDef(
                    type="string",
                    description="Message type ('comment' or 'note', note only for admin)",
                    default="comment",
                ),
                "body": ParameterDef(
                    type="string",
                    description="The reply content",
                    required=True,
                ),
                "admin_id": ParameterDef(
                    type="string",
                    description="Admin ID (required if reply_type is 'admin')",
                ),
                "intercom_user_id": ParameterDef(
                    type="string",
                    description="Intercom user ID (for user reply)",
                ),
                "attachment_urls": ParameterDef(
                    type="array",
                    description="List of image URLs to attach (max 10)",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Intercom OAuth (recommended for production use)",
            setup_environment_variables=[
                EnvVar(
                    name="INTERCOM_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Your Intercom OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                ),
                EnvVar(
                    name="INTERCOM_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Your Intercom OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                ),
                EnvVar(
                    name="INTERCOM_API_BASE_URL",
                    display_name="API Base URL",
                    description=(
                        "Intercom API base URL (optional — leave empty for "
                        "https://api.intercom.io US default). Set to "
                        "https://api.eu.intercom.io for EU workspaces or "
                        "https://api.au.intercom.io for Australia."
                    ),
                    required=False,
                    sensitive=False,
                    sample_format="https://api.intercom.io",
                    about_url="https://developers.intercom.com/docs/build-an-integration/learn-more/rest-apis/api-base-urls/",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://app.intercom.com/oauth",
                token_url="https://api.intercom.io/auth/eagle/token",
                scopes=[],
                token_auth_method="body",
            ),
            test_endpoint=_me_test_endpoint(
                "access_token",
                "Validates OAuth token by fetching authenticated admin info",
            ),
        ),
        BearerTokenAuthSchema(
            display_name="Access Token",
            description="Use your Intercom Access Token for direct authentication",
            setup_environment_variables=[
                EnvVar(
                    name="INTERCOM_ACCESS_TOKEN",
                    display_name="Access Token",
                    description="Your Intercom Access Token",
                    required=True,
                    sensitive=True,
                    sample_format="dG9rOjxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                ),
                EnvVar(
                    name="INTERCOM_API_BASE_URL",
                    display_name="API Base URL",
                    description=(
                        "Intercom API base URL (optional — leave empty for "
                        "https://api.intercom.io US default). Set to "
                        "https://api.eu.intercom.io for EU workspaces or "
                        "https://api.au.intercom.io for Australia."
                    ),
                    required=False,
                    sensitive=False,
                    sample_format="https://api.intercom.io",
                    about_url="https://developers.intercom.com/docs/build-an-integration/learn-more/rest-apis/api-base-urls/",
                ),
            ],
            test_endpoint=_me_test_endpoint(
                "bearer_token",
                "Validates Access Token by fetching authenticated admin info",
            ),
        ),
    ],
)
