# Browserbase

Cloud browser infrastructure for running and managing headless browser sessions
via the Browserbase REST API (`api.browserbase.com/v1`).

## Authentication

### API Key Authentication

- Sign in at <https://www.browserbase.com> and navigate to Settings > API Keys.
- Create a new API key or copy your existing one.
- Required env var: `BROWSERBASE_API_KEY` (format: `bb_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_context` | Creates a new context in Browserbase for persistent browser state | `project_id` |
| `create_session` | Creates a new browser session with specified settings | `project_id` |
| `list_projects` | Lists all projects in the Browserbase account | _(none)_ |

Every tool takes an additional `api_key` parameter that the runtime fills in
from the resolved credential.

## Limits & Quotas

- Rate limits are not publicly documented by Browserbase; contact their support for enterprise limits.
- Session timeout range: 60–21600 seconds.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
