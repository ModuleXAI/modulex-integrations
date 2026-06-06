"""Pinterest integration manifest.

Two auth schemas both produce a Bearer access token at runtime — the
modulex runtime injects ``api_key`` either way, so tools.py only
implements one signature (api_key Bearer).

Legacy JSON's ``oauth_config`` carried ``response_type`` and
``grant_type``; legacy ``auth_schemas[1].token_fields`` carried a token
field mapping. Neither is in our schema and both are dropped during
migration.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


_TEST_SUCCESS = SuccessIndicators(status_codes=[200], response_fields=["items"])

manifest = IntegrationManifest(
    name="pinterest",
    display_name="Pinterest",
    description=(
        "Visual discovery and social media platform for managing boards, "
        "pins, and content. Create pins, organize boards, and manage "
        "visual content for marketing and inspiration."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:pinterest",
    app_url="https://www.pinterest.com",
    categories=[
        "Social Media",
        "Marketing & Email",
        "social_media",
        "automation",
        "development",
        "miscellaneous",
        "pinterest",
    ],
    actions=[
        ActionDefinition(
            name="list_boards",
            description="List all Pinterest boards for the authenticated user",
            parameters={
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of boards per page (max 250)",
                    default=25,
                ),
                "bookmark": ParameterDef(
                    type="string",
                    description="Cursor for pagination to get the next page",
                ),
            },
        ),
        ActionDefinition(
            name="get_board_sections",
            description="Get sections of a Pinterest board to organize pins",
            parameters={
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board to get sections from",
                    required=True,
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of sections per page (max 250)",
                    default=25,
                ),
                "bookmark": ParameterDef(
                    type="string", description="Cursor for pagination"
                ),
            },
        ),
        ActionDefinition(
            name="create_pin",
            description="Create a new pin on a Pinterest board with an image URL",
            parameters={
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board to pin to",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string", description="Title of the pin", required=True
                ),
                "media_url": ParameterDef(
                    type="string",
                    description="URL of the image to pin",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string", description="Description of the pin"
                ),
                "link": ParameterDef(
                    type="string", description="Source link/URL for the pin"
                ),
                "alt_text": ParameterDef(
                    type="string", description="Alt text for accessibility"
                ),
                "board_section_id": ParameterDef(
                    type="string", description="ID of the board section"
                ),
            },
        ),
        ActionDefinition(
            name="list_pins",
            description="List pins from a Pinterest board or board section",
            parameters={
                "board_id": ParameterDef(
                    type="string",
                    description="The ID of the board to list pins from",
                    required=True,
                ),
                "board_section_id": ParameterDef(
                    type="string", description="ID of the board section (optional)"
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of pins per page (max 250)",
                    default=25,
                ),
                "bookmark": ParameterDef(
                    type="string", description="Cursor for pagination"
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="OAuth Access Token",
            description=(
                "Authenticate using your Pinterest OAuth access token. The "
                "token can be obtained through Pinterest's OAuth 2.0 flow."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="PINTEREST_API_KEY",
                    display_name="Access Token",
                    description="Your Pinterest OAuth access token",
                    required=True,
                    sensitive=True,
                    about_url=(
                        "https://developers.pinterest.com/docs/getting-started/authentication/"
                    ),
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.pinterest.com/v5/boards",
                method="GET",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                success_indicators=_TEST_SUCCESS,
                cost_level="minimal",
                description="Validates API credentials by listing boards",
            ),
        ),
        OAuth2AuthSchema(
            display_name="OAuth 2.0",
            description=(
                "Authenticate using Pinterest OAuth 2.0 for full API access "
                "with token refresh capabilities."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="PINTEREST_OAUTH2_CLIENT_ID",
                    display_name="App ID",
                    description="Your Pinterest App ID from the developer portal",
                    required=True,
                    sensitive=False,
                    about_url="https://developers.pinterest.com/apps/",
                ),
                EnvVar(
                    name="PINTEREST_OAUTH2_CLIENT_SECRET",
                    display_name="App Secret",
                    description="Your Pinterest App Secret from the developer portal",
                    required=True,
                    sensitive=True,
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://www.pinterest.com/oauth/",
                token_url="https://api.pinterest.com/v5/oauth/token",
                scopes=[
                    "boards:read",
                    "boards:write",
                    "pins:read",
                    "pins:write",
                    "user_accounts:read",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://api.pinterest.com/v5/boards",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                success_indicators=_TEST_SUCCESS,
                cost_level="minimal",
                description="Validates OAuth access by listing boards",
            ),
        ),
    ],
)
