"""Microsoft Entra ID integration manifest."""
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
    name="microsoft_entra_id",
    display_name="Microsoft Entra ID",
    description="Identity and access management via Microsoft Graph API for users, groups, and directory objects.",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:microsoft_entra_id",
    app_url="https://entra.microsoft.com",
    categories=["Identity & Access Management", "Enterprise", "Security"],
    actions=[
        ActionDefinition(
            name="add_member_to_group",
            description="Add a user as a member to a Microsoft Entra ID group.",
            parameters={
                "group_id": ParameterDef(
                    type="string",
                    description="Identifier of the group",
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="Identifier of the user to add",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_group",
            description="Create a new group in Microsoft Entra ID.",
            parameters={
                "display_name": ParameterDef(
                    type="string",
                    description="The name to display in the address book for the group",
                    required=True,
                ),
                "mail_enabled": ParameterDef(
                    type="boolean",
                    description="Set to true for mail-enabled groups",
                    required=True,
                ),
                "mail_nickname": ParameterDef(
                    type="string",
                    description="The mail alias for the group, unique for groups in the organization. Maximum length is 64 characters.",
                    required=True,
                ),
                "security_enabled": ParameterDef(
                    type="boolean",
                    description="Set to true for security-enabled groups",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_group",
            description="Delete a group in Microsoft Entra ID.",
            parameters={
                "group_id": ParameterDef(
                    type="string",
                    description="Identifier of the group to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_manager",
            description="Get the user's manager information. Returns the user or organizational contact assigned as the user's manager.",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="Identifier of the user. Leave empty to use the signed-in user.",
                ),
            },
        ),
        ActionDefinition(
            name="get_ms365_groups",
            description="Get the user's Microsoft 365 groups (unified groups). Returns groups the user is a direct member of.",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="Identifier of the user. Leave empty to use the signed-in user.",
                ),
            },
        ),
        ActionDefinition(
            name="get_organization_groups",
            description="List all groups in the organization (excluding dynamic distribution groups).",
            parameters={},
        ),
        ActionDefinition(
            name="get_organization_users",
            description="List all users in the organization. By default returns only enabled accounts.",
            parameters={
                "max_users": ParameterDef(
                    type="integer",
                    description="Maximum number of users to return. Omit for no limit.",
                ),
                "filter": ParameterDef(
                    type="string",
                    description="OData filter expression, e.g. 'accountEnabled eq true'",
                    default="accountEnabled eq true",
                ),
                "search": ParameterDef(
                    type="string",
                    description="OData search expression, e.g. '\"displayName:John\"'",
                ),
            },
        ),
        ActionDefinition(
            name="get_profile",
            description="Get the user's profile information from Microsoft Entra ID.",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="Identifier of the user. Leave empty to use the signed-in user.",
                ),
            },
        ),
        ActionDefinition(
            name="remove_member_from_group",
            description="Remove a member from a Microsoft Entra ID group.",
            parameters={
                "group_id": ParameterDef(
                    type="string",
                    description="Identifier of the group",
                    required=True,
                ),
                "user_id": ParameterDef(
                    type="string",
                    description="Identifier of the user to remove",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_groups",
            description="Search for groups by name or description in Microsoft Entra ID.",
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Keywords to search by",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="The maximum number of groups to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="update_group",
            description="Update an existing group in Microsoft Entra ID.",
            parameters={
                "group_id": ParameterDef(
                    type="string",
                    description="Identifier of the group to update",
                    required=True,
                ),
                "allow_external_senders": ParameterDef(
                    type="boolean",
                    description="Whether people external to the organization can send messages to the group",
                ),
                "auto_subscribe_new_members": ParameterDef(
                    type="boolean",
                    description="Whether new members added to the group will be auto-subscribed to receive email notifications",
                ),
                "description": ParameterDef(
                    type="string",
                    description="An optional description for the group",
                ),
                "display_name": ParameterDef(
                    type="string",
                    description="The name to display in the address book for the group",
                ),
                "mail_nickname": ParameterDef(
                    type="string",
                    description="The mail alias for the group. Maximum length is 64 characters.",
                ),
                "security_enabled": ParameterDef(
                    type="boolean",
                    description="Set to true for security-enabled groups",
                ),
                "visibility": ParameterDef(
                    type="string",
                    description="Specifies the visibility of the group. Allowed values: Public, Private.",
                ),
            },
        ),
        ActionDefinition(
            name="update_user",
            description="Update an existing user in Microsoft Entra ID.",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="Identifier of the user to update",
                    required=True,
                ),
                "display_name": ParameterDef(
                    type="string",
                    description="The name to display in the address book for the user",
                ),
                "mail": ParameterDef(
                    type="string",
                    description="The SMTP address for the user",
                ),
                "mail_nickname": ParameterDef(
                    type="string",
                    description="The mail alias for the user",
                ),
                "account_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the account is enabled",
                    default=True,
                ),
                "street_address": ParameterDef(
                    type="string",
                    description="The street address of the user's place of business",
                ),
                "city": ParameterDef(
                    type="string",
                    description="The city in which the user is located",
                ),
                "state": ParameterDef(
                    type="string",
                    description="The state or province in the user's address",
                ),
                "postal_code": ParameterDef(
                    type="string",
                    description="The postal code for the user's postal address",
                ),
                "country": ParameterDef(
                    type="string",
                    description="The country/region in which the user is located",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Microsoft Entra ID OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="MICROSOFT_ENTRA_ID_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Microsoft Entra ID OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                ),
                EnvVar(
                    name="MICROSOFT_ENTRA_ID_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Microsoft Entra ID OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                scopes=[
                    "User.Read",
                    "User.ReadWrite.All",
                    "Group.ReadWrite.All",
                    "GroupMember.ReadWrite.All",
                    "Directory.ReadWrite.All",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://graph.microsoft.com/v1.0/me",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
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
