"""Medium integration manifest."""
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
    name="medium",
    display_name="Medium",
    description="Publish posts to Medium via the Medium REST API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:medium-themed",
    app_url="https://medium.com",
    categories=["Social Media", "Content & Publishing", "Blogging"],
    actions=[
        ActionDefinition(
            name="create_post",
            description="Create a new Medium post.",
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="The title of the post. Used for SEO and listing display. Titles longer than 100 characters will be ignored.",
                    required=True,
                ),
                "content_format": ParameterDef(
                    type="string",
                    description="The format of the content field. Valid values are 'html' and 'markdown'.",
                    required=True,
                ),
                "content": ParameterDef(
                    type="string",
                    description="The body of the post, in valid semantic HTML or Markdown. Include the title in the content if you want it displayed on the post page.",
                    required=True,
                ),
                "tags": ParameterDef(
                    type="array",
                    description="Tags to classify the post (array of strings). Only the first three are used. Tags longer than 25 characters are ignored.",
                ),
                "canonical_url": ParameterDef(
                    type="string",
                    description="The original home of this content, if it was originally published elsewhere.",
                ),
                "publish_status": ParameterDef(
                    type="string",
                    description="The status of the post. Valid values are 'public', 'draft', or 'unlisted'. Default is 'public'.",
                ),
                "license": ParameterDef(
                    type="string",
                    description="The license of the post. Valid values are 'all-rights-reserved', 'cc-40-by', 'cc-40-by-sa', 'cc-40-by-nd', 'cc-40-by-nc', 'cc-40-by-nc-nd', 'cc-40-by-nc-sa', 'cc-40-zero', 'public-domain'. Default is 'all-rights-reserved'.",
                ),
                "notify_followers": ParameterDef(
                    type="boolean",
                    description="Whether to notify followers that the user has published.",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Medium OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="MEDIUM_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Medium OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://medium.com/me/applications",
                ),
                EnvVar(
                    name="MEDIUM_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Medium OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://medium.com/me/applications",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://medium.com/m/oauth/authorize",
                token_url="https://api.medium.com/v1/tokens",
                scopes=["basicProfile", "publishPost"],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.medium.com/v1/me",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching the authenticated user profile",
            ),
        ),
    ],
)
