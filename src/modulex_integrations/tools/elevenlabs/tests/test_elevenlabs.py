"""Tests for the ElevenLabs integration."""
from __future__ import annotations

import base64
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from modulex_integrations.tools.elevenlabs import (
    TOOLS,
    add_knowledge_base_to_agent,
    check_subscription,
    create_agent,
    get_agent,
    get_conversation,
    get_voice,
    isolate_audio,
    list_agents,
    list_conversations,
    list_models,
    manifest,
    search_voices,
    speech_to_text,
    text_to_sound_effects,
    text_to_speech,
    voice_clone,
)
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
    SearchVoicesOutput,
    SpeechToTextOutput,
    TextToSoundEffectsOutput,
    TextToSpeechOutput,
    VoiceCloneOutput,
)

_API_KEY = "sk_test"


def _patch_client(client: MagicMock) -> Any:
    return patch(
        "modulex_integrations.tools.elevenlabs.tools._client",
        return_value=client,
    )


class TestManifest:
    def test_manifest_exposes_15_actions(self) -> None:
        assert len(manifest.actions) == 15

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_paired_auth(self) -> None:
        types = {a.auth_type for a in manifest.auth_schemas}
        assert types == {"api_key", "modulex_key"}


@pytest.mark.asyncio
async def test_text_to_speech_missing_key() -> None:
    result = TextToSpeechOutput.model_validate(
        await text_to_speech.ainvoke({"text": "hi", "api_key": ""})
    )
    assert result.success is False
    assert result.error is not None and "empty" in result.error


@pytest.mark.asyncio
async def test_text_to_speech_voice_xor() -> None:
    result = TextToSpeechOutput.model_validate(
        await text_to_speech.ainvoke(
            {
                "text": "hi",
                "api_key": _API_KEY,
                "voice_id": "v1",
                "voice_name": "Bob",
            }
        )
    )
    assert result.success is False
    assert result.error is not None and "voice_id" in result.error


@pytest.mark.asyncio
async def test_text_to_speech() -> None:
    client = MagicMock()
    # iter of bytes chunks
    client.text_to_speech.convert.return_value = iter([b"abc", b"def"])
    with _patch_client(client):
        result = TextToSpeechOutput.model_validate(
            await text_to_speech.ainvoke(
                {"text": "Hello", "api_key": _API_KEY, "voice_id": "v1"}
            )
        )
    assert result.success is True
    assert base64.b64decode(result.audio_base64 or "") == b"abcdef"
    assert result.text_length == 5


@pytest.mark.asyncio
async def test_speech_to_text_validates_xor() -> None:
    result = SpeechToTextOutput.model_validate(
        await speech_to_text.ainvoke({"api_key": _API_KEY})
    )
    assert result.success is False
    assert result.error is not None and "audio_base64" in result.error


@pytest.mark.asyncio
async def test_speech_to_text_with_base64() -> None:
    transcription = MagicMock()
    transcription.text = "hello world"
    transcription.language_code = "en"
    client = MagicMock()
    client.speech_to_text.convert.return_value = transcription
    with _patch_client(client):
        result = SpeechToTextOutput.model_validate(
            await speech_to_text.ainvoke(
                {
                    "api_key": _API_KEY,
                    "audio_base64": base64.b64encode(b"audio").decode(),
                }
            )
        )
    assert result.success is True
    assert result.transcript == "hello world"


@pytest.mark.asyncio
async def test_text_to_sound_effects_duration_validation() -> None:
    result = TextToSoundEffectsOutput.model_validate(
        await text_to_sound_effects.ainvoke(
            {"text": "boom", "api_key": _API_KEY, "duration_seconds": 10}
        )
    )
    assert result.success is False
    assert result.error is not None and "0.5 and 5" in result.error


@pytest.mark.asyncio
async def test_text_to_sound_effects() -> None:
    client = MagicMock()
    client.text_to_sound_effects.convert.return_value = iter([b"sfx"])
    with _patch_client(client):
        result = TextToSoundEffectsOutput.model_validate(
            await text_to_sound_effects.ainvoke(
                {"text": "thunder", "api_key": _API_KEY, "duration_seconds": 2.0}
            )
        )
    assert result.success is True


@pytest.mark.asyncio
async def test_search_voices() -> None:
    voice = MagicMock()
    voice.voice_id = "v1"
    voice.name = "Alice"
    voice.category = "premade"
    voice.description = None
    voice.labels = {}
    response = MagicMock()
    response.voices = [voice]
    client = MagicMock()
    client.voices.search.return_value = response
    with _patch_client(client):
        result = SearchVoicesOutput.model_validate(
            await search_voices.ainvoke({"api_key": _API_KEY})
        )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_list_models() -> None:
    model = MagicMock()
    model.model_id = "m1"
    model.name = "Test"
    model.description = None
    lang = MagicMock()
    lang.language_id = "en"
    lang.name = "English"
    model.languages = [lang]
    client = MagicMock()
    client.models.list.return_value = [model]
    with _patch_client(client):
        result = ListModelsOutput.model_validate(
            await list_models.ainvoke({"api_key": _API_KEY})
        )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_get_voice() -> None:
    voice = MagicMock()
    voice.voice_id = "v1"
    voice.name = "Voice"
    voice.category = "cloned"
    voice.description = "Test"
    voice.labels = {}
    voice.fine_tuning = MagicMock()
    voice.fine_tuning.state = "ready"
    voice.settings = MagicMock()
    voice.settings.stability = 0.5
    voice.settings.similarity_boost = 0.75
    client = MagicMock()
    client.voices.get.return_value = voice
    with _patch_client(client):
        result = GetVoiceOutput.model_validate(
            await get_voice.ainvoke({"voice_id": "v1", "api_key": _API_KEY})
        )
    assert result.success is True
    assert result.fine_tuning_status == "ready"


@pytest.mark.asyncio
async def test_voice_clone_requires_audio() -> None:
    result = VoiceCloneOutput.model_validate(
        await voice_clone.ainvoke(
            {"name": "X", "audio_files_base64": [], "api_key": _API_KEY}
        )
    )
    assert result.success is False
    assert result.error is not None and "audio file" in result.error


@pytest.mark.asyncio
async def test_voice_clone() -> None:
    voice = MagicMock()
    voice.voice_id = "v1"
    voice.name = "Cloned"
    voice.category = "cloned"
    voice.description = None
    client = MagicMock()
    client.voices.ivc.create.return_value = voice
    with _patch_client(client):
        result = VoiceCloneOutput.model_validate(
            await voice_clone.ainvoke(
                {
                    "name": "Cloned",
                    "audio_files_base64": [base64.b64encode(b"audio").decode()],
                    "api_key": _API_KEY,
                }
            )
        )
    assert result.success is True
    assert result.id == "v1"


@pytest.mark.asyncio
async def test_isolate_audio() -> None:
    client = MagicMock()
    client.audio_isolation.convert.return_value = iter([b"clean"])
    with _patch_client(client):
        result = IsolateAudioOutput.model_validate(
            await isolate_audio.ainvoke(
                {
                    "api_key": _API_KEY,
                    "audio_base64": base64.b64encode(b"raw").decode(),
                }
            )
        )
    assert result.success is True
    assert result.original_size_bytes == 3
    assert result.isolated_size_bytes == 5


@pytest.mark.asyncio
async def test_check_subscription() -> None:
    sub = MagicMock()
    sub.tier = "creator"
    sub.character_count = 1000
    sub.character_limit = 30000
    client = MagicMock()
    client.user.subscription.get.return_value = sub
    with _patch_client(client):
        result = CheckSubscriptionOutput.model_validate(
            await check_subscription.ainvoke({"api_key": _API_KEY})
        )
    assert result.success is True
    assert result.tier == "creator"


@pytest.mark.asyncio
async def test_create_agent() -> None:
    response = MagicMock()
    response.agent_id = "a1"
    client = MagicMock()
    client.conversational_ai.agents.create.return_value = response
    with _patch_client(client):
        result = CreateAgentOutput.model_validate(
            await create_agent.ainvoke(
                {
                    "name": "Bot",
                    "first_message": "Hi",
                    "system_prompt": "Be helpful",
                    "api_key": _API_KEY,
                }
            )
        )
    assert result.success is True
    assert result.agent_id == "a1"


@pytest.mark.asyncio
async def test_list_agents() -> None:
    agent = MagicMock()
    agent.agent_id = "a1"
    agent.name = "Bot"
    response = MagicMock()
    response.agents = [agent]
    client = MagicMock()
    client.conversational_ai.agents.list.return_value = response
    with _patch_client(client):
        result = ListAgentsOutput.model_validate(
            await list_agents.ainvoke({"api_key": _API_KEY})
        )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_get_agent() -> None:
    response = MagicMock()
    response.agent_id = "a1"
    response.name = "Bot"
    response.conversation_config = MagicMock()
    response.conversation_config.tts = MagicMock()
    response.conversation_config.tts.voice_id = "v1"
    response.metadata = MagicMock()
    response.metadata.created_at_unix_secs = 0
    client = MagicMock()
    client.conversational_ai.agents.get.return_value = response
    with _patch_client(client):
        result = GetAgentOutput.model_validate(
            await get_agent.ainvoke({"agent_id": "a1", "api_key": _API_KEY})
        )
    assert result.success is True
    assert result.voice_id == "v1"


@pytest.mark.asyncio
async def test_add_knowledge_base_validates_xor() -> None:
    result = AddKnowledgeBaseOutput.model_validate(
        await add_knowledge_base_to_agent.ainvoke(
            {"agent_id": "a1", "knowledge_base_name": "KB", "api_key": _API_KEY}
        )
    )
    assert result.success is False
    assert result.error is not None and "url, text" in result.error


@pytest.mark.asyncio
async def test_add_knowledge_base_with_url() -> None:
    kb_response = MagicMock()
    kb_response.id = "kb1"
    agent = MagicMock()
    agent.conversation_config = MagicMock()
    agent.conversation_config.agent = MagicMock()
    agent.conversation_config.agent.prompt = MagicMock()
    agent.conversation_config.agent.prompt.knowledge_base = []
    client = MagicMock()
    client.conversational_ai.knowledge_base.documents.create_from_url.return_value = (
        kb_response
    )
    client.conversational_ai.agents.get.return_value = agent
    with _patch_client(client):
        result = AddKnowledgeBaseOutput.model_validate(
            await add_knowledge_base_to_agent.ainvoke(
                {
                    "agent_id": "a1",
                    "knowledge_base_name": "Docs",
                    "api_key": _API_KEY,
                    "url": "https://example.com",
                }
            )
        )
    assert result.success is True
    assert result.knowledge_base_id == "kb1"
    assert result.source_type == "url"


@pytest.mark.asyncio
async def test_list_conversations() -> None:
    conv = MagicMock()
    conv.conversation_id = "c1"
    conv.agent_id = "a1"
    conv.status = "done"
    conv.start_time_unix_secs = 0
    response = MagicMock()
    response.conversations = [conv]
    client = MagicMock()
    client.conversational_ai.conversations.list.return_value = response
    with _patch_client(client):
        result = ListConversationsOutput.model_validate(
            await list_conversations.ainvoke({"api_key": _API_KEY})
        )
    assert result.success is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_get_conversation() -> None:
    entry = MagicMock()
    entry.role = "user"
    entry.message = "hi"
    response = MagicMock()
    response.conversation_id = "c1"
    response.agent_id = "a1"
    response.status = "done"
    response.transcript = [entry]
    response.metadata = MagicMock()
    response.metadata.call_duration_secs = 30
    response.analysis = MagicMock()
    response.analysis.summary = "Good chat"
    client = MagicMock()
    client.conversational_ai.conversations.get.return_value = response
    with _patch_client(client):
        result = GetConversationOutput.model_validate(
            await get_conversation.ainvoke(
                {"conversation_id": "c1", "api_key": _API_KEY}
            )
        )
    assert result.success is True
    assert "USER: hi" in (result.transcript or "")
    assert result.duration_seconds == 30
