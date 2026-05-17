"""Klaviyo integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="klaviyo",
    display_name="Klaviyo",
    description=(
        "Email marketing and automation platform for personalized customer "
        "experiences. Manage lists, profiles, and subscriptions for targeted "
        "email campaigns."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:klaviyo-themed",
    app_url="https://www.klaviyo.com",
    categories=["Marketing & Email", "email", "automation", "development"],
    actions=[
        ActionDefinition(
            name="get_lists",
            description=(
                "Get a listing of all lists in a Klaviyo account with optional "
                "sorting and pagination"
            ),
            parameters={
                "sort": ParameterDef(
                    type="string",
                    description="Field to sort by: 'created', 'id', 'name', or 'updated'",
                    default="created",
                ),
                "sort_direction": ParameterDef(
                    type="string",
                    description="Sort direction: 'asc' or 'desc'",
                    default="desc",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of lists to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="get_list",
            description="Get a specific Klaviyo list by its ID",
            parameters={
                "list_id": ParameterDef(
                    type="string",
                    description="The ID of the Klaviyo list to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_list",
            description="Create a new list in a Klaviyo account",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="The name for the new list",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_profiles",
            description=(
                "Get profiles from a Klaviyo account with optional sorting and "
                "pagination"
            ),
            parameters={
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of profiles to return",
                    default=100,
                ),
                "sort": ParameterDef(
                    type="string",
                    description="Field to sort by: 'created', 'updated', 'email'",
                    default="created",
                ),
                "sort_direction": ParameterDef(
                    type="string",
                    description="Sort direction: 'asc' or 'desc'",
                    default="desc",
                ),
            },
        ),
        ActionDefinition(
            name="add_members_to_list",
            description="Add one or more profiles to a specific Klaviyo list",
            parameters={
                "list_id": ParameterDef(
                    type="string",
                    description="The ID of the list to add members to",
                    required=True,
                ),
                "profile_ids": ParameterDef(
                    type="array",
                    description="List of profile IDs to add to the list",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Private API Key",
            description=(
                "Authenticate using your Klaviyo Private API Key. Create one "
                "in Settings > API Keys"
            ),
            setup_environment_variables=[
                EnvVar(
                    name="KLAVIYO_API_KEY",
                    display_name="Klaviyo Private API Key",
                    description="Your Klaviyo Private API Key for API authentication",
                    required=True,
                    sensitive=True,
                    sample_format="pk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                    about_url="https://www.klaviyo.com/settings/account/api-keys",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://a.klaviyo.com/api/lists",
                method="GET",
                headers={
                    "Authorization": "Klaviyo-API-Key {api_key}",
                    "Accept": "application/json",
                    "revision": "2024-10-15",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["data"]
                ),
                cost_level="minimal",
                description="Validates Private API Key by listing accessible lists",
            ),
        ),
    ],
)
