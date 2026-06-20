"""Gamma integration manifest."""
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


_TEST_HEADERS = {"X-API-KEY": "{api_key}"}
_TEST_SUCCESS = SuccessIndicators(status_codes=[200])


manifest = IntegrationManifest(
    name="gamma",
    display_name="Gamma",
    description=(
        "Integrate Gamma into the workflow. Can generate presentations, "
        "documents, webpages, and social posts from text, create from "
        "templates, check generation status, and browse themes and folders."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:gamma-themed",
    app_url="https://gamma.app",
    categories=["Marketing & Advertising", "document-processing", "content-management"],
    actions=[
        ActionDefinition(
            name="generate",
            description=(
                "Generate a new Gamma presentation, document, webpage, or "
                "social post from text input."
            ),
            parameters={
                "input_text": ParameterDef(
                    type="string",
                    description=(
                        "Text and image URLs used to generate your gamma "
                        "(1-100,000 tokens)"
                    ),
                    required=True,
                ),
                "text_mode": ParameterDef(
                    type="string",
                    description=(
                        "How to handle input text: generate (AI expands), condense "
                        "(AI summarizes), or preserve (keep as-is)"
                    ),
                    required=True,
                ),
                "format": ParameterDef(
                    type="string",
                    description=(
                        "Output format: presentation, document, webpage, or "
                        "social (default: presentation)"
                    ),
                ),
                "theme_id": ParameterDef(
                    type="string",
                    description="Custom Gamma workspace theme ID (use list_themes to find themes)",
                ),
                "num_cards": ParameterDef(
                    type="integer",
                    description=(
                        "Number of cards/slides to generate "
                        "(1-60 for Pro, 1-75 for Ultra; default: 10)"
                    ),
                ),
                "card_split": ParameterDef(
                    type="string",
                    description="How to split content into cards: auto or inputTextBreaks",
                ),
                "card_dimensions": ParameterDef(
                    type="string",
                    description=(
                        "Card aspect ratio. Presentation: fluid, 16x9, 4x3. "
                        "Document: fluid, pageless, letter, a4. Social: 1x1, 4x5, 9x16"
                    ),
                ),
                "additional_instructions": ParameterDef(
                    type="string",
                    description="Additional instructions for the AI generation (max 2000 chars)",
                ),
                "export_as": ParameterDef(
                    type="string",
                    description="Automatically export the generated gamma as pdf or pptx",
                ),
                "folder_ids": ParameterDef(
                    type="string",
                    description="Comma-separated folder IDs to store the generated gamma in",
                ),
                "text_amount": ParameterDef(
                    type="string",
                    description="Amount of text per card: brief, medium, detailed, or extensive",
                ),
                "text_tone": ParameterDef(
                    type="string",
                    description='Tone of the generated text, e.g. "professional" (max 500 chars)',
                ),
                "text_audience": ParameterDef(
                    type="string",
                    description='Target audience, e.g. "executives", "students" (max 500 chars)',
                ),
                "text_language": ParameterDef(
                    type="string",
                    description="Language code for the generated text (default: en)",
                ),
                "image_source": ParameterDef(
                    type="string",
                    description=(
                        "Where to source images: aiGenerated, pictographic, unsplash, "
                        "webAllImages, webFreeToUse, webFreeToUseCommercially, giphy, "
                        "placeholder, or noImages"
                    ),
                ),
                "image_model": ParameterDef(
                    type="string",
                    description="AI image generation model to use when image_source is aiGenerated",
                ),
                "image_style": ParameterDef(
                    type="string",
                    description='Style directive for AI-generated images, e.g. "watercolor"',
                ),
            },
        ),
        ActionDefinition(
            name="generate_from_template",
            description="Generate a new Gamma by adapting an existing template with a prompt.",
            parameters={
                "gamma_id": ParameterDef(
                    type="string",
                    description="The ID of the template gamma to adapt",
                    required=True,
                ),
                "prompt": ParameterDef(
                    type="string",
                    description="Instructions for how to adapt the template (1-100,000 tokens)",
                    required=True,
                ),
                "theme_id": ParameterDef(
                    type="string",
                    description="Custom Gamma workspace theme ID to apply",
                ),
                "export_as": ParameterDef(
                    type="string",
                    description="Automatically export the generated gamma as pdf or pptx",
                ),
                "folder_ids": ParameterDef(
                    type="string",
                    description="Comma-separated folder IDs to store the generated gamma in",
                ),
                "image_model": ParameterDef(
                    type="string",
                    description="AI image generation model to use when image_source is aiGenerated",
                ),
                "image_style": ParameterDef(
                    type="string",
                    description='Style directive for AI-generated images, e.g. "watercolor"',
                ),
            },
        ),
        ActionDefinition(
            name="check_status",
            description=(
                "Check the status of a Gamma generation job. Returns the gamma "
                "URL when completed, or error details if failed."
            ),
            parameters={
                "generation_id": ParameterDef(
                    type="string",
                    description="The generation ID returned by generate or generate_from_template",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_themes",
            description=(
                "List available themes in your Gamma workspace. Returns theme "
                "IDs, names, and keywords for styling."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Search query to filter themes by name (case-insensitive)",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of themes to return per page (max 50)",
                ),
                "after": ParameterDef(
                    type="string",
                    description="Pagination cursor from a previous response (next_cursor)",
                ),
            },
        ),
        ActionDefinition(
            name="list_folders",
            description=(
                "List available folders in your Gamma workspace. Returns folder "
                "IDs and names for organizing generated content."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Search query to filter folders by name (case-sensitive)",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of folders to return per page (max 50)",
                ),
                "after": ParameterDef(
                    type="string",
                    description="Pagination cursor from a previous response (next_cursor)",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Gamma API key",
            setup_instructions=[
                "Sign in to Gamma with a Pro, Ultra, Teams, or Business plan",
                "Open Account Settings and navigate to the 'API Keys' section",
                "Create a new API key (format: sk-gamma-xxxxxxxx) or copy an existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="GAMMA_API_KEY",
                    display_name="Gamma API Key",
                    description="Your Gamma API key from Account Settings > API Keys",
                    required=True,
                    sensitive=True,
                    sample_format="sk-gamma-xxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://developers.gamma.app/",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://public-api.gamma.app/v1.0/themes",
                method="GET",
                headers=_TEST_HEADERS,
                params={"limit": "1"},
                success_indicators=_TEST_SUCCESS,
                cost_level="free",
                description="Validates the API key by listing one workspace theme",
            ),
        ),
    ],
)
