"""New Relic integration manifest.

New Relic exposes its observability data through NerdGraph, a single
GraphQL endpoint. Every action POSTs a GraphQL document to that endpoint
authenticated with a user API key sent in the ``API-Key`` header.
"""
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


_REGION_PARAM = ParameterDef(
    type="string",
    description="New Relic data center region: 'us' (default) or 'eu'",
    default="us",
)


manifest = IntegrationManifest(
    name="new_relic",
    display_name="New Relic",
    description=(
        "Integrate New Relic into workflows. Run NRQL queries, search monitored "
        "entities, fetch entity details, and record deployment change events via "
        "the NerdGraph GraphQL API."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:new_relic-themed",
    app_url="https://newrelic.com",
    categories=["Monitoring & Observability", "monitoring", "observability"],
    actions=[
        ActionDefinition(
            name="nrql_query",
            description="Run a NRQL query against a New Relic account using NerdGraph.",
            parameters={
                "account_id": ParameterDef(
                    type="integer",
                    description="New Relic account ID to query",
                    required=True,
                ),
                "nrql": ParameterDef(
                    type="string",
                    description="NRQL query to execute",
                    required=True,
                ),
                "region": _REGION_PARAM,
                "timeout": ParameterDef(
                    type="integer",
                    description="Optional query timeout in seconds",
                ),
            },
        ),
        ActionDefinition(
            name="search_entities",
            description=(
                "Search New Relic entities by name, GUID, domain type, tags, or "
                "reporting state."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description=(
                        'Entity search query, e.g. name like "api" or '
                        'domainType = "APM-APPLICATION"'
                    ),
                    required=True,
                ),
                "region": _REGION_PARAM,
                "cursor": ParameterDef(
                    type="string",
                    description="Pagination cursor from a previous entity search",
                ),
            },
        ),
        ActionDefinition(
            name="get_entity",
            description="Fetch a New Relic entity by GUID.",
            parameters={
                "guid": ParameterDef(
                    type="string",
                    description="Entity GUID",
                    required=True,
                ),
                "region": _REGION_PARAM,
            },
        ),
        ActionDefinition(
            name="create_deployment_event",
            description="Record a deployment change event in New Relic change tracking.",
            parameters={
                "entity_guid": ParameterDef(
                    type="string",
                    description="GUID of the entity associated with the deployment",
                    required=True,
                ),
                "version": ParameterDef(
                    type="string",
                    description="Deployment version, release name, or commit SHA",
                    required=True,
                ),
                "region": _REGION_PARAM,
                "short_description": ParameterDef(
                    type="string",
                    description="Short description of the deployment",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Longer deployment description",
                ),
                "changelog": ParameterDef(
                    type="string",
                    description="Deployment changelog text or URL",
                ),
                "commit": ParameterDef(
                    type="string",
                    description="Commit SHA or identifier associated with the deployment",
                ),
                "deep_link": ParameterDef(
                    type="string",
                    description="URL to the deployment, build, or release details",
                ),
                "user": ParameterDef(
                    type="string",
                    description="User or automation that performed the deployment",
                ),
                "group_id": ParameterDef(
                    type="string",
                    description="Optional group ID to correlate related changes",
                ),
                "custom_attributes": ParameterDef(
                    type="object",
                    description=(
                        "Custom change event metadata as key-value pairs with string, "
                        "number, or boolean values"
                    ),
                ),
                "deployment_type": ParameterDef(
                    type="string",
                    description=(
                        "Deployment type: 'basic', 'blue green', 'canary', 'rolling', "
                        "or 'shadow'"
                    ),
                    default="basic",
                ),
                "timestamp": ParameterDef(
                    type="integer",
                    description="Event timestamp in milliseconds since Unix epoch",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your New Relic user API key",
            setup_instructions=[
                "Sign in to New Relic at https://one.newrelic.com",
                "Open the user menu and go to 'API keys'",
                "Create a new 'User' key (its value starts with 'NRAK-')",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="NEW_RELIC_API_KEY",
                    display_name="New Relic User API Key",
                    description="Your New Relic user API key (starts with 'NRAK-')",
                    required=True,
                    sensitive=True,
                    sample_format="NRAK-<your-user-key>",
                    about_url="https://docs.newrelic.com/docs/apis/intro-apis/new-relic-api-keys/",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.newrelic.com/graphql",
                method="POST",
                headers={
                    "API-Key": "{api_key}",
                    "Content-Type": "application/json",
                },
                body={"query": "{ actor { user { name } } }"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates the API key with a minimal NerdGraph user query",
            ),
        ),
    ],
)
