"""ElevenLabs LangChain ``@tool`` functions.

Wraps the synchronous ``elevenlabs`` SDK inside async tool functions.
Key-based runtime convention (``api_key: str`` first arg) with a single
Bearer-authed ``api_key`` schema (bring-your-own-key).

15 actions across TTS, STT, sound effects, voice library / cloning /
isolation, subscription, and Conversational-AI (agents + knowledge
bases + conversations).

Audio binary helpers preserved verbatim from legacy:
- ``_get_audio_bytes`` accepts base64 OR URL; the URL path uses an
  async httpx client.
- ``_format_diarized_transcript`` walks the SDK's word-level output
  and groups consecutive words by speaker.
"""
from __future__ import annotations

import base64
import io
from datetime import datetime
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.elevenlabs.outputs import (
    AddKnowledgeBaseOutput,
    CheckSubscriptionOutput,
    CreateAgentOutput,
    GetAgentOutput,
    GetConversationOutput,
    GetVoiceOutput,
    IsolateAudioOutput,
    ListAgentsOutput,
    ListConversationsOutput,
    ListModelsOutput,
    ModelEntry,
    SearchVoicesOutput,
    SpeechToTextOutput,
    TextToSoundEffectsOutput,
    TextToSpeechOutput,
    VoiceCloneOutput,
    VoiceEntry,
)

__all__ = [
    "add_knowledge_base_to_agent",
    "check_subscription",
    "create_agent",
    "get_agent",
    "get_conversation",
    "get_voice",
    "isolate_audio",
    "list_agents",
    "list_conversations",
    "list_models",
    "search_voices",
    "speech_to_text",
    "text_to_sound_effects",
    "text_to_speech",
    "voice_clone",
]

DEFAULT_VOICE_ID = "cgSgspJ2msm6clMCkdW9"


def _client(api_key: str) -> Any:
    """Lazy-imported ElevenLabs SDK client."""
    from elevenlabs.client import ElevenLabs

    return ElevenLabs(api_key=api_key)


def _validate_key(api_key: str, action: str) -> str | None:
    if not api_key or not api_key.strip():
        return f"ElevenLabs API key is empty for {action}"
    return None


async def _fetch_audio(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


async def _resolve_audio(
    audio_base64: str | None, audio_url: str | None
) -> tuple[bytes | None, str | None]:
    """Return (bytes, error_message). Exactly one source required."""
    if audio_base64 and audio_url:
        return None, "Cannot specify both audio_base64 and audio_url. Choose one."
    if not audio_base64 and not audio_url:
        return None, "Must provide either audio_base64 or audio_url."
    try:
        if audio_base64:
            return base64.b64decode(audio_base64), None
        assert audio_url is not None
        return await _fetch_audio(audio_url), None
    except Exception as exc:
        return None, f"Failed to load audio: {exc}"


def _format_diarized(transcription: Any) -> str:
    """Walk the SDK's word-level output, grouping by speaker."""
    try:
        words = getattr(transcription, "words", None)
        if not words:
            return str(transcription.text)
        lines: list[str] = []
        current_speaker: str | None = None
        current_text: list[str] = []
        for word in words:
            word_speaker = getattr(word, "speaker_id", None)
            word_text = getattr(word, "text", None)
            word_type = getattr(word, "type", None)
            if not word_speaker or not word_text or word_type == "spacing":
                continue
            if current_speaker != word_speaker:
                if current_speaker and current_text:
                    label = current_speaker.upper().replace("_", " ")
                    lines.append(f"{label}: {' '.join(current_text)}")
                current_speaker = word_speaker
                current_text = [word_text.strip()]
            else:
                current_text.append(word_text.strip())
        if current_speaker and current_text:
            label = current_speaker.upper().replace("_", " ")
            lines.append(f"{label}: {' '.join(current_text)}")
        return "\n\n".join(lines)
    except Exception:
        return getattr(transcription, "text", "")


# --- Input schemas ---------------------------------------------------------


class TextToSpeechInput(BaseModel):
    text: str = Field(description="Text to synthesize")
    api_key: str = Field(description="ElevenLabs API key")
    voice_id: str | None = None
    voice_name: str | None = None
    model_id: str | None = "eleven_multilingual_v2"
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    speed: float = 1.0
    language: str = "en"
    output_format: str = "mp3_44100_128"


class SpeechToTextInput(BaseModel):
    api_key: str = Field(description="ElevenLabs API key")
    audio_base64: str | None = None
    audio_url: str | None = None
    language_code: str | None = None
    diarize: bool = False


class TextToSoundEffectsInput(BaseModel):
    text: str = Field(description="Sound effect description")
    api_key: str = Field(description="ElevenLabs API key")
    duration_seconds: float = 2.0
    output_format: str = "mp3_44100_128"


class SearchVoicesInput(BaseModel):
    api_key: str = Field(description="ElevenLabs API key")
    search: str | None = None
    sort: str = "name"
    sort_direction: str = "desc"


class ListModelsInput(BaseModel):
    api_key: str = Field(description="ElevenLabs API key")


class GetVoiceInput(BaseModel):
    voice_id: str = Field(description="Voice ID")
    api_key: str = Field(description="ElevenLabs API key")


class VoiceCloneInput(BaseModel):
    name: str = Field(description="Voice name")
    audio_files_base64: list[str] = Field(description="Base64-encoded audio samples")
    api_key: str = Field(description="ElevenLabs API key")
    description: str | None = None


class IsolateAudioInput(BaseModel):
    api_key: str = Field(description="ElevenLabs API key")
    audio_base64: str | None = None
    audio_url: str | None = None


class CheckSubscriptionInput(BaseModel):
    api_key: str = Field(description="ElevenLabs API key")


class CreateAgentInput(BaseModel):
    name: str = Field(description="Agent name")
    first_message: str = Field(description="Initial greeting")
    system_prompt: str = Field(description="System prompt")
    api_key: str = Field(description="ElevenLabs API key")
    voice_id: str | None = DEFAULT_VOICE_ID
    language: str = "en"
    llm: str = "gemini-2.0-flash-001"
    temperature: float = 0.5
    max_tokens: int | None = None
    stability: float = 0.5
    similarity_boost: float = 0.8
    max_duration_seconds: int = 300


class ListAgentsInput(BaseModel):
    api_key: str = Field(description="ElevenLabs API key")


class GetAgentInput(BaseModel):
    agent_id: str = Field(description="Agent ID")
    api_key: str = Field(description="ElevenLabs API key")


class AddKnowledgeBaseInput(BaseModel):
    agent_id: str = Field(description="Agent ID")
    knowledge_base_name: str = Field(description="KB display name")
    api_key: str = Field(description="ElevenLabs API key")
    url: str | None = None
    text: str | None = None
    file_base64: str | None = None


class ListConversationsInput(BaseModel):
    api_key: str = Field(description="ElevenLabs API key")
    agent_id: str | None = None
    page_size: int = 30


class GetConversationInput(BaseModel):
    conversation_id: str = Field(description="Conversation ID")
    api_key: str = Field(description="ElevenLabs API key")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=TextToSpeechInput)
@serialize_pydantic_return
async def text_to_speech(
    text: str,
    api_key: str,
    voice_id: str | None = None,
    voice_name: str | None = None,
    model_id: str | None = "eleven_multilingual_v2",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    style: float = 0.0,
    speed: float = 1.0,
    language: str = "en",
    output_format: str = "mp3_44100_128",
) -> TextToSpeechOutput:
    """Synthesize speech from text."""
    err = _validate_key(api_key, "text_to_speech")
    if err:
        return TextToSpeechOutput(success=False, error=err)
    if not text or not text.strip():
        return TextToSpeechOutput(
            success=False, error="Text is required for speech synthesis."
        )
    if voice_id and voice_name:
        return TextToSpeechOutput(
            success=False,
            error="Cannot specify both voice_id and voice_name. Choose one.",
        )
    try:
        client = _client(api_key)
        resolved_voice_id = voice_id
        voice_info: dict[str, Any] | None = None
        if voice_name:
            voices = client.voices.search(search=voice_name)
            if not voices.voices:
                return TextToSpeechOutput(
                    success=False, error=f"No voice found with name: {voice_name}"
                )
            voice = next(
                (v for v in voices.voices if v.name == voice_name),
                voices.voices[0],
            )
            resolved_voice_id = voice.voice_id
            voice_info = {"id": voice.voice_id, "name": voice.name}
        elif voice_id:
            voice = client.voices.get(voice_id=voice_id)
            voice_info = {"id": voice.voice_id, "name": voice.name}
        if not resolved_voice_id:
            resolved_voice_id = DEFAULT_VOICE_ID
            voice_info = {"id": DEFAULT_VOICE_ID, "name": "Default Voice"}
        if model_id is None:
            model_id = (
                "eleven_flash_v2_5"
                if language in ("hu", "no", "vi")
                else "eleven_multilingual_v2"
            )

        audio_data = client.text_to_speech.convert(
            text=text,
            voice_id=resolved_voice_id,
            model_id=model_id,
            output_format=output_format,
            voice_settings={
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": True,
                "speed": speed,
            },
        )
        audio_bytes = b"".join(audio_data)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:
        return TextToSpeechOutput(
            success=False, error=f"Text-to-speech failed: {exc}"
        )
    return TextToSpeechOutput(
        success=True,
        audio_base64=audio_b64,
        voice=voice_info,
        model_id=model_id,
        format=output_format,
        text_length=len(text),
        audio_size_bytes=len(audio_bytes),
    )


@tool(args_schema=SpeechToTextInput)
@serialize_pydantic_return
async def speech_to_text(
    api_key: str,
    audio_base64: str | None = None,
    audio_url: str | None = None,
    language_code: str | None = None,
    diarize: bool = False,
) -> SpeechToTextOutput:
    """Transcribe audio to text (optionally with diarization)."""
    err = _validate_key(api_key, "speech_to_text")
    if err:
        return SpeechToTextOutput(success=False, error=err)
    audio_bytes, e = await _resolve_audio(audio_base64, audio_url)
    if audio_bytes is None:
        return SpeechToTextOutput(success=False, error=e)
    try:
        client = _client(api_key)
        transcription = client.speech_to_text.convert(
            model_id="scribe_v1",
            file=audio_bytes,
            language_code=language_code if language_code else None,
            enable_logging=True,
            diarize=diarize,
            tag_audio_events=True,
        )
        text = (
            _format_diarized(transcription) if diarize else transcription.text
        )
    except Exception as exc:
        return SpeechToTextOutput(
            success=False, error=f"Speech-to-text failed: {exc}"
        )
    return SpeechToTextOutput(
        success=True,
        transcript=text,
        diarized=diarize,
        language_detected=getattr(transcription, "language_code", language_code),
    )


@tool(args_schema=TextToSoundEffectsInput)
@serialize_pydantic_return
async def text_to_sound_effects(
    text: str,
    api_key: str,
    duration_seconds: float = 2.0,
    output_format: str = "mp3_44100_128",
) -> TextToSoundEffectsOutput:
    """Generate a custom sound effect from a text description."""
    err = _validate_key(api_key, "text_to_sound_effects")
    if err:
        return TextToSoundEffectsOutput(success=False, error=err)
    if duration_seconds < 0.5 or duration_seconds > 5:
        return TextToSoundEffectsOutput(
            success=False, error="Duration must be between 0.5 and 5 seconds."
        )
    try:
        client = _client(api_key)
        audio_data = client.text_to_sound_effects.convert(
            text=text,
            output_format=output_format,
            duration_seconds=duration_seconds,
        )
        audio_bytes = b"".join(audio_data)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:
        return TextToSoundEffectsOutput(
            success=False, error=f"Sound effect generation failed: {exc}"
        )
    return TextToSoundEffectsOutput(
        success=True,
        audio_base64=audio_b64,
        description=text,
        duration_seconds=duration_seconds,
        format=output_format,
        audio_size_bytes=len(audio_bytes),
    )


@tool(args_schema=SearchVoicesInput)
@serialize_pydantic_return
async def search_voices(
    api_key: str,
    search: str | None = None,
    sort: str = "name",
    sort_direction: str = "desc",
) -> SearchVoicesOutput:
    """Search the ElevenLabs voice library."""
    err = _validate_key(api_key, "search_voices")
    if err:
        return SearchVoicesOutput(success=False, error=err)
    try:
        client = _client(api_key)
        response = client.voices.search(
            search=search, sort=sort, sort_direction=sort_direction
        )
        voices = [
            VoiceEntry(
                id=v.voice_id,
                name=v.name,
                category=v.category,
                description=getattr(v, "description", None),
                labels=getattr(v, "labels", {}) or {},
            )
            for v in response.voices
        ]
    except Exception as exc:
        return SearchVoicesOutput(success=False, error=f"Voice search failed: {exc}")
    return SearchVoicesOutput(success=True, voices=voices, count=len(voices))


@tool(args_schema=ListModelsInput)
@serialize_pydantic_return
async def list_models(api_key: str) -> ListModelsOutput:
    """List all available TTS models."""
    err = _validate_key(api_key, "list_models")
    if err:
        return ListModelsOutput(success=False, error=err)
    try:
        client = _client(api_key)
        response = client.models.list()
        models = [
            ModelEntry(
                id=m.model_id,
                name=m.name,
                description=getattr(m, "description", None),
                languages=[
                    {"id": lang.language_id, "name": lang.name}
                    for lang in (m.languages or [])
                ],
            )
            for m in response
        ]
    except Exception as exc:
        return ListModelsOutput(success=False, error=f"Failed to list models: {exc}")
    return ListModelsOutput(success=True, models=models, count=len(models))


@tool(args_schema=GetVoiceInput)
@serialize_pydantic_return
async def get_voice(voice_id: str, api_key: str) -> GetVoiceOutput:
    """Get details for a specific voice."""
    err = _validate_key(api_key, "get_voice")
    if err:
        return GetVoiceOutput(success=False, error=err)
    try:
        client = _client(api_key)
        voice = client.voices.get(voice_id=voice_id)
        settings: dict[str, Any] = {
            "stability": (
                getattr(voice.settings, "stability", None) if voice.settings else None
            ),
            "similarity_boost": (
                getattr(voice.settings, "similarity_boost", None)
                if voice.settings
                else None
            ),
        }
    except Exception as exc:
        return GetVoiceOutput(success=False, error=f"Failed to get voice: {exc}")
    return GetVoiceOutput(
        success=True,
        id=voice.voice_id,
        name=voice.name,
        category=voice.category,
        description=getattr(voice, "description", None),
        labels=getattr(voice, "labels", {}) or {},
        fine_tuning_status=(
            getattr(voice.fine_tuning, "state", None) if voice.fine_tuning else None
        ),
        settings=settings,
    )


@tool(args_schema=VoiceCloneInput)
@serialize_pydantic_return
async def voice_clone(
    name: str,
    audio_files_base64: list[str],
    api_key: str,
    description: str | None = None,
) -> VoiceCloneOutput:
    """Create an instant voice clone from base64-encoded audio samples."""
    err = _validate_key(api_key, "voice_clone")
    if err:
        return VoiceCloneOutput(success=False, error=err)
    if not audio_files_base64:
        return VoiceCloneOutput(
            success=False,
            error="At least one audio file is required for voice cloning.",
        )

    import os
    import tempfile

    temp_files: list[str] = []
    try:
        client = _client(api_key)
        for audio_b64 in audio_files_base64:
            audio_bytes = base64.b64decode(audio_b64)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmp.write(audio_bytes)
            tmp.close()
            temp_files.append(tmp.name)
        voice = client.voices.ivc.create(
            name=name, description=description, files=temp_files
        )
    except Exception as exc:
        for tmp_path in temp_files:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        return VoiceCloneOutput(success=False, error=f"Voice cloning failed: {exc}")
    for tmp_path in temp_files:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
    return VoiceCloneOutput(
        success=True,
        id=voice.voice_id,
        name=voice.name,
        category=voice.category,
        description=getattr(voice, "description", None),
    )


@tool(args_schema=IsolateAudioInput)
@serialize_pydantic_return
async def isolate_audio(
    api_key: str,
    audio_base64: str | None = None,
    audio_url: str | None = None,
) -> IsolateAudioOutput:
    """Isolate voice from background noise / music."""
    err = _validate_key(api_key, "isolate_audio")
    if err:
        return IsolateAudioOutput(success=False, error=err)
    audio_bytes, e = await _resolve_audio(audio_base64, audio_url)
    if audio_bytes is None:
        return IsolateAudioOutput(success=False, error=e)
    try:
        client = _client(api_key)
        isolated_data = client.audio_isolation.convert(audio=audio_bytes)
        isolated_bytes = b"".join(isolated_data)
    except Exception as exc:
        return IsolateAudioOutput(
            success=False, error=f"Audio isolation failed: {exc}"
        )
    return IsolateAudioOutput(
        success=True,
        audio_base64=base64.b64encode(isolated_bytes).decode("utf-8"),
        original_size_bytes=len(audio_bytes),
        isolated_size_bytes=len(isolated_bytes),
    )


@tool(args_schema=CheckSubscriptionInput)
@serialize_pydantic_return
async def check_subscription(api_key: str) -> CheckSubscriptionOutput:
    """Check current subscription tier + usage."""
    err = _validate_key(api_key, "check_subscription")
    if err:
        return CheckSubscriptionOutput(success=False, error=err)
    try:
        client = _client(api_key)
        sub = client.user.subscription.get()
    except Exception as exc:
        return CheckSubscriptionOutput(
            success=False, error=f"Failed to check subscription: {exc}"
        )
    return CheckSubscriptionOutput(
        success=True,
        tier=getattr(sub, "tier", None),
        character_count=getattr(sub, "character_count", None),
        character_limit=getattr(sub, "character_limit", None),
        can_extend_character_limit=getattr(sub, "can_extend_character_limit", None),
        allowed_to_extend_character_limit=getattr(
            sub, "allowed_to_extend_character_limit", None
        ),
        next_character_count_reset_unix=getattr(
            sub, "next_character_count_reset_unix", None
        ),
        voice_limit=getattr(sub, "voice_limit", None),
        professional_voice_limit=getattr(sub, "professional_voice_limit", None),
    )


@tool(args_schema=CreateAgentInput)
@serialize_pydantic_return
async def create_agent(
    name: str,
    first_message: str,
    system_prompt: str,
    api_key: str,
    voice_id: str | None = DEFAULT_VOICE_ID,
    language: str = "en",
    llm: str = "gemini-2.0-flash-001",
    temperature: float = 0.5,
    max_tokens: int | None = None,
    stability: float = 0.5,
    similarity_boost: float = 0.8,
    max_duration_seconds: int = 300,
) -> CreateAgentOutput:
    """Create a conversational AI agent."""
    err = _validate_key(api_key, "create_agent")
    if err:
        return CreateAgentOutput(success=False, error=err)
    conversation_config: dict[str, Any] = {
        "agent": {
            "language": language,
            "prompt": {
                "prompt": system_prompt,
                "llm": llm,
                "tools": [{"type": "system", "name": "end_call", "description": ""}],
                "knowledge_base": [],
                "temperature": temperature,
            },
            "first_message": first_message,
            "dynamic_variables": {"dynamic_variable_placeholders": {}},
        },
        "asr": {
            "quality": "high",
            "provider": "elevenlabs",
            "user_input_audio_format": "pcm_16000",
            "keywords": [],
        },
        "tts": {
            "voice_id": voice_id,
            "model_id": "eleven_turbo_v2",
            "agent_output_audio_format": "pcm_16000",
            "optimize_streaming_latency": 3,
            "stability": stability,
            "similarity_boost": similarity_boost,
        },
        "turn": {"turn_timeout": 7},
        "conversation": {
            "max_duration_seconds": max_duration_seconds,
            "client_events": [
                "audio",
                "interruption",
                "user_transcript",
                "agent_response",
                "agent_response_correction",
            ],
        },
    }
    if max_tokens:
        conversation_config["agent"]["prompt"]["max_tokens"] = max_tokens

    platform_settings: dict[str, Any] = {
        "widget": {
            "variant": "full",
            "avatar": {"type": "orb", "color_1": "#6DB035", "color_2": "#F5CABB"},
            "feedback_mode": "during",
        },
        "call_limits": {"agent_concurrency_limit": -1, "daily_limit": 100000},
        "privacy": {
            "record_voice": True,
            "retention_days": 730,
            "delete_transcript_and_pii": True,
            "delete_audio": True,
        },
    }

    try:
        client = _client(api_key)
        response = client.conversational_ai.agents.create(
            name=name,
            conversation_config=conversation_config,
            platform_settings=platform_settings,
        )
    except Exception as exc:
        return CreateAgentOutput(success=False, error=f"Failed to create agent: {exc}")
    return CreateAgentOutput(
        success=True,
        agent_id=response.agent_id,
        name=name,
        voice_id=voice_id,
        language=language,
        llm=llm,
    )


@tool(args_schema=ListAgentsInput)
@serialize_pydantic_return
async def list_agents(api_key: str) -> ListAgentsOutput:
    """List all conversational AI agents."""
    err = _validate_key(api_key, "list_agents")
    if err:
        return ListAgentsOutput(success=False, error=err)
    try:
        client = _client(api_key)
        response = client.conversational_ai.agents.list()
        agents = (
            [
                {"agent_id": agent.agent_id, "name": agent.name}
                for agent in (response.agents or [])
            ]
            if response.agents
            else []
        )
    except Exception as exc:
        return ListAgentsOutput(success=False, error=f"Failed to list agents: {exc}")
    return ListAgentsOutput(success=True, agents=agents, count=len(agents))


@tool(args_schema=GetAgentInput)
@serialize_pydantic_return
async def get_agent(agent_id: str, api_key: str) -> GetAgentOutput:
    """Get a specific agent's configuration."""
    err = _validate_key(api_key, "get_agent")
    if err:
        return GetAgentOutput(success=False, error=err)
    try:
        client = _client(api_key)
        response = client.conversational_ai.agents.get(agent_id=agent_id)
        voice_id = None
        if response.conversation_config and response.conversation_config.tts:
            voice_id = response.conversation_config.tts.voice_id
        created_at: str | None = None
        if response.metadata and response.metadata.created_at_unix_secs:
            created_at = datetime.fromtimestamp(
                response.metadata.created_at_unix_secs
            ).isoformat()
    except Exception as exc:
        return GetAgentOutput(success=False, error=f"Failed to get agent: {exc}")
    return GetAgentOutput(
        success=True,
        agent_id=response.agent_id,
        name=response.name,
        voice_id=voice_id,
        created_at=created_at,
    )


@tool(args_schema=AddKnowledgeBaseInput)
@serialize_pydantic_return
async def add_knowledge_base_to_agent(
    agent_id: str,
    knowledge_base_name: str,
    api_key: str,
    url: str | None = None,
    text: str | None = None,
    file_base64: str | None = None,
) -> AddKnowledgeBaseOutput:
    """Attach a KB document (url/text/file) to an agent."""
    err = _validate_key(api_key, "add_knowledge_base_to_agent")
    if err:
        return AddKnowledgeBaseOutput(success=False, error=err)

    sources = [s for s in (url, text, file_base64) if s is not None]
    if len(sources) == 0:
        return AddKnowledgeBaseOutput(
            success=False, error="Must provide one of: url, text, or file_base64"
        )
    if len(sources) > 1:
        return AddKnowledgeBaseOutput(
            success=False,
            error="Must provide exactly one of: url, text, or file_base64",
        )

    try:
        client = _client(api_key)
        if url:
            response = client.conversational_ai.knowledge_base.documents.create_from_url(
                name=knowledge_base_name, url=url
            )
        else:
            if text:
                file_io: Any = io.BytesIO(text.encode("utf-8"))
                file_io.name = "text.txt"
            else:
                assert file_base64 is not None
                file_io = io.BytesIO(base64.b64decode(file_base64))
                file_io.name = "document.pdf"
            response = client.conversational_ai.knowledge_base.documents.create_from_file(
                name=knowledge_base_name, file=file_io
            )

        agent = client.conversational_ai.agents.get(agent_id=agent_id)
        agent_config = agent.conversation_config.agent
        existing_kb: list[Any] = []
        if agent_config:
            prompt_config = getattr(agent_config, "prompt", None)
            if prompt_config:
                existing_kb = list(getattr(prompt_config, "knowledge_base", []) or [])

        kb_locator = {
            "type": "file" if not url else "url",
            "name": knowledge_base_name,
            "id": response.id,
        }
        client.conversational_ai.agents.update(
            agent_id=agent_id,
            conversation_config={
                "agent": {"prompt": {"knowledge_base": [*existing_kb, kb_locator]}}
            },
        )
    except Exception as exc:
        return AddKnowledgeBaseOutput(
            success=False, error=f"Failed to add knowledge base: {exc}"
        )
    return AddKnowledgeBaseOutput(
        success=True,
        knowledge_base_id=response.id,
        name=knowledge_base_name,
        agent_id=agent_id,
        source_type=("url" if url else ("text" if text else "file")),
    )


@tool(args_schema=ListConversationsInput)
@serialize_pydantic_return
async def list_conversations(
    api_key: str,
    agent_id: str | None = None,
    page_size: int = 30,
) -> ListConversationsOutput:
    """List recorded conversations."""
    err = _validate_key(api_key, "list_conversations")
    if err:
        return ListConversationsOutput(success=False, error=err)
    page_size = min(max(page_size, 1), 100)
    try:
        client = _client(api_key)
        response = client.conversational_ai.conversations.list(
            agent_id=agent_id, page_size=page_size
        )
        conversations: list[dict[str, Any]] = []
        for conv in (response.conversations or []):
            start_time = (
                datetime.fromtimestamp(conv.start_time_unix_secs).isoformat()
                if conv.start_time_unix_secs
                else None
            )
            conversations.append(
                {
                    "conversation_id": conv.conversation_id,
                    "agent_id": conv.agent_id,
                    "status": conv.status,
                    "start_time": start_time,
                }
            )
    except Exception as exc:
        return ListConversationsOutput(
            success=False, error=f"Failed to list conversations: {exc}"
        )
    return ListConversationsOutput(
        success=True, conversations=conversations, count=len(conversations)
    )


@tool(args_schema=GetConversationInput)
@serialize_pydantic_return
async def get_conversation(
    conversation_id: str, api_key: str
) -> GetConversationOutput:
    """Get a conversation's full transcript."""
    err = _validate_key(api_key, "get_conversation")
    if err:
        return GetConversationOutput(success=False, error=err)
    try:
        client = _client(api_key)
        response = client.conversational_ai.conversations.get(conversation_id)
        transcript_lines = []
        for entry in response.transcript:
            role = getattr(entry, "role", "unknown").upper()
            message = getattr(entry, "message", "")
            transcript_lines.append(f"{role}: {message}")
        transcript = "\n\n".join(transcript_lines)
        duration = (
            getattr(response.metadata, "call_duration_secs", None)
            if response.metadata
            else None
        )
        analysis = (
            getattr(response.analysis, "summary", None)
            if response.analysis
            else None
        )
    except Exception as exc:
        return GetConversationOutput(
            success=False, error=f"Failed to get conversation: {exc}"
        )
    return GetConversationOutput(
        success=True,
        conversation_id=response.conversation_id,
        agent_id=response.agent_id,
        status=response.status,
        transcript=transcript,
        message_count=len(response.transcript),
        duration_seconds=duration,
        analysis_summary=analysis,
    )
