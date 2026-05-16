# ElevenLabs

AI voice integration via the **synchronous** `elevenlabs` SDK. 15
actions across TTS, STT, sound effects, voice library / cloning /
isolation, subscription, and Conversational-AI agents.

## Authentication

- **Paired `api_key + modulex_key` schemas** (both Bearer-authed —
  the runtime picks which credential to inject; tool code is
  auth-agnostic).
- `api_key` env: `ELEVENLABS_API_KEY` (sensitive).
- `modulex_key` env: none (managed by ModuleX).
- Both `test_endpoint`s hit `GET /v1/user/subscription` and assert
  the `tier` field.

## Runtime convention

Key-based: every `@tool` accepts `(api_key, ...)`.

## Tools

| group | tools |
| --- | --- |
| TTS | `text_to_speech`, `text_to_sound_effects` |
| STT | `speech_to_text` |
| Voices | `search_voices`, `get_voice`, `voice_clone` |
| Audio | `isolate_audio` |
| Models | `list_models` |
| Account | `check_subscription` |
| Agents | `create_agent`, `list_agents`, `get_agent`, `add_knowledge_base_to_agent` |
| Conversations | `list_conversations`, `get_conversation` |

## Notes

- **Sync SDK in async tools** — preserved verbatim from legacy.
  Calls into `elevenlabs` block the event loop.
- Audio actions return **base64-encoded MP3** by default (output
  format configurable on the TTS/sound-effects tools).
- `speech_to_text` + `isolate_audio` accept either base64 or URL
  via the shared `_resolve_audio` helper. The URL path uses an
  internal async httpx fetch.
- `add_knowledge_base_to_agent` chains 3 SDK calls: create KB
  document → get agent → update agent's `knowledge_base` list.
  XOR-validates `url` / `text` / `file_base64`.
- `voice_clone` writes audio samples to temp files (the SDK
  requires file paths, not bytes) and cleans them up in a
  `finally`-style branch.
- `elevenlabs` is lazy-imported inside `_client()` so manifest
  inspection works without the SDK installed.

## Maintainer

ModuleX core team.
