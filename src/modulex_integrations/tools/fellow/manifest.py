"""Fellow integration manifest."""
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
    name="fellow",
    display_name="Fellow",
    description="Meeting productivity platform for notes, action items, and meeting management",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:fellow-themed",
    app_url="https://fellow.ai",
    categories=["Productivity & Collaboration", "meetings"],
    actions=[
        ActionDefinition(
            name="archive_action_item",
            description="Archive an action item",
            parameters={
                "action_item_id": ParameterDef(
                    type="string",
                    description="The ID of the action item to archive",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="complete_action_item",
            description="Complete an action item",
            parameters={
                "action_item_id": ParameterDef(
                    type="string",
                    description="The ID of the action item to mark as complete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_note_by_id",
            description="Get a note by its ID",
            parameters={
                "note_id": ParameterDef(
                    type="string",
                    description="The ID of the note to retrieve",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Fellow API key and workspace subdomain",
            setup_instructions=[
                "Sign in to your Fellow workspace at https://<subdomain>.fellow.app",
                "Navigate to Settings > Integrations > API",
                "Generate a new API key or copy your existing one",
                "Note your workspace subdomain (the part before .fellow.app in your URL)",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="FELLOW_SUBDOMAIN",
                    display_name="Workspace Subdomain",
                    description="Your Fellow workspace subdomain (the part before .fellow.app)",
                    required=True,
                    sensitive=False,
                    sample_format="mycompany",
                    about_url="https://fellow.app",
                ),
                EnvVar(
                    name="FELLOW_API_KEY",
                    display_name="API Key",
                    description="Your Fellow API key from Settings > Integrations > API",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://developers.fellow.ai",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://{subdomain}.fellow.app/api/v1/note",
                method="GET",
                headers={"x-api-key": "{api_key}"},
                params={"limit": "1"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="free",
                description="Validates credentials by listing notes with limit=1",
            ),
        ),
    ],
)
