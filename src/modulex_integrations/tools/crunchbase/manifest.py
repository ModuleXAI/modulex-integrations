"""Crunchbase integration manifest."""
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
    name="crunchbase",
    display_name="Crunchbase",
    description="Access Crunchbase company and organization data for business intelligence and research",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:crunchbase-themed",
    app_url="https://www.crunchbase.com",
    categories=["Business Intelligence", "Data", "Research"],
    actions=[
        ActionDefinition(
            name="get_organization",
            description="Retrieve details about an organization by UUID or permalink",
            parameters={
                "entity_id": ParameterDef(
                    type="string",
                    description="UUID or permalink of the organization to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_organizations",
            description="Search for organizations based on specified criteria",
            parameters={
                "field_ids": ParameterDef(
                    type="array",
                    description="Fields to include on the resulting entity (e.g. identifier, short_description, name, website_url)",
                    required=True,
                ),
                "query": ParameterDef(
                    type="array",
                    description="Array of query predicate objects for filtering organizations. Each object should have operator_id, type, values, and field_id keys.",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Crunchbase user key",
            setup_instructions=[
                "Go to https://data.crunchbase.com and sign in",
                "Navigate to your account settings or API key management",
                "Copy your user key",
                "Paste the key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="CRUNCHBASE_USER_KEY",
                    display_name="Crunchbase User Key",
                    description="Your Crunchbase API user key from data.crunchbase.com",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://data.crunchbase.com/docs/using-the-api",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.crunchbase.com/v4/data/entities/organizations/crunchbase",
                method="GET",
                headers={"X-cb-user-key": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["properties"],
                ),
                cost_level="minimal",
                description="Validates the API key by fetching the Crunchbase organization entity",
            ),
        ),
    ],
)
