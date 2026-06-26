"""ElevenLabs integration manifest."""
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


def _test_endpoint(placeholder: str) -> TestEndpoint:
    return TestEndpoint(
        url="https://api.elevenlabs.io/v1/user/subscription",
        method="GET",
        headers={"xi-api-key": f"{{{placeholder}}}"},
        success_indicators=SuccessIndicators(
            status_codes=[200], response_fields=["tier"]
        ),
        cost_level="free",
        description="Validates API key by checking subscription status",
    )


manifest = IntegrationManifest(
    name="elevenlabs",
    display_name="ElevenLabs",
    description=(
        "AI voice generation, transcription, sound effects, voice cloning, "
        "and conversational AI agents. Uses the `elevenlabs` SDK."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:elevenlabs-themed",
    app_url="https://elevenlabs.io",
    categories=["AI & Machine Learning", "Audio", "Voice"],
    actions=[
        ActionDefinition(
            name="text_to_speech",
            description="Convert text to AI-generated speech audio (base64-encoded)",
            parameters={
                "text": ParameterDef(
                    type="string", description="Text to synthesize", required=True
                ),
                "voice_id": ParameterDef(type="string", description="Voice ID"),
                "voice_name": ParameterDef(
                    type="string", description="Voice name (alternative to voice_id)"
                ),
                "model_id": ParameterDef(
                    type="string",
                    description="TTS model ID",
                    default="eleven_multilingual_v2",
                ),
                "stability": ParameterDef(
                    type="number", description="Voice stability (0-1)", default=0.5
                ),
                "similarity_boost": ParameterDef(
                    type="number",
                    description="Voice similarity to original (0-1)",
                    default=0.75,
                ),
                "style": ParameterDef(
                    type="number",
                    description="Style exaggeration (0-1)",
                    default=0.0,
                ),
                "speed": ParameterDef(
                    type="number", description="Speech speed (0.7-1.2)", default=1.0
                ),
                "language": ParameterDef(
                    type="string",
                    description="ISO 639-1 language code",
                    default="en",
                ),
                "output_format": ParameterDef(
                    type="string",
                    description="Audio output format",
                    default="mp3_44100_128",
                ),
            },
        ),
        ActionDefinition(
            name="speech_to_text",
            description="Transcribe audio to text with optional speaker diarization",
            parameters={
                "audio_base64": ParameterDef(
                    type="string",
                    description="Base64-encoded audio (XOR with audio_url)",
                ),
                "audio_url": ParameterDef(
                    type="string", description="URL to audio file"
                ),
                "language_code": ParameterDef(
                    type="string", description="ISO 639-3 language code"
                ),
                "diarize": ParameterDef(
                    type="boolean", description="Identify speakers", default=False
                ),
            },
        ),
        ActionDefinition(
            name="text_to_sound_effects",
            description="Generate a custom sound effect from a text description",
            parameters={
                "text": ParameterDef(
                    type="string",
                    description="Sound description (e.g. 'thunder rumbling')",
                    required=True,
                ),
                "duration_seconds": ParameterDef(
                    type="number",
                    description="Duration (0.5-5 seconds)",
                    default=2.0,
                ),
                "output_format": ParameterDef(
                    type="string",
                    description="Audio output format",
                    default="mp3_44100_128",
                ),
            },
        ),
        ActionDefinition(
            name="search_voices",
            description="Search the ElevenLabs voice library",
            parameters={
                "search": ParameterDef(
                    type="string", description="Search term to filter voices"
                ),
                "sort": ParameterDef(
                    type="string",
                    description="created_at_unix or name",
                    default="name",
                ),
                "sort_direction": ParameterDef(
                    type="string", description="asc or desc", default="desc"
                ),
            },
        ),
        ActionDefinition(
            name="list_models",
            description="List all available TTS models",
            parameters={},
        ),
        ActionDefinition(
            name="get_voice",
            description="Get details for a specific voice",
            parameters={
                "voice_id": ParameterDef(
                    type="string", description="Voice ID", required=True
                ),
            },
        ),
        ActionDefinition(
            name="voice_clone",
            description="Create an instant voice clone from audio samples",
            parameters={
                "name": ParameterDef(
                    type="string", description="Voice name", required=True
                ),
                "audio_files_base64": ParameterDef(
                    type="array",
                    description="Base64-encoded audio samples",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string", description="Optional voice description"
                ),
            },
        ),
        ActionDefinition(
            name="isolate_audio",
            description="Isolate voice from background noise / music",
            parameters={
                "audio_base64": ParameterDef(
                    type="string", description="Base64-encoded audio"
                ),
                "audio_url": ParameterDef(
                    type="string", description="Audio URL (alternative to base64)"
                ),
            },
        ),
        ActionDefinition(
            name="check_subscription",
            description="Check current subscription tier + usage",
            parameters={},
        ),
        ActionDefinition(
            name="create_agent",
            description="Create a conversational AI agent",
            parameters={
                "name": ParameterDef(
                    type="string", description="Agent name", required=True
                ),
                "first_message": ParameterDef(
                    type="string",
                    description="Greeting message",
                    required=True,
                ),
                "system_prompt": ParameterDef(
                    type="string", description="System prompt", required=True
                ),
                "voice_id": ParameterDef(
                    type="string",
                    description="Voice ID",
                    default="cgSgspJ2msm6clMCkdW9",
                ),
                "language": ParameterDef(
                    type="string", description="ISO 639-1", default="en"
                ),
                "llm": ParameterDef(
                    type="string",
                    description="LLM to power the agent",
                    default="gemini-2.0-flash-001",
                ),
                "temperature": ParameterDef(
                    type="number", description="LLM temperature", default=0.5
                ),
                "max_tokens": ParameterDef(
                    type="integer", description="Max LLM tokens"
                ),
                "stability": ParameterDef(
                    type="number", description="Voice stability", default=0.5
                ),
                "similarity_boost": ParameterDef(
                    type="number", description="Voice similarity", default=0.8
                ),
                "max_duration_seconds": ParameterDef(
                    type="integer",
                    description="Max conversation duration",
                    default=300,
                ),
            },
        ),
        ActionDefinition(
            name="list_agents",
            description="List all conversational AI agents",
            parameters={},
        ),
        ActionDefinition(
            name="get_agent",
            description="Get a specific agent's configuration",
            parameters={
                "agent_id": ParameterDef(
                    type="string", description="Agent ID", required=True
                ),
            },
        ),
        ActionDefinition(
            name="add_knowledge_base_to_agent",
            description=(
                "Attach a knowledge base document (from URL, text, or file) "
                "to an agent"
            ),
            parameters={
                "agent_id": ParameterDef(
                    type="string", description="Agent ID", required=True
                ),
                "knowledge_base_name": ParameterDef(
                    type="string",
                    description="Display name for the KB document",
                    required=True,
                ),
                "url": ParameterDef(
                    type="string", description="Source URL (XOR text / file)"
                ),
                "text": ParameterDef(
                    type="string", description="Raw text content"
                ),
                "file_base64": ParameterDef(
                    type="string",
                    description="Base64 file (epub / pdf / docx / txt / html)",
                ),
            },
        ),
        ActionDefinition(
            name="list_conversations",
            description="List recorded conversations (optionally filtered by agent)",
            parameters={
                "agent_id": ParameterDef(
                    type="string", description="Filter by agent ID"
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Results per page (1-100)",
                    default=30,
                ),
            },
        ),
        ActionDefinition(
            name="get_conversation",
            description="Get a conversation's full transcript",
            parameters={
                "conversation_id": ParameterDef(
                    type="string",
                    description="Conversation ID",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your ElevenLabs API key",
            setup_environment_variables=[
                EnvVar(
                    name="ELEVENLABS_API_KEY",
                    display_name="ElevenLabs API Key",
                    description="Your ElevenLabs API key",
                    required=True,
                    sensitive=True,
                    sample_format="sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://elevenlabs.io/app/settings/api-keys",
                ),
            ],
            test_endpoint=_test_endpoint("api_key"),
        ),
    ],
)
