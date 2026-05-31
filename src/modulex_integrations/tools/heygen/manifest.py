"""HeyGen integration manifest."""
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
    name="heygen",
    display_name="HeyGen",
    description="AI video generation platform for creating talking avatar videos",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:heygen",
    app_url="https://www.heygen.com",
    categories=["AI", "Video", "Content Creation"],
    actions=[
        ActionDefinition(
            name="create_talking_photo",
            description="Creates a talking photo video from a provided image, text, and voice",
            parameters={
                "talking_photo_id": ParameterDef(
                    type="string",
                    description="Identifier of the talking photo to use",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="The text that the character will speak",
                    required=True,
                ),
                "voice_id": ParameterDef(
                    type="string",
                    description="Identifier of the voice to use",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="Title of the video",
                ),
                "test": ParameterDef(
                    type="boolean",
                    description="Set to true to use test mode (no credits charged, watermark added)",
                ),
                "caption": ParameterDef(
                    type="boolean",
                    description="Set to true to create video with captions",
                ),
                "scale": ParameterDef(
                    type="string",
                    description="Talking photo scale, value between 0 and 2.0 (default 1.0)",
                ),
                "talking_photo_style": ParameterDef(
                    type="string",
                    description="Talking photo crop style: square, circle",
                ),
                "talking_style": ParameterDef(
                    type="string",
                    description="Talking photo talking style: stable, expressive",
                ),
                "expression": ParameterDef(
                    type="string",
                    description="Talking photo expression style: default, happy",
                ),
                "super_resolution": ParameterDef(
                    type="boolean",
                    description="Whether to enhance the photo image",
                ),
                "matting": ParameterDef(
                    type="boolean",
                    description="Whether to apply matting to the photo",
                ),
            },
        ),
        ActionDefinition(
            name="create_video_from_template",
            description="Generates a video from a selected template with optional variable overrides",
            parameters={
                "template_id": ParameterDef(
                    type="string",
                    description="Identifier of the template to use",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="Title of the video",
                ),
                "test": ParameterDef(
                    type="boolean",
                    description="Set to true to use test mode (no credits charged, watermark added)",
                ),
                "caption": ParameterDef(
                    type="boolean",
                    description="Set to true to create video with captions",
                ),
                "variables": ParameterDef(
                    type="object",
                    description="Template variable overrides as a JSON object where keys are variable names and values are objects with variable properties",
                ),
            },
        ),
        ActionDefinition(
            name="list_custom_events_options",
            description="Retrieves available options for webhook custom events",
            parameters={},
        ),
        ActionDefinition(
            name="list_voice_id_options",
            description="Retrieves available voice options for video generation",
            parameters={},
        ),
        ActionDefinition(
            name="retrieve_video_link",
            description="Fetches the status and download link for a specific HeyGen video",
            parameters={
                "video_id": ParameterDef(
                    type="string",
                    description="Identifier of the HeyGen video to retrieve",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your HeyGen API key",
            setup_instructions=[
                "Go to https://app.heygen.com and sign in",
                "Navigate to Settings > API",
                "Copy your API key",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="HEYGEN_API_KEY",
                    display_name="HeyGen API Key",
                    description="Your HeyGen API key from app.heygen.com/settings",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://app.heygen.com/settings",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.heygen.com/v2/voices",
                method="GET",
                headers={"X-Api-Key": "{api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates the API key by listing available voices",
            ),
        ),
    ],
)
