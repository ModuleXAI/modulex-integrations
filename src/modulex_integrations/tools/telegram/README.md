# Telegram Bot

Telegram Bot API integration via direct HTTP against
`api.telegram.org/bot<token>/<method>`. Covers messaging,
chat/member management, and a long-poll updates feed.

## Authentication

### Bot Token (in URL path)

- Required env var: `TELEGRAM_BOT_TOKEN`.
- Obtain a token by talking to `@BotFather` on Telegram.
- **Unique among integrations**: the credential is embedded
  **inside the URL path** (`/bot{token}/...`), not in a header or
  query string. The `test_endpoint.url` carries the
  `{api_key}` placeholder which the modulex runtime substitutes
  (both single- and double-brace forms are accepted).

## Tools

17 actions across messaging + chat management:

- **Messaging**: `send_text_message`, `send_photo`, `send_document`,
  `send_video`, `send_audio`, `forward_message`,
  `edit_text_message`, `delete_message`, `pin_message`,
  `create_chat_invite_link`.
- **Inspection**: `get_chat`, `get_chat_member_count`,
  `get_chat_administrators`, `get_updates`, `get_me`.
- **Moderation**: `ban_chat_member`, `unban_chat_member`.

## Limits & Quotas

- Media (`send_photo` / `send_document` / `send_video` /
  `send_audio`) accepts a **file_id or HTTPS URL** only — local
  file uploads via multipart aren't supported here (the legacy
  implementation didn't actually upload bytes either, despite the
  docstring claim — we preserve the simpler behavior).
- Failures (Telegram `ok: false`, HTTP errors, exceptions) all
  surface as `success=False` + `error` carrying the upstream
  `description` field where available.
- `delete_message` only works for messages younger than 48 hours
  (Telegram constraint).

## Maintainer

ModuleX core team.
