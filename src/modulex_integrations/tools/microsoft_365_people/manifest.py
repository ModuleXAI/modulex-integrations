"""Microsoft 365 People integration manifest."""
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
    name="microsoft_365_people",
    display_name="Microsoft 365 People",
    description="Manage contacts and contact folders via the Microsoft Graph API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:microsoft_365_people-themed",
    app_url="https://www.microsoft.com/en-us/microsoft-365",
    categories=["Productivity & Collaboration", "contacts"],
    actions=[
        ActionDefinition(
            name="create_contact",
            description="Create a new contact in Microsoft 365 People",
            parameters={
                "email": ParameterDef(
                    type="string",
                    description="Email address of the contact",
                    required=True,
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="First name of the contact",
                    required=True,
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Last name of the contact",
                ),
                "folder_id": ParameterDef(
                    type="string",
                    description="ID of the contact folder to create the contact in (defaults to the root contacts folder)",
                ),
                "mobile_phone": ParameterDef(
                    type="string",
                    description="Mobile phone number of the contact",
                ),
                "home_phones": ParameterDef(
                    type="array",
                    description="List of home phone numbers for the contact (each element is a string)",
                ),
                "street": ParameterDef(
                    type="string",
                    description="Street address of the contact",
                ),
                "city": ParameterDef(
                    type="string",
                    description="City of the contact",
                ),
                "state": ParameterDef(
                    type="string",
                    description="State of the contact",
                ),
                "postal_code": ParameterDef(
                    type="string",
                    description="Postal code of the contact",
                ),
                "country_or_region": ParameterDef(
                    type="string",
                    description="Country or region of the contact",
                ),
            },
        ),
        ActionDefinition(
            name="create_contact_folder",
            description="Create a new contact folder in Microsoft 365 People",
            parameters={
                "display_name": ParameterDef(
                    type="string",
                    description="The display name of the new contact folder",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_contact",
            description="Update an existing contact in Microsoft 365 People",
            parameters={
                "contact_id": ParameterDef(
                    type="string",
                    description="ID of the contact to update",
                    required=True,
                ),
                "folder_id": ParameterDef(
                    type="string",
                    description="ID of the contact folder containing the contact (defaults to the root contacts folder)",
                ),
                "email": ParameterDef(
                    type="string",
                    description="New email address for the contact",
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="New first name for the contact",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="New last name for the contact",
                ),
                "mobile_phone": ParameterDef(
                    type="string",
                    description="New mobile phone number for the contact",
                ),
                "home_phones": ParameterDef(
                    type="array",
                    description="New list of home phone numbers for the contact (each element is a string)",
                ),
                "street": ParameterDef(
                    type="string",
                    description="New street address for the contact",
                ),
                "city": ParameterDef(
                    type="string",
                    description="New city for the contact",
                ),
                "state": ParameterDef(
                    type="string",
                    description="New state for the contact",
                ),
                "postal_code": ParameterDef(
                    type="string",
                    description="New postal code for the contact",
                ),
                "country_or_region": ParameterDef(
                    type="string",
                    description="New country or region for the contact",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Microsoft OAuth2 (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="MICROSOFT_365_PEOPLE_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Microsoft Azure AD OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                ),
                EnvVar(
                    name="MICROSOFT_365_PEOPLE_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Microsoft Azure AD OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                scopes=["Contacts.ReadWrite", "User.Read", "offline_access"],
            ),
            test_endpoint=TestEndpoint(
                url="https://graph.microsoft.com/v1.0/me",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching the authenticated user profile",
            ),
        ),
    ],
)
