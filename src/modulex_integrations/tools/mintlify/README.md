# Mintlify

Documentation platform with AI-powered assistant chat, semantic search, and project update triggers against the Mintlify REST APIs (`api-dsc.mintlify.com/v1` and `api.mintlify.com/v1`).

## Authentication

### Mintlify API Keys

This integration uses three credential fields:

- **Assistant API Key** (`MINTLIFY_ASSISTANT_API_KEY`): Used for chat and search endpoints. Obtain from your [Mintlify dashboard](https://dashboard.mintlify.com).
- **Admin API Key** (`MINTLIFY_ADMIN_API_KEY`): Used for triggering project updates. Obtain from your [Mintlify dashboard](https://dashboard.mintlify.com).
- **Project ID** (`MINTLIFY_PROJECT_ID`): Your project identifier used for update triggers. Found in the [Mintlify dashboard](https://dashboard.mintlify.com).

## Tools

| name | description | required params |
| --- | --- | --- |
| `chat_with_assistant` | Generates a response message from the assistant for the specified domain. | `domain`, `fp`, `message` |
| `search_documentation` | Perform semantic and keyword searches across your documentation. | `domain`, `query` |
| `trigger_update` | Trigger an update for a project. | (none) |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential.

## Limits & Quotas

- No publicly documented rate limits for the Mintlify API.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
