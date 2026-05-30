"""Cogmento integration manifest."""
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
    name="cogmento",
    display_name="Cogmento",
    description="CRM platform for managing contacts, deals, and tasks",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:cogmento-themed",
    app_url="https://www.cogmento.com",
    categories=["CRM", "Sales", "Productivity"],
    actions=[
        ActionDefinition(
            name="create_contact",
            description="Create a new contact in Cogmento CRM",
            parameters={
                "first_name": ParameterDef(
                    type="string",
                    description="First name of the contact",
                    required=True,
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Last name of the contact",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="Email address of the contact",
                ),
                "phone": ParameterDef(
                    type="string",
                    description="Phone number of the contact",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Description of the contact",
                ),
                "tags": ParameterDef(
                    type="array",
                    description="List of tags (strings) associated with the contact",
                ),
                "do_not_call": ParameterDef(
                    type="boolean",
                    description="Set to true to mark the contact as Do Not Call",
                ),
                "do_not_text": ParameterDef(
                    type="boolean",
                    description="Set to true to mark the contact as Do Not Text",
                ),
                "do_not_email": ParameterDef(
                    type="boolean",
                    description="Set to true to mark the contact as Do Not Email",
                ),
            },
        ),
        ActionDefinition(
            name="create_deal",
            description="Create a new deal in Cogmento CRM",
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="The title of the deal",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="A description of the deal",
                ),
                "assignee_ids": ParameterDef(
                    type="array",
                    description="List of user IDs (strings) to assign to the deal",
                ),
                "tags": ParameterDef(
                    type="array",
                    description="List of tags (strings) associated with the deal",
                ),
                "close_date": ParameterDef(
                    type="string",
                    description="The date the deal was completed (format: YYYY-MM-DD)",
                ),
                "product_ids": ParameterDef(
                    type="array",
                    description="List of product IDs (strings) to include in the deal",
                ),
                "amount": ParameterDef(
                    type="string",
                    description="The final deal value (numeric string)",
                ),
            },
        ),
        ActionDefinition(
            name="create_task",
            description="Create a new task in Cogmento CRM",
            parameters={
                "title": ParameterDef(
                    type="string",
                    description="The title of the task",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="A description of the task",
                ),
                "due_date": ParameterDef(
                    type="string",
                    description="The task's deadline (format: YYYY-MM-DD)",
                ),
                "assignee_ids": ParameterDef(
                    type="array",
                    description="List of user IDs (strings) to assign to the task",
                ),
                "deal_id": ParameterDef(
                    type="string",
                    description="Identifier of a deal to associate with the task",
                ),
                "contact_id": ParameterDef(
                    type="string",
                    description="Identifier of a contact to associate with the task",
                ),
            },
        ),
        ActionDefinition(
            name="list_user_ids_options",
            description="Retrieve available user options for assignment fields",
            parameters={},
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Cogmento OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="COGMENTO_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Cogmento OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                ),
                EnvVar(
                    name="COGMENTO_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Cogmento OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://www.cogmento.com/oauth/authorize",
                token_url="https://www.cogmento.com/oauth/token",
                scopes=[],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.cogmento.com/api/1/auth/user",
                method="GET",
                headers={
                    "Authorization": "Token {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching authenticated user info",
            ),
        ),
    ],
)
