"""Mem0 integration manifest."""
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


_TEST_HEADERS = {
    "Authorization": "Token {api_key}",
    "Content-Type": "application/json",
}
_TEST_BODY = {"filters": {"user_id": "modulex-credential-test"}, "page": 1, "page_size": 1}
_TEST_SUCCESS = SuccessIndicators(status_codes=[200])


manifest = IntegrationManifest(
    name="mem0",
    display_name="Mem0",
    description=(
        "Persistent agent memory management — add, search, and retrieve "
        "long-term memories so AI agents can recall user context, "
        "preferences, and prior conversations across sessions."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:mem0-themed",
    app_url="https://mem0.ai",
    categories=["AI & Machine Learning", "knowledge-base", "agentic"],
    actions=[
        ActionDefinition(
            name="add_memories",
            description="Add memories to Mem0 for persistent storage and retrieval.",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description=(
                        'User ID associated with the memory '
                        '(e.g., "user_123", "alice@example.com")'
                    ),
                    required=True,
                ),
                "messages": ParameterDef(
                    type="array",
                    description=(
                        "Array of message objects with role and content "
                        '(e.g., [{"role": "user", "content": "Hello"}])'
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_memories",
            description="Search for memories in Mem0 using semantic search.",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description=(
                        'User ID to search memories for '
                        '(e.g., "user_123", "alice@example.com")'
                    ),
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description=(
                        'Search query to find relevant memories '
                        '(e.g., "What are my favorite foods?")'
                    ),
                    required=True,
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return (e.g., 10, 50, 100)",
                    default=10,
                ),
            },
        ),
        ActionDefinition(
            name="get_memories",
            description="Retrieve memories from Mem0 by ID or filter criteria.",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description=(
                        'User ID to retrieve memories for '
                        '(e.g., "user_123", "alice@example.com")'
                    ),
                    required=True,
                ),
                "memory_id": ParameterDef(
                    type="string",
                    description='Specific memory ID to retrieve (e.g., "mem_abc123")',
                ),
                "start_date": ParameterDef(
                    type="string",
                    description='Start date for filtering by created_at (e.g., "2024-01-15")',
                ),
                "end_date": ParameterDef(
                    type="string",
                    description='End date for filtering by created_at (e.g., "2024-12-31")',
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return (e.g., 10, 50, 100)",
                    default=10,
                ),
                "page": ParameterDef(
                    type="integer",
                    description="Page number to retrieve for paginated list results",
                    default=1,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Mem0 API key",
            setup_instructions=[
                "Go to https://app.mem0.ai and sign up or log in",
                "Open the dashboard and navigate to the 'API Keys' section",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="MEM0_API_KEY",
                    display_name="Mem0 API Key",
                    description="Your Mem0 API key from app.mem0.ai",
                    required=True,
                    sensitive=True,
                    about_url="https://docs.mem0.ai/platform/quickstart",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.mem0.ai/v3/memories/",
                method="POST",
                headers=_TEST_HEADERS,
                body=_TEST_BODY,
                success_indicators=_TEST_SUCCESS,
                cost_level="free",
                description="Validates the API key with a minimal paginated list query (1 result)",
            ),
        ),
    ],
)
