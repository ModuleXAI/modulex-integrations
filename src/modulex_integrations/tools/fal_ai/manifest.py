"""fal.ai integration manifest."""
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
    name="fal_ai",
    display_name="fal.ai",
    description="Queue-based AI model inference via the fal.ai platform",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:fal_ai",
    app_url="https://fal.ai",
    categories=["AI & Machine Learning", "Generative AI"],
    actions=[
        ActionDefinition(
            name="add_request_to_queue",
            description="Adds a request to the queue for asynchronous processing, including specifying a webhook URL for receiving updates",
            parameters={
                "app_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the fal.ai app/model (e.g. 'lora', 'fast-sdxl')",
                    required=True,
                ),
                "data": ParameterDef(
                    type="object",
                    description="Input data for the model. Fields depend on the specific app/model being called",
                    required=True,
                ),
                "webhook_url": ParameterDef(
                    type="string",
                    description="Optional URL to receive webhook updates about the request status",
                ),
            },
        ),
        ActionDefinition(
            name="cancel_request",
            description="Cancels a request in the queue to stop a long-running task that is no longer needed",
            parameters={
                "app_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the fal.ai app/model",
                    required=True,
                ),
                "request_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the request to cancel",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_request_response",
            description="Gets the response of a completed request in the queue to retrieve results of an asynchronous task",
            parameters={
                "app_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the fal.ai app/model",
                    required=True,
                ),
                "request_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the request",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_request_status",
            description="Gets the status of a request in the queue to monitor the progress of an asynchronous task",
            parameters={
                "app_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the fal.ai app/model",
                    required=True,
                ),
                "request_id": ParameterDef(
                    type="string",
                    description="The unique identifier for the request",
                    required=True,
                ),
                "logs": ParameterDef(
                    type="boolean",
                    description="Whether to include logs in the status response",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your fal.ai API key",
            setup_instructions=[
                "Go to https://fal.ai/dashboard/keys and sign in",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="FAL_AI_API_KEY",
                    display_name="fal.ai API Key",
                    description="Your fal.ai API key from https://fal.ai/dashboard/keys",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://fal.ai/dashboard/keys",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://queue.fal.run/fal-ai/fast-sdxl/requests/test-nonexistent",
                method="GET",
                headers={"Authorization": "Key {api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200, 404, 422],
                    response_fields=[],
                ),
                cost_level="free",
                description="Validates the API key by attempting to fetch a request status (404 still proves auth is valid)",
            ),
        ),
    ],
)
