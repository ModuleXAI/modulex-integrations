"""Postman integration manifest."""
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
    name="postman",
    display_name="Postman",
    description="API development and testing platform for building, monitoring, and managing APIs",
    version="1.0.0",
    author="ModuleX",
    logo="logos:postman-icon",
    app_url="https://www.postman.com",
    categories=["Developer Tools & Infrastructure", "api-testing"],
    actions=[
        ActionDefinition(
            name="create_environment",
            description="Create a new environment in Postman with optional variables",
            parameters={
                "environment_name": ParameterDef(
                    type="string",
                    description="The name for the new environment",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="The ID of the workspace to create the environment in",
                ),
                "variables": ParameterDef(
                    type="array",
                    description="List of variable objects with keys: key (string), value (string), enabled (boolean), type ('secret' or 'default')",
                ),
            },
        ),
        ActionDefinition(
            name="list_workspace_id_options",
            description="List available workspaces with their IDs and names",
            parameters={},
        ),
        ActionDefinition(
            name="run_monitor",
            description="Run a specific monitor in Postman",
            parameters={
                "monitor_id": ParameterDef(
                    type="string",
                    description="The ID of the monitor to run",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="update_variable",
            description="Update a specific environment variable in Postman",
            parameters={
                "environment_id": ParameterDef(
                    type="string",
                    description="The ID of the environment containing the variable",
                    required=True,
                ),
                "variable": ParameterDef(
                    type="string",
                    description="The variable key (name) to update",
                    required=True,
                ),
                "variable_value": ParameterDef(
                    type="string",
                    description="The new value for the variable",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="The ID of the workspace containing the environment",
                ),
                "variable_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the variable is enabled or not",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Postman API key",
            setup_instructions=[
                "Go to https://web.postman.co and sign in",
                "Click your avatar in the top-right, then select Settings",
                "Navigate to the 'API Keys' tab",
                "Generate a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="POSTMAN_API_KEY",
                    display_name="Postman API Key",
                    description="Your Postman API key from web.postman.co/settings/me/api-keys",
                    required=True,
                    sensitive=True,
                    sample_format="PMAK-xxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://web.postman.co/settings/me/api-keys",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.getpostman.com/me",
                method="GET",
                headers={"X-Api-Key": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["user"],
                ),
                cost_level="free",
                description="Validates the API key by fetching the current user",
            ),
        ),
    ],
)
