"""Mintlify integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="mintlify",
    display_name="Mintlify",
    description="Documentation platform with AI-powered assistant, semantic search, and project update triggers.",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:mintlify",
    app_url="https://www.mintlify.com",
    categories=["Developer Tools & Infrastructure", "documentation"],
    actions=[
        ActionDefinition(
            name="chat_with_assistant",
            description="Generates a response message from the assistant for the specified domain.",
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="The domain identifier from your domain.mintlify.app URL. Can be found in the top left of your dashboard.",
                    required=True,
                ),
                "fp": ParameterDef(
                    type="string",
                    description="Browser fingerprint or arbitrary string identifier for message tracking.",
                    required=True,
                ),
                "message": ParameterDef(
                    type="string",
                    description="The content of the message to send to the assistant.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_documentation",
            description="Perform semantic and keyword searches across your documentation.",
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="The domain identifier from your domain.mintlify.app URL. Can be found in the top left of your dashboard.",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="The search query to execute against your documentation content.",
                    required=True,
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of search results to return. Defaults to 10 if not specified.",
                ),
                "version": ParameterDef(
                    type="string",
                    description="Filter results by documentation version.",
                ),
                "language": ParameterDef(
                    type="string",
                    description="Filter results by content language.",
                ),
            },
        ),
        ActionDefinition(
            name="trigger_update",
            description="Trigger an update for a project.",
            parameters={},
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Mintlify API Keys",
            description=(
                "Authenticate using Mintlify assistant API key, admin API key, "
                "and project ID. Different actions use different credentials."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="MINTLIFY_ASSISTANT_API_KEY",
                    display_name="Assistant API Key",
                    description="Your Mintlify Assistant API key for chat and search endpoints.",
                    required=True,
                    sensitive=True,
                    about_url="https://dashboard.mintlify.com",
                ),
                EnvVar(
                    name="MINTLIFY_ADMIN_API_KEY",
                    display_name="Admin API Key",
                    description="Your Mintlify Admin API key for triggering project updates.",
                    required=True,
                    sensitive=True,
                    about_url="https://dashboard.mintlify.com",
                ),
                EnvVar(
                    name="MINTLIFY_PROJECT_ID",
                    display_name="Project ID",
                    description="Your Mintlify project ID used for update triggers.",
                    required=True,
                    sensitive=False,
                    about_url="https://dashboard.mintlify.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api-dsc.mintlify.com/v1/chat/{MINTLIFY_PROJECT_ID}/topic",
                method="POST",
                headers={
                    "Authorization": "Bearer {MINTLIFY_ASSISTANT_API_KEY}",
                    "Content-Type": "application/json",
                },
                body={"messages": []},
                # Auth-correct: 200 (topic returned) or 400 (empty messages
                #   rejected — but auth was accepted).
                # Auth-wrong: 401/403.
                success_indicators=SuccessIndicators(status_codes=[200, 400]),
                cost_level="minimal",
                description=(
                    "Validates the assistant API key + project ID by "
                    "hitting the Chat Topic endpoint with an empty "
                    "message list. Auth pass returns 200 or 400; auth "
                    "fail returns 401/403."
                ),
            ),
        ),
    ],
)
