"""Quiver integration manifest.

QuiverAI is an AI vector-graphics platform: it generates SVGs from text
prompts and vectorizes raster images into clean SVG output via the
``api.quiver.ai/v1`` REST API. Authentication is a single API key
(``Authorization: Bearer <key>``).
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


_TEST_HEADERS = {"Authorization": "Bearer {api_key}"}
_TEST_SUCCESS = SuccessIndicators(
    status_codes=[200],
    response_fields=["data"],
)


manifest = IntegrationManifest(
    name="quiver",
    display_name="Quiver",
    description=(
        "Generate SVG images from text prompts or vectorize raster images into "
        "SVGs using QuiverAI. Supports reference images, style instructions, and "
        "multiple output generation."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:quiver-themed",
    app_url="https://quiver.ai",
    categories=["AI & Machine Learning", "image-generation", "design"],
    actions=[
        ActionDefinition(
            name="text_to_svg",
            description="Generate SVG images from text prompts using QuiverAI.",
            parameters={
                "prompt": ParameterDef(
                    type="string",
                    description="A text description of the desired SVG",
                    required=True,
                ),
                "model": ParameterDef(
                    type="string",
                    description='The model to use for SVG generation (e.g. "arrow-1.1")',
                    default="arrow-1.1",
                ),
                "instructions": ParameterDef(
                    type="string",
                    description="Style or formatting guidance for the SVG output",
                ),
                "references": ParameterDef(
                    type="array",
                    description=(
                        "Reference image URLs to guide SVG generation (up to 4 for "
                        "arrow-1.1, 16 for arrow-1.1-max)"
                    ),
                ),
                "n": ParameterDef(
                    type="integer",
                    description="Number of SVGs to generate (1-16, default 1)",
                ),
                "temperature": ParameterDef(
                    type="number",
                    description="Sampling temperature (0-2, default 1)",
                ),
                "top_p": ParameterDef(
                    type="number",
                    description="Nucleus sampling probability (0-1, default 1)",
                ),
                "max_output_tokens": ParameterDef(
                    type="integer",
                    description="Maximum output tokens (1-65536)",
                ),
                "presence_penalty": ParameterDef(
                    type="number",
                    description="Token penalty for prior output (-2 to 2, default 0)",
                ),
            },
        ),
        ActionDefinition(
            name="image_to_svg",
            description="Convert raster images into vector SVG format using QuiverAI.",
            parameters={
                "image": ParameterDef(
                    type="string",
                    description="URL of the raster image to vectorize into SVG",
                    required=True,
                ),
                "model": ParameterDef(
                    type="string",
                    description='The model to use for vectorization (e.g. "arrow-1.1")',
                    default="arrow-1.1",
                ),
                "auto_crop": ParameterDef(
                    type="boolean",
                    description="Automatically crop the image to its dominant subject",
                ),
                "target_size": ParameterDef(
                    type="integer",
                    description="Square resize target in pixels (128-4096)",
                ),
                "temperature": ParameterDef(
                    type="number",
                    description="Sampling temperature (0-2, default 1)",
                ),
                "top_p": ParameterDef(
                    type="number",
                    description="Nucleus sampling probability (0-1, default 1)",
                ),
                "max_output_tokens": ParameterDef(
                    type="integer",
                    description="Maximum output tokens (1-65536)",
                ),
                "presence_penalty": ParameterDef(
                    type="number",
                    description="Token penalty for prior output (-2 to 2, default 0)",
                ),
            },
        ),
        ActionDefinition(
            name="list_models",
            description="List all available QuiverAI models.",
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your QuiverAI API key",
            setup_instructions=[
                "Go to https://quiver.ai and sign up or log in",
                "Open your account dashboard and navigate to API keys",
                "Create a new API key or copy your existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="QUIVER_API_KEY",
                    display_name="QuiverAI API Key",
                    description="Your QuiverAI API key from quiver.ai",
                    required=True,
                    sensitive=True,
                    about_url="https://docs.quiver.ai/getting-started/quickstart",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.quiver.ai/v1/models",
                method="GET",
                headers=_TEST_HEADERS,
                success_indicators=_TEST_SUCCESS,
                cost_level="free",
                description="Validates the API key by listing available models",
            ),
        ),
    ],
)
