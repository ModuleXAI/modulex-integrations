"""Google Directory integration manifest."""
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
    name="google_directory",
    display_name="Google Directory",
    description="Manage users, groups, and group memberships in Google Workspace via the Admin SDK Directory API.",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:google_directory-themed",
    app_url="https://admin.google.com",
    categories=["Productivity & Collaboration", "identity", "admin"],
    actions=[
        ActionDefinition(
            name="add_member_to_group",
            description="Adds a member to a Google Workspace group",
            parameters={
                "group_id": ParameterDef(
                    type="string",
                    description="The group ID or email address of the target group",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="The email address of the member to add",
                    required=True,
                ),
                "role": ParameterDef(
                    type="string",
                    description="The role of the member: MEMBER, OWNER, or MANAGER",
                    default="MEMBER",
                ),
            },
        ),
        ActionDefinition(
            name="create_group",
            description="Creates a new Google Workspace group",
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="The group's email address (domain must be associated with the account)",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="The group name",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="Description of the group",
                ),
            },
        ),
        ActionDefinition(
            name="create_user",
            description="Creates a new Google Workspace user",
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="The user's primary email address (domain must be associated with the account)",
                    required=True,
                ),
                "password": ParameterDef(
                    type="string",
                    description="The password for the user account",
                    required=True,
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="First name of the user",
                    required=True,
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Last name of the user",
                    required=True,
                ),
                "phone": ParameterDef(
                    type="string",
                    description="Phone number of the user",
                ),
                "notes": ParameterDef(
                    type="string",
                    description="Notes for the user",
                ),
            },
        ),
        ActionDefinition(
            name="get_group",
            description="Retrieves information about a Google Workspace group",
            parameters={
                "group_id": ParameterDef(
                    type="string",
                    description="The group ID or email address of the group to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_user",
            description="Retrieves information about a Google Workspace user",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="The user ID or primary email address of the user to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_groups",
            description="Retrieves a list of all groups in the Google Workspace directory",
            parameters={
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of groups to return (default returns all)",
                ),
                "page_token": ParameterDef(
                    type="string",
                    description="Token for fetching the next page of results",
                ),
            },
        ),
        ActionDefinition(
            name="list_users",
            description="Retrieves a list of all users in the Google Workspace directory",
            parameters={
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of users to return (default returns all)",
                ),
                "page_token": ParameterDef(
                    type="string",
                    description="Token for fetching the next page of results",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Google OAuth (recommended for Workspace admin access)",
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_DIRECTORY_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="123456789-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_DIRECTORY_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google OAuth App Client Secret",
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
                    "https://www.googleapis.com/auth/admin.directory.user",
                    "https://www.googleapis.com/auth/admin.directory.group",
                    "https://www.googleapis.com/auth/admin.directory.group.member",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://admin.googleapis.com/admin/directory/v1/users?customer=my_customer&maxResults=1",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["kind"],
                ),
                cost_level="free",
                description="Validates OAuth token by listing one user from the directory",
            ),
        ),
    ],
)
