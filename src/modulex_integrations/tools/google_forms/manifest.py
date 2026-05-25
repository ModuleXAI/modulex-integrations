"""Google Forms integration manifest."""
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
    name="google_forms",
    display_name="Google Forms",
    description="Create, update, and read Google Forms and their responses via the Google Forms API.",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:google_forms",
    app_url="https://forms.google.com",
    categories=["Productivity & Collaboration", "Forms & Surveys"],
    actions=[
        ActionDefinition(
            name="create_form",
            description="Creates a new Google Form with the specified title and optional document title.",
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="The title of the form which is visible to responders.",
                    required=True,
                ),
                "document_title": ParameterDef(
                    type="string",
                    description="The title of the document which is visible in Google Drive. Optional.",
                ),
            },
        ),
        ActionDefinition(
            name="create_text_question",
            description="Creates a new text question (short or paragraph) in an existing Google Form via batchUpdate.",
            parameters={
                "form_id": ParameterDef(
                    type="string",
                    description="Identifier of the Google Form to update.",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="Title of the question.",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="Description of the question.",
                    required=True,
                ),
                "index": ParameterDef(
                    type="integer",
                    description="The 0-based index where the item is inserted in the form. Must be in the range [0..N), where N is the current number of items.",
                    required=True,
                ),
                "paragraph": ParameterDef(
                    type="boolean",
                    description="If true, the question is a paragraph (multi-line) question. If false, it is a short text question.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_form",
            description="Gets information about a Google Form, including its title, settings, and items.",
            parameters={
                "form_id": ParameterDef(
                    type="string",
                    description="Identifier of the Google Form to retrieve.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_form_response",
            description="Gets a single response from a Google Form by response ID.",
            parameters={
                "form_id": ParameterDef(
                    type="string",
                    description="Identifier of the Google Form the response belongs to.",
                    required=True,
                ),
                "response_id": ParameterDef(
                    type="string",
                    description="The response ID within the form to retrieve.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_form_responses",
            description="Lists all responses submitted to a Google Form.",
            parameters={
                "form_id": ParameterDef(
                    type="string",
                    description="Identifier of the Google Form whose responses are listed.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_form_title",
            description="Updates the title of an existing Google Form via batchUpdate.",
            parameters={
                "form_id": ParameterDef(
                    type="string",
                    description="Identifier of the Google Form to update.",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The new title of the form which is visible to responders.",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Google OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_FORMS_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth App Client ID from the Google Cloud Console.",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_FORMS_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google OAuth App Client Secret from the Google Cloud Console.",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scopes=[
                    "https://www.googleapis.com/auth/forms.body",
                    "https://www.googleapis.com/auth/forms.responses.readonly",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://www.googleapis.com/oauth2/v3/userinfo",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["sub"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching the authenticated Google user info.",
            ),
        ),
    ],
)
