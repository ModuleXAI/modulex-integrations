"""Gmail integration manifest."""
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


def _profile_test_endpoint(placeholder: str, description: str) -> TestEndpoint:
    return TestEndpoint(
        url="https://www.googleapis.com/gmail/v1/users/me/profile",
        method="GET",
        headers={"Authorization": f"Bearer {{{placeholder}}}"},
        success_indicators=SuccessIndicators(
            status_codes=[200], response_fields=["emailAddress"]
        ),
        cost_level="free",
        description=description,
    )


def _message_id_param() -> ParameterDef:
    return ParameterDef(
        type="string", description="The ID of the message", required=True
    )


def _email_compose_params() -> dict[str, ParameterDef]:
    return {
        "to": ParameterDef(
            type="string", description="Recipient email address", required=True
        ),
        "subject": ParameterDef(
            type="string", description="Email subject line", required=True
        ),
        "body": ParameterDef(
            type="string", description="Email body content", required=True
        ),
        "cc": ParameterDef(
            type="string", description="CC recipients (comma-separated)"
        ),
        "bcc": ParameterDef(
            type="string", description="BCC recipients (comma-separated)"
        ),
        "is_html": ParameterDef(
            type="boolean",
            description="Whether the body is HTML content",
            default=False,
        ),
    }


manifest = IntegrationManifest(
    name="gmail",
    display_name="Gmail",
    description=(
        "Google Gmail email service for sending, reading, and managing "
        "emails."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:google-gmail",
    app_url="https://mail.google.com",
    categories=["Communication", "Communication & Collaboration", "email", "productivity"],
    actions=[
        ActionDefinition(
            name="send_message",
            description="Send a new email via Gmail",
            parameters=_email_compose_params(),
        ),
        ActionDefinition(
            name="read_message",
            description="Read a specific email message by ID",
            parameters={
                "message_id": _message_id_param(),
                "format": ParameterDef(
                    type="string",
                    description="Message format ('minimal', 'full', 'raw', 'metadata')",
                    default="full",
                ),
            },
        ),
        ActionDefinition(
            name="search_messages",
            description="Search emails using Gmail query syntax",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Gmail search query (e.g. 'from:user@x.io', 'is:unread')",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum messages to return (max 500)",
                    default=10,
                ),
                "page_token": ParameterDef(
                    type="string", description="Token for pagination"
                ),
                "label_ids": ParameterDef(
                    type="array", description="Filter by label IDs"
                ),
            },
        ),
        ActionDefinition(
            name="list_messages",
            description="List emails from specified folders/labels",
            parameters={
                "label_ids": ParameterDef(
                    type="array",
                    description="Label IDs to list (e.g. ['INBOX'], ['SENT'])",
                    default=["INBOX"],
                ),
                "query": ParameterDef(
                    type="string",
                    description="Gmail search query for filtering",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum messages to return",
                    default=20,
                ),
                "page_token": ParameterDef(
                    type="string", description="Token for pagination"
                ),
                "include_spam_trash": ParameterDef(
                    type="boolean",
                    description="Include messages from SPAM and TRASH",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="create_draft",
            description="Create an email draft",
            parameters=_email_compose_params(),
        ),
        ActionDefinition(
            name="mark_as_read",
            description="Mark an email as read",
            parameters={"message_id": _message_id_param()},
        ),
        ActionDefinition(
            name="mark_as_unread",
            description="Mark an email as unread",
            parameters={"message_id": _message_id_param()},
        ),
        ActionDefinition(
            name="archive_message",
            description="Archive an email (remove from inbox)",
            parameters={"message_id": _message_id_param()},
        ),
        ActionDefinition(
            name="unarchive_message",
            description="Move an archived email back to inbox",
            parameters={"message_id": _message_id_param()},
        ),
        ActionDefinition(
            name="delete_message",
            description="Move an email to trash",
            parameters={"message_id": _message_id_param()},
        ),
        ActionDefinition(
            name="add_label",
            description="Add labels to an email",
            parameters={
                "message_id": _message_id_param(),
                "label_ids": ParameterDef(
                    type="array", description="Label IDs to add", required=True
                ),
            },
        ),
        ActionDefinition(
            name="remove_label",
            description="Remove labels from an email",
            parameters={
                "message_id": _message_id_param(),
                "label_ids": ParameterDef(
                    type="array", description="Label IDs to remove", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_labels",
            description="List all available Gmail labels",
            parameters={},
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description=(
                "Connect using Google OAuth2 (recommended). Provides secure "
                "access to Gmail."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="GMAIL_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth2 Client ID from Google Cloud Console",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="123456789-xxxxxxxxxxxxxxxx.apps.googleusercontent.com",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GMAIL_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google OAuth2 Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scopes=[
                    "https://www.googleapis.com/auth/gmail.send",
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.modify",
                    "https://www.googleapis.com/auth/gmail.labels",
                ],
                token_auth_method="body",
            ),
            test_endpoint=_profile_test_endpoint(
                "access_token",
                "Validates OAuth token by fetching Gmail profile information",
            ),
        ),
        BearerTokenAuthSchema(
            display_name="Service Account / Access Token",
            description=(
                "Use a pre-generated access token or service account "
                "credentials"
            ),
            setup_environment_variables=[
                EnvVar(
                    name="GMAIL_ACCESS_TOKEN",
                    display_name="Access Token",
                    description="A valid Google OAuth2 access token with Gmail scopes",
                    required=True,
                    sensitive=True,
                ),
            ],
            test_endpoint=_profile_test_endpoint(
                "bearer_token",
                "Validates token by fetching Gmail profile information",
            ),
        ),
    ],
)
