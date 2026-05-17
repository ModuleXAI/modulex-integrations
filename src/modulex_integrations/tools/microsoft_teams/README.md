# Microsoft Teams

Create channels, send channel and chat messages, list teams / channels / chats / messages / shifts, search messages, and retrieve the current user via the Microsoft Graph REST API (`graph.microsoft.com/v1.0`).

## Authentication

This integration uses Microsoft Entra (formerly Azure AD) OAuth 2.0 against Microsoft Graph. Personal Microsoft accounts are not supported by the Microsoft Teams APIs — the signed-in account must be a Microsoft 365 work or school account in a Microsoft Entra tenant.

### OAuth2 Authentication

- Register an app at the [Microsoft Entra admin center](https://entra.microsoft.com) under **App registrations**.
- Under **Authentication**, add the redirect URI `https://api.modulex.dev/credentials/oauth2/callback` (type: Web).
- Under **API permissions**, add the Microsoft Graph **delegated** permissions listed below and grant admin consent if your tenant requires it.
- Under **Certificates & secrets**, create a Client Secret and copy its **Value** (not the Secret ID).
- Required env vars:
  - `MICROSOFT_TEAMS_OAUTH2_CLIENT_ID` (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) — Microsoft Entra Application (client) ID.
  - `MICROSOFT_TEAMS_OAUTH2_CLIENT_SECRET` — Microsoft Entra Client Secret **Value**.
- Authorize endpoint: `https://login.microsoftonline.com/common/oauth2/v2.0/authorize`
- Token endpoint: `https://login.microsoftonline.com/common/oauth2/v2.0/token`
- Scopes requested: `offline_access User.Read Team.ReadBasic.All Channel.ReadBasic.All ChannelMessage.Read.All ChannelMessage.Send Chat.ReadWrite ChatMessage.Send Schedule.Read.All Mail.Read`

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_channel` | Create a new channel in Microsoft Teams. | `team_id`, `display_name` |
| `get_chat_message` | Get a specific message from a chat. | `chat_id`, `message_id` |
| `get_current_user` | Returns the authenticated user's ID, display name, email, and principal name. | _none_ |
| `list_channel_messages` | Lists messages in a Microsoft Teams channel. | `team_id`, `channel_id` |
| `list_channels` | Lists all channels in a Microsoft Team. | `team_id` |
| `list_chats` | Lists all chat conversations for the authenticated user. | _none_ |
| `list_messages_in_chat` | Get the list of messages in a chat (ordered by `createdDateTime` descending). | `chat_id` |
| `list_shifts` | Get the list of shift instances for a team. | `team_id` |
| `list_teams` | Lists all teams the authenticated user has joined. | _none_ |
| `search_messages` | Search for email (`entity_type=message`) or Teams chat (`entity_type=chatMessage`) messages. | `entity_type`, `query_string` |
| `send_channel_message` | Send a message to a team's channel. Optionally include inline images via `hosted_contents`. | `team_id`, `channel_id`, `message` |
| `send_chat_message` | Send a message to a team's chat. | `chat_id`, `message` |

Every tool takes an additional `auth_type` / `auth_data` pair that the runtime fills in from the resolved OAuth2 credential.

## Limits & Quotas

- Microsoft Graph applies per-app, per-tenant, and per-resource throttling. Teams messaging endpoints have specific RU-based limits documented at <https://learn.microsoft.com/en-us/graph/throttling>. Retry on HTTP 429 honoring the `Retry-After` header.
- `search_messages` returns at most 25 results per call (upper bound enforced by the Microsoft Graph search API for this entity-type set). Use the `from_` parameter to page beyond the first window.
- Dynamic team / channel / chat / message pickers are not available — pass IDs directly; use the corresponding `list_*` action to enumerate IDs.
- Webhook / change-notification subscriptions are not part of this integration; polling via the `list_*` actions is the supported pattern.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` plus an `error` string rather than raising. Plan for retries on the agent side based on the error text.

## Maintainer

ModuleX core team.
