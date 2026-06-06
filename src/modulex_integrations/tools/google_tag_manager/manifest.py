"""Google Tag Manager integration manifest."""
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
    name="google_tag_manager",
    display_name="Google Tag Manager",
    description="Manage tags, variables, and workspaces in Google Tag Manager containers",
    version="1.0.0",
    author="ModuleX",
    logo="logos:google-tag-manager",
    app_url="https://tagmanager.google.com",
    categories=["Analytics & Data", "Analytics", "Marketing"],
    actions=[
        ActionDefinition(
            name="create_tag",
            description="Create a tag in a Google Tag Manager workspace",
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="The Google Tag Manager account ID",
                    required=True,
                ),
                "container_id": ParameterDef(
                    type="string",
                    description="The container ID",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="The workspace ID",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="The name of the tag",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="The type of the tag (see Tag Dictionary Reference)",
                    required=True,
                ),
                "parameter": ParameterDef(
                    type="string",
                    description="JSON string representing the list of parameters for the tag",
                    required=True,
                ),
                "live_only": ParameterDef(
                    type="boolean",
                    description="Whether the tag should only fire in the live environment",
                ),
                "notes": ParameterDef(
                    type="string",
                    description="Any notes or comments about the tag",
                ),
                "consent_settings": ParameterDef(
                    type="string",
                    description="JSON string representing consent settings for the tag",
                ),
                "monitoring_metadata": ParameterDef(
                    type="string",
                    description="JSON string representing monitoring metadata for the tag",
                ),
            },
        ),
        ActionDefinition(
            name="get_tag",
            description="Get a specific tag from a Google Tag Manager workspace",
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="The Google Tag Manager account ID",
                    required=True,
                ),
                "container_id": ParameterDef(
                    type="string",
                    description="The container ID",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="The workspace ID",
                    required=True,
                ),
                "tag_id": ParameterDef(
                    type="string",
                    description="The tag ID",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_tags",
            description="List all tags in a Google Tag Manager workspace",
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="The Google Tag Manager account ID",
                    required=True,
                ),
                "container_id": ParameterDef(
                    type="string",
                    description="The container ID",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="The workspace ID",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_account_id_options",
            description="List available Google Tag Manager accounts",
            parameters={},
        ),
        ActionDefinition(
            name="update_tag",
            description="Update a tag in a Google Tag Manager workspace",
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="The Google Tag Manager account ID",
                    required=True,
                ),
                "container_id": ParameterDef(
                    type="string",
                    description="The container ID",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="The workspace ID",
                    required=True,
                ),
                "tag_id": ParameterDef(
                    type="string",
                    description="The tag ID",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="The type of the tag (see Tag Dictionary Reference)",
                    required=True,
                ),
                "parameter": ParameterDef(
                    type="string",
                    description="JSON string representing the list of parameters for the tag",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="The name of the tag",
                ),
                "live_only": ParameterDef(
                    type="boolean",
                    description="Whether the tag should only fire in the live environment",
                ),
                "notes": ParameterDef(
                    type="string",
                    description="Any notes or comments about the tag",
                ),
                "consent_settings": ParameterDef(
                    type="string",
                    description="JSON string representing consent settings for the tag",
                ),
                "monitoring_metadata": ParameterDef(
                    type="string",
                    description="JSON string representing monitoring metadata for the tag",
                ),
            },
        ),
        ActionDefinition(
            name="update_variable",
            description="Update a variable in a Google Tag Manager workspace",
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="The Google Tag Manager account ID",
                    required=True,
                ),
                "container_id": ParameterDef(
                    type="string",
                    description="The container ID",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="The workspace ID",
                    required=True,
                ),
                "variable_id": ParameterDef(
                    type="string",
                    description="The variable ID",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="The name of the variable",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="The type of the variable (e.g. 'jsm')",
                    required=True,
                ),
                "parameter": ParameterDef(
                    type="string",
                    description="JSON string representing the list of parameters for the variable",
                    required=True,
                ),
                "format_value": ParameterDef(
                    type="string",
                    description="JSON string representing the formatValue object for the variable",
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
                    name="GOOGLE_TAG_MANAGER_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_TAG_MANAGER_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scopes=[
                    "https://www.googleapis.com/auth/tagmanager.edit.containers",
                    "https://www.googleapis.com/auth/tagmanager.readonly",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://www.googleapis.com/tagmanager/v2/accounts",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="free",
                description="Validates OAuth token by listing Tag Manager accounts",
            ),
        ),
    ],
)
