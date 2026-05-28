"""Reflect integration manifest."""
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
    name="reflect",
    display_name="Reflect",
    description="Note-taking and knowledge management via the Reflect API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:reflect-themed",
    app_url="https://reflect.app",
    categories=["Productivity & Collaboration", "note-taking", "knowledge-management"],
    actions=[
        ActionDefinition(
            name="append_daily_note",
            description="Append to a daily note",
            parameters={
                "graph_id": ParameterDef(
                    type="string",
                    description="The graph identifier",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Text to append to the daily note",
                    required=True,
                ),
                "list_name": ParameterDef(
                    type="string",
                    description="Name of the list to append to",
                ),
                "date": ParameterDef(
                    type="string",
                    description="Date of the daily note in ISO 8601 format. Defaults to today.",
                ),
            },
        ),
        ActionDefinition(
            name="create_link",
            description="Create a new link",
            parameters={
                "graph_id": ParameterDef(
                    type="string",
                    description="The graph identifier",
                    required=True,
                ),
                "url": ParameterDef(
                    type="string",
                    description="The URL of the link to create",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The link title",
                ),
                "description": ParameterDef(
                    type="string",
                    description="The link description",
                ),
            },
        ),
        ActionDefinition(
            name="get_user",
            description="Retieves information about the authenticated user",
            parameters={},
        ),
        ActionDefinition(
            name="list_graph_id_options",
            description="Retrieves available options for the GraphId field",
            parameters={},
        ),
        ActionDefinition(
            name="list_links",
            description="Retieve all links for a graph",
            parameters={
                "graph_id": ParameterDef(
                    type="string",
                    description="The graph identifier",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Reflect OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="REFLECT_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Reflect OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://reflect.app/developer",
                ),
                EnvVar(
                    name="REFLECT_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Reflect OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://reflect.app/developer",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://reflect.app/oauth/authorize",
                token_url="https://reflect.app/oauth/token",
                scopes=[],
            ),
            test_endpoint=TestEndpoint(
                url="https://reflect.app/api/users/me",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["uid"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching authenticated user info",
            ),
        ),
    ],
)
