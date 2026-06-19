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


def _labels_test_endpoint(placeholder: str, description: str) -> TestEndpoint:
    return TestEndpoint(
        url="https://www.googleapis.com/gmail/v1/users/me/labels",
        method="GET",
        headers={"Authorization": f"Bearer {{{placeholder}}}"},
        success_indicators=SuccessIndicators(
            status_codes=[200], response_fields=["labels"]
        ),
        cost_level="free",
        description=description,
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
                access_type="offline",
                prompt="consent",
                scopes=[
                    "https://www.googleapis.com/auth/gmail.send",
                    "https://www.googleapis.com/auth/gmail.labels",
                ],
                token_auth_method="body",
            ),
            test_endpoint=_labels_test_endpoint(
                "access_token",
                "Validates OAuth token by listing Gmail labels",
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
            test_endpoint=_labels_test_endpoint(
                "bearer_token",
                "Validates token by listing Gmail labels",
            ),
        ),
    ],
)
