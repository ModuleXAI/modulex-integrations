"""Microsoft Dynamics 365 Sales integration manifest."""
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
    name="microsoft_dynamics_365_sales",
    display_name="Microsoft Dynamics 365 Sales",
    description="CRM platform for managing accounts, contacts, appointments, and custom entities via the Dynamics 365 Web API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:microsoft_dynamics_365_sales",
    app_url="https://dynamics.microsoft.com",
    categories=["CRM", "Sales", "Productivity & Collaboration"],
    actions=[
        ActionDefinition(
            name="create_appointment",
            description="Create a new appointment linked to an account with a required attendee (system user)",
            parameters={
                "subject": ParameterDef(
                    type="string",
                    description="Title of the appointment",
                    required=True,
                ),
                "scheduledstart": ParameterDef(
                    type="string",
                    description="Start date/time in ISO 8601 format (e.g. 2026-02-20T12:00:00Z)",
                    required=True,
                ),
                "scheduledend": ParameterDef(
                    type="string",
                    description="End date/time in ISO 8601 format",
                    required=True,
                ),
                "regarding_account_id": ParameterDef(
                    type="string",
                    description="Account ID the appointment is regarding",
                    required=True,
                ),
                "required_attendee_email": ParameterDef(
                    type="string",
                    description="Email address of the Dynamics system user to add as attendee",
                    required=True,
                ),
                "category": ParameterDef(
                    type="integer",
                    description="Optional category value (numeric). Use list_appointment_categories to discover valid values",
                ),
            },
        ),
        ActionDefinition(
            name="create_custom_entity",
            description="Create a custom entity definition in Dynamics 365",
            parameters={
                "solution_id": ParameterDef(
                    type="string",
                    description="Identifier of the solution to associate the entity with",
                    required=True,
                ),
                "display_name": ParameterDef(
                    type="string",
                    description="Display name for the new entity (e.g. 'Bank Account')",
                    required=True,
                ),
                "primary_attribute": ParameterDef(
                    type="string",
                    description="Primary name attribute of the new entity (e.g. 'Account Name')",
                    required=True,
                ),
                "language_code": ParameterDef(
                    type="integer",
                    description="Language code (e.g. 1033 for English US)",
                    default=1033,
                ),
                "additional_attributes": ParameterDef(
                    type="object",
                    description="Array of attribute definition objects to add to the entity",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Description of the new entity",
                ),
                "has_activities": ParameterDef(
                    type="boolean",
                    description="Whether the entity supports activities",
                    default=False,
                ),
                "has_notes": ParameterDef(
                    type="boolean",
                    description="Whether the entity supports notes",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="find_contact",
            description="Search for a contact by ID, name, or custom OData filter",
            parameters={
                "contact_id": ParameterDef(
                    type="string",
                    description="Contact GUID to look up directly",
                ),
                "name": ParameterDef(
                    type="string",
                    description="Find contacts whose full name contains this value",
                ),
                "filter": ParameterDef(
                    type="string",
                    description="Custom OData $filter expression (e.g. \"lastname eq 'Smith'\")",
                ),
            },
        ),
        ActionDefinition(
            name="get_account",
            description="Retrieve a single account by its GUID",
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="Account GUID to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_accounts",
            description="List accounts with optional OData filter and pagination",
            parameters={
                "filter": ParameterDef(
                    type="string",
                    description="Optional OData $filter (e.g. 'statecode eq 0' for active accounts)",
                ),
                "records_per_page": ParameterDef(
                    type="integer",
                    description="Number of records per page (max 5000)",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="list_appointment_categories",
            description="List available appointment category values from metadata or existing rows",
            parameters={},
        ),
        ActionDefinition(
            name="list_appointment_category_options",
            description="Retrieve available options for the appointment Category picklist field",
            parameters={},
        ),
        ActionDefinition(
            name="list_appointments",
            description="List appointments ordered by scheduled start descending",
            parameters={
                "filter": ParameterDef(
                    type="string",
                    description="Optional OData $filter (e.g. 'statecode eq 0')",
                ),
                "records_per_page": ParameterDef(
                    type="integer",
                    description="Number of appointments to return (max 100)",
                    default=25,
                ),
            },
        ),
        ActionDefinition(
            name="list_solution_id_options",
            description="Retrieve available solutions with their IDs and names",
            parameters={},
        ),
        ActionDefinition(
            name="search_accounts",
            description="Search accounts by company name substring",
            parameters={
                "search_term": ParameterDef(
                    type="string",
                    description="Substring to match against account name",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_appointment",
            description="Update an existing appointment (only supplied fields are modified)",
            parameters={
                "appointment_id": ParameterDef(
                    type="string",
                    description="Appointment activity GUID to update",
                    required=True,
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Updated subject/title",
                ),
                "scheduledstart": ParameterDef(
                    type="string",
                    description="Updated start in ISO 8601",
                ),
                "scheduledend": ParameterDef(
                    type="string",
                    description="Updated end in ISO 8601",
                ),
                "category": ParameterDef(
                    type="integer",
                    description="Updated category value (numeric). Use list_appointment_categories to discover valid values",
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
                    name="MICROSOFT_DYNAMICS_365_SALES_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Microsoft Entra (Azure AD) OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                ),
                EnvVar(
                    name="MICROSOFT_DYNAMICS_365_SALES_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Microsoft Entra (Azure AD) OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                ),
                EnvVar(
                    name="MICROSOFT_DYNAMICS_365_SALES_API_URL",
                    display_name="Dynamics 365 Instance URL",
                    description="Your Dynamics 365 org URL hostname (e.g. org12345.crm.dynamics.com)",
                    required=True,
                    sensitive=False,
                    only_for_custom=False,
                    sample_format="org12345.crm.dynamics.com",
                    about_url="https://learn.microsoft.com/en-us/power-apps/developer/data-platform/discovery-orgs",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                scopes=["https://dynamics.microsoft.com/user_impersonation", "offline_access"],
            ),
            test_endpoint=TestEndpoint(
                url="https://{api_url}/api/data/v9.2/WhoAmI",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["UserId"],
                ),
                cost_level="free",
                description="Validates OAuth token by calling the WhoAmI endpoint",
            ),
        ),
    ],
)
