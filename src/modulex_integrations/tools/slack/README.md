# Slack

Channels, messages, threads, reactions, and user management against
the Slack Web API (`slack.com/api`).

## Authentication

Two methods supported — both validate against `auth.test`.

### OAuth2 (recommended)

- Create a Slack App at <https://api.slack.com/apps>.
- Required env vars (only for custom OAuth Apps):
  - `SLACK_OAUTH2_CLIENT_ID`
  - `SLACK_OAUTH2_CLIENT_SECRET`
- Scopes:
  `channels:read`, `channels:history`, `chat:write`, `reactions:write`,
  `users:read`, `users.profile:read`.
- Auth URL: `https://slack.com/oauth/v2/authorize`
- Token URL: `https://slack.com/api/oauth.v2.access`

### Bot Token (xoxb-…)

- From your Slack App's *OAuth & Permissions* page, copy the **Bot
  User OAuth Token**.
- Required env var: `SLACK_BOT_TOKEN` (format: `xoxb-…`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_channels` | List public channels with pagination | — |
| `post_message` | Post a new message to a channel | `channel_id`, `text` |
| `reply_to_thread` | Reply to a thread | `channel_id`, `thread_ts`, `text` |
| `add_reaction` | Add an emoji reaction | `channel_id`, `timestamp`, `reaction` |
| `get_channel_history` | Get recent messages from a channel | `channel_id` |
| `get_thread_replies` | Get replies in a thread | `channel_id`, `thread_ts` |
| `get_users` | List workspace users | — |
| `get_user_profile` | Get a user's detailed profile | `user_id` |

All tools take an additional `auth_type` and `auth_data` parameter
pair the runtime fills in.

## Limits & Quotas

- **Tier 1** (most read endpoints): ~60 req/min.
- **Tier 2** (`chat.postMessage`, `reactions.add`): ~20 req/min.
- **Tier 3** (`conversations.history`, `users.list`): ~100 req/min.
- Slack reports errors as HTTP 200 with `ok: false` and an `error`
  field — the tools surface this in the output as `success: False` +
  `error`, *not* an exception. Plan for retry/back-off based on the
  string error code (e.g. `ratelimited`, `channel_not_found`).

## Maintainer

ModuleX core team.
