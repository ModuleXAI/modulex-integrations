"""Pydantic response models for the ElevenLabs integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddKnowledgeBaseOutput",
    "CheckSubscriptionOutput",
    "CreateAgentOutput",
    "GetAgentOutput",
    "GetConversationOutput",
    "GetVoiceOutput",
    "IsolateAudioOutput",
    "ListAgentsOutput",
    "ListConversationsOutput",
    "ListModelsOutput",
    "ModelEntry",
    "SearchVoicesOutput",
    "SpeechToTextOutput",
    "TextToSoundEffectsOutput",
    "TextToSpeechOutput",
    "VoiceCloneOutput",
    "VoiceEntry",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class TextToSpeechOutput(_Base):
    audio_base64: str | None = None
    voice: dict[str, Any] | None = None
    model_id: str | None = None
    format: str | None = None
    text_length: int = 0
    audio_size_bytes: int = 0


class SpeechToTextOutput(_Base):
    transcript: str | None = None
    diarized: bool = False
    language_detected: str | None = None


class TextToSoundEffectsOutput(_Base):
    audio_base64: str | None = None
    description: str | None = None
    duration_seconds: float | None = None
    format: str | None = None
    audio_size_bytes: int = 0


class VoiceEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str | None = None
    name: str | None = None
    category: str | None = None
    description: str | None = None
    labels: dict[str, Any] = Field(default_factory=dict)


class SearchVoicesOutput(_Base):
    voices: list[VoiceEntry] = Field(default_factory=list)
    count: int = 0


class ModelEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())
    id: str | None = None
    name: str | None = None
    description: str | None = None
    languages: list[dict[str, Any]] = Field(default_factory=list)


class ListModelsOutput(_Base):
    models: list[ModelEntry] = Field(default_factory=list)
    count: int = 0


class GetVoiceOutput(_Base):
    id: str | None = None
    name: str | None = None
    category: str | None = None
    description: str | None = None
    labels: dict[str, Any] = Field(default_factory=dict)
    fine_tuning_status: str | None = None
    settings: dict[str, Any] | None = None


class VoiceCloneOutput(_Base):
    id: str | None = None
    name: str | None = None
    category: str | None = None
    description: str | None = None


class IsolateAudioOutput(_Base):
    audio_base64: str | None = None
    original_size_bytes: int = 0
    isolated_size_bytes: int = 0


class CheckSubscriptionOutput(_Base):
    tier: str | None = None
    character_count: int | None = None
    character_limit: int | None = None
    can_extend_character_limit: bool | None = None
    allowed_to_extend_character_limit: bool | None = None
    next_character_count_reset_unix: int | None = None
    voice_limit: int | None = None
    professional_voice_limit: int | None = None


class CreateAgentOutput(_Base):
    agent_id: str | None = None
    name: str | None = None
    voice_id: str | None = None
    language: str | None = None
    llm: str | None = None


class ListAgentsOutput(_Base):
    agents: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class GetAgentOutput(_Base):
    agent_id: str | None = None
    name: str | None = None
    voice_id: str | None = None
    created_at: str | None = None


class AddKnowledgeBaseOutput(_Base):
    knowledge_base_id: str | None = None
    name: str | None = None
    agent_id: str | None = None
    source_type: str | None = None


class ListConversationsOutput(_Base):
    conversations: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class GetConversationOutput(_Base):
    conversation_id: str | None = None
    agent_id: str | None = None
    status: str | None = None
    transcript: str | None = None
    message_count: int = 0
    duration_seconds: int | None = None
    analysis_summary: str | None = None
