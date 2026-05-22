"""Algolia integration manifest."""
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
    name="algolia",
    display_name="Algolia",
    description="Search and indexing platform for building fast, relevant search experiences",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:algolia-themed",
    app_url="https://www.algolia.com",
    categories=["Search", "Developer Tools & Infrastructure"],
    actions=[
        ActionDefinition(
            name="browse_records",
            description="Browse for records in the given index",
            parameters={
                "index_name": ParameterDef(
                    type="string",
                    description="The name of the Algolia index to browse",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="delete_records",
            description="Delete records from the given index by object IDs",
            parameters={
                "index_name": ParameterDef(
                    type="string",
                    description="The name of the Algolia index",
                    required=True,
                ),
                "record_ids": ParameterDef(
                    type="array",
                    description="List of object IDs (strings) to delete from the index",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_index_name_options",
            description="Retrieves available index names for the application",
            parameters={},
        ),
        ActionDefinition(
            name="save_records",
            description="Adds or updates records in the given index",
            parameters={
                "index_name": ParameterDef(
                    type="string",
                    description="The name of the Algolia index",
                    required=True,
                ),
                "records": ParameterDef(
                    type="array",
                    description="List of JSON objects to save. Each must have an 'objectID' field.",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Algolia API Credentials",
            description="Authenticate using your Algolia Application ID and API Key",
            setup_instructions=[
                "Go to https://dashboard.algolia.com and sign in",
                "Navigate to Settings > API Keys",
                "Copy your Application ID and Admin API Key",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="ALGOLIA_APPLICATION_ID",
                    display_name="Application ID",
                    description="Your Algolia Application ID from the dashboard",
                    required=True,
                    sensitive=False,
                    sample_format="ABCDEF1234",
                    about_url="https://dashboard.algolia.com/account/api-keys/all",
                ),
                EnvVar(
                    name="ALGOLIA_API_KEY",
                    display_name="Admin API Key",
                    description=(
                        "Your Algolia Admin API Key"
                        " (or a key with appropriate permissions)"
                    ),
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://dashboard.algolia.com/account/api-keys/all",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://{application_id}-dsn.algolia.net/1/indexes",
                method="GET",
                headers={
                    "X-Algolia-API-Key": "{api_key}",
                    "X-Algolia-Application-Id": "{application_id}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["items"],
                ),
                cost_level="free",
                description="Lists indices to validate credentials",
            ),
        ),
    ],
)
