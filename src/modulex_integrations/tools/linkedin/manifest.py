"""LinkedIn integration manifest."""
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
    name="linkedin",
    display_name="LinkedIn",
    description="LinkedIn social networking platform for professional connections, posts, and organization management",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:linkedin-themed",
    app_url="https://www.linkedin.com",
    categories=["Social Media", "Marketing", "Communication"],
    actions=[
        ActionDefinition(
            name="create_comment",
            description="Create a comment on a share or user generated content post",
            parameters={
                "urn_to_comment": ParameterDef(
                    type="string",
                    description="The share or user generated content post URN where the comment will be made",
                    required=True,
                ),
                "actor": ParameterDef(
                    type="string",
                    description="Entity authoring the comment, must be a person or organization URN (e.g. urn:li:person:ABC123)",
                    required=True,
                ),
                "message": ParameterDef(
                    type="string",
                    description="Text of the comment",
                    required=True,
                ),
                "content": ParameterDef(
                    type="object",
                    description="Optional media content entities as a JSON object",
                ),
                "parent_comment": ParameterDef(
                    type="string",
                    description="URN of the parent comment for nested comments (not available for first-level comments)",
                ),
            },
        ),
        ActionDefinition(
            name="create_image_post_organization",
            description="Create an image post on LinkedIn as an organization",
            parameters={
                "organization_id": ParameterDef(
                    type="string",
                    description="ID of the organization that will author the post",
                    required=True,
                ),
                "image_url": ParameterDef(
                    type="string",
                    description="URL of the image to upload and post",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Text to be posted on the LinkedIn timeline",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_image_post_user",
            description="Create an image post on LinkedIn as the authenticated user",
            parameters={
                "image_url": ParameterDef(
                    type="string",
                    description="URL of the image to upload and post",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Text to be posted on the LinkedIn timeline",
                    required=True,
                ),
                "visibility": ParameterDef(
                    type="string",
                    description="Visibility restrictions on content. Valid values: CONNECTIONS, PUBLIC, LOGGED_IN",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_like_on_share",
            description="Create a like on a share or user generated content post",
            parameters={
                "parent_urn": ParameterDef(
                    type="string",
                    description="The top-level share URN or user generated content URN where the like will be performed",
                    required=True,
                ),
                "actor": ParameterDef(
                    type="string",
                    description="Entity performing the like, must be a person or organization URN",
                    required=True,
                ),
                "object": ParameterDef(
                    type="string",
                    description="URN of the entity to which the like belongs, should be a sub-entity of the top-level share",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_text_post_organization",
            description="Create a text post on LinkedIn as an organization, optionally with an article URL",
            parameters={
                "organization_id": ParameterDef(
                    type="string",
                    description="ID of the organization that will author the post",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Text to be posted on the LinkedIn timeline",
                    required=True,
                ),
                "article": ParameterDef(
                    type="string",
                    description="URL of an article to share with the post",
                ),
            },
        ),
        ActionDefinition(
            name="create_text_post_user",
            description="Create a text post on LinkedIn as the authenticated user, optionally with an article URL",
            parameters={
                "visibility": ParameterDef(
                    type="string",
                    description="Visibility restrictions on content. Valid values: CONNECTIONS, PUBLIC, LOGGED_IN",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Text to be posted on the LinkedIn timeline",
                    required=True,
                ),
                "article": ParameterDef(
                    type="string",
                    description="URL of an article to share with the post",
                ),
            },
        ),
        ActionDefinition(
            name="delete_post",
            description="Delete a post from LinkedIn",
            parameters={
                "post_id": ParameterDef(
                    type="string",
                    description="URN of the post to delete (e.g. urn:li:ugcPost:123 or urn:li:share:123)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="fetch_ad_account",
            description="Fetch an individual ad account given its ID",
            parameters={
                "ad_account_id": ParameterDef(
                    type="string",
                    description="ID of the ad account to fetch",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_current_member_profile",
            description="Get the profile of the current authenticated member",
            parameters={},
        ),
        ActionDefinition(
            name="get_member_profile",
            description="Get another member's profile given their person ID",
            parameters={
                "person_id": ParameterDef(
                    type="string",
                    description="Identifier of the person to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_multiple_member_profiles",
            description="Get multiple member profiles at once given their person IDs",
            parameters={
                "people_ids": ParameterDef(
                    type="array",
                    description="List of person ID strings to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_org_member_access",
            description="Get the organization access control information of the current authenticated member",
            parameters={
                "role": ParameterDef(
                    type="string",
                    description="Limit results to a specific role. Valid values: ADMINISTRATOR, DIRECT_SPONSORED_CONTENT_POSTER, RECRUITING_POSTER, LEAD_CAPTURE_ADMINISTRATOR, LEAD_GEN_FORMS_MANAGER, ANALYST, CURATOR, CONTENT_ADMINISTRATOR",
                ),
                "state": ParameterDef(
                    type="string",
                    description="Limit results to a specific role state. Valid values: APPROVED, REJECTED, REQUESTED, REVOKED",
                ),
            },
        ),
        ActionDefinition(
            name="get_organization_access_control",
            description="Get a selected organization's access control information",
            parameters={
                "organization_id": ParameterDef(
                    type="string",
                    description="ID of the organization for which the access control information is being retrieved",
                    required=True,
                ),
                "max": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="get_organization_administrators",
            description="Get the administrator members of a selected organization",
            parameters={
                "organization_id": ParameterDef(
                    type="string",
                    description="ID of the organization for which administrators are being retrieved",
                    required=True,
                ),
                "max_pages": ParameterDef(
                    type="integer",
                    description="Maximum number of pages to fetch (1-500)",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="get_profile_picture_fields",
            description="Get the authenticated user's profile picture data including display image and metadata",
            parameters={
                "include_original_image": ParameterDef(
                    type="boolean",
                    description="Whether to include the original image data in the response (requires special permissions)",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="retrieve_comments_on_comments",
            description="Retrieve comments on a comment given the parent comment URN",
            parameters={
                "comment_urn": ParameterDef(
                    type="string",
                    description="Parent comment URN to retrieve nested comments for. A composite URN using comment ID and activity URN",
                    required=True,
                ),
                "max": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="retrieve_comments_shares",
            description="Retrieve comments on a share given the share URN",
            parameters={
                "entity_urn": ParameterDef(
                    type="string",
                    description="URN of the entity to retrieve comments on",
                    required=True,
                ),
                "max": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="search_organization",
            description="Search for an organization by vanity name or email domain",
            parameters={
                "search_by": ParameterDef(
                    type="string",
                    description="Field to search by. Valid values: vanityName, emailDomain",
                    required=True,
                ),
                "search_term": ParameterDef(
                    type="string",
                    description="Keyword to search for",
                    required=True,
                ),
                "max": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=50,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using LinkedIn OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="LINKEDIN_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="LinkedIn OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://www.linkedin.com/developers/apps",
                ),
                EnvVar(
                    name="LINKEDIN_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="LinkedIn OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://www.linkedin.com/developers/apps",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://www.linkedin.com/oauth/v2/authorization",
                token_url="https://www.linkedin.com/oauth/v2/accessToken",
                scopes=[
                    "openid",
                    "profile",
                    "email",
                    "w_member_social",
                    "r_organization_social",
                    "w_organization_social",
                    "rw_organization_admin",
                    "r_ads",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.linkedin.com/rest/me",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                    "LinkedIn-Version": "202509",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching authenticated user profile",
            ),
        ),
    ],
)
