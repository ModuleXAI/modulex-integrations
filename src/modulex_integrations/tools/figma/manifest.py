"""Figma integration manifest."""
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
    name="figma",
    display_name="Figma",
    description=(
        "Design collaboration platform for creating, sharing,"
        " and commenting on design files"
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:figma",
    app_url="https://www.figma.com",
    categories=["Productivity & Collaboration", "Design"],
    actions=[
        ActionDefinition(
            name="list_comments",
            description="List all comments left on a Figma file",
            parameters={
                "file_id": ParameterDef(
                    type="string",
                    description="The Figma file ID (found in the file URL after /file/)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_comment",
            description="Delete a comment from a Figma file",
            parameters={
                "file_id": ParameterDef(
                    type="string",
                    description="The Figma file ID (found in the file URL after /file/)",
                    required=True,
                ),
                "comment_id": ParameterDef(
                    type="string",
                    description="The ID of the comment to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="post_a_comment",
            description="Post a comment to a Figma file",
            parameters={
                "file_id": ParameterDef(
                    type="string",
                    description="The Figma file ID (found in the file URL after /file/)",
                    required=True,
                ),
                "message": ParameterDef(
                    type="string",
                    description="The text contents of the comment to post",
                    required=True,
                ),
                "comment_id": ParameterDef(
                    type="string",
                    description="The ID of the comment to reply to (must be a root comment)",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Figma OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="FIGMA_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Figma OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://www.figma.com/developers/apps",
                ),
                EnvVar(
                    name="FIGMA_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Figma OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://www.figma.com/developers/apps",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://www.figma.com/oauth",
                token_url="https://api.figma.com/v1/oauth/token",
                scopes=["file_content:read", "file_comments:read", "file_comments:write"],
                token_auth_method="basic",
            ),
            test_endpoint=TestEndpoint(
                url="https://api.figma.com/v1/me",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching authenticated user info",
            ),
        ),
    ],
)
