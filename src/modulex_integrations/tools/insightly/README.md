# Insightly

CRM and project management platform for managing contacts, tasks, and sales pipelines via the Insightly REST API (`api.{pod}.insightly.com/v3.1`).

## Authentication

### Insightly API Key

- Log in to your Insightly account and navigate to **User Settings > API** to find your API key.
- Required env vars:
  - `INSIGHTLY_POD` — your Insightly pod/region identifier (e.g. `na1`, `au1`) found in your Insightly URL.
  - `INSIGHTLY_API_KEY` — your Insightly API key (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).
- Authentication uses HTTP Basic Auth with the API key as the username and an empty password.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_contact` | Creates a new contact in Insightly | `first_name`, `last_name`, `email` |
| `create_task` | Creates a new task in Insightly | `title`, `status`, `due_date` |

Every tool takes additional `pod` and `api_key` parameters that the runtime fills in from the resolved credential.

## Limits & Quotas

- **Rate limits**: Insightly enforces per-plan rate limits (typically 10 requests/second for Professional plans, higher for Enterprise).
- **Pricing**: API access requires a paid Insightly plan (Professional or higher).
- **Error model**: non-2xx responses are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
