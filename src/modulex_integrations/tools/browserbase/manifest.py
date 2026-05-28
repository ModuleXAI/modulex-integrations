"""Browserbase integration manifest."""
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
    name="browserbase",
    display_name="Browserbase",
    description="Cloud browser infrastructure for running and managing headless browser sessions",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:browserbase",
    app_url="https://www.browserbase.com",
    categories=["Developer Tools & Infrastructure", "automation", "browser"],
    actions=[
        ActionDefinition(
            name="create_context",
            description="Creates a new context in Browserbase for persistent browser state",
            parameters={
                "project_id": ParameterDef(
                    type="string",
                    description="The ID of the Browserbase project",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_session",
            description="Creates a new browser session with specified settings",
            parameters={
                "project_id": ParameterDef(
                    type="string",
                    description="The ID of the Browserbase project",
                    required=True,
                ),
                "extension_id": ParameterDef(
                    type="string",
                    description="The uploaded Extension ID to load in the session",
                ),
                "browser_settings": ParameterDef(
                    type="object",
                    description="Settings for the session (e.g. fingerprint, viewport). See Browserbase docs for schema.",
                ),
                "timeout": ParameterDef(
                    type="integer",
                    description="Duration in seconds after which the session will automatically end. Min: 60, Max: 21600.",
                ),
                "keep_alive": ParameterDef(
                    type="boolean",
                    description="Set to true to keep the session alive even after disconnections",
                ),
                "proxies": ParameterDef(
                    type="array",
                    description="Array of proxy configuration objects. Each element should have type and optional geolocation fields.",
                ),
                "region": ParameterDef(
                    type="string",
                    description="The region where the session should run. One of: us-west-2, us-east-1, eu-central-1, ap-southeast-1.",
                ),
                "user_metadata": ParameterDef(
                    type="object",
                    description="Arbitrary user metadata to attach to the session",
                ),
            },
        ),
        ActionDefinition(
            name="list_projects",
            description="Lists all projects in the Browserbase account",
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Browserbase API key",
            setup_instructions=[
                "Go to https://www.browserbase.com and sign in",
                "Navigate to Settings > API Keys",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="BROWSERBASE_API_KEY",
                    display_name="Browserbase API Key",
                    description="Your Browserbase API key from the settings page",
                    required=True,
                    sensitive=True,
                    sample_format="bb_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://www.browserbase.com/settings",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.browserbase.com/v1/projects",
                method="GET",
                headers={"x-bb-api-key": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="free",
                description="Validates the API key by listing projects",
            ),
        ),
    ],
)
