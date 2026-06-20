# Mercury

Business banking platform for startups and scaling companies. Integrates with
the Mercury REST API (`backend.mercury.com/api/v1`).

## Authentication

### API Token

- Log in to your Mercury dashboard at <https://app.mercury.com>.
- Navigate to **Settings -> API Tokens** and generate a new token.
- Required env var: `MERCURY_API_TOKEN` (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_account_info` | Retrieve information about a specific Mercury bank account | `account_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved credential.

## Limits & Quotas

- No publicly documented rate limits for the Mercury API.
- Access is limited to accounts with API access enabled by Mercury support.
- Error model: non-2xx responses and timeouts are caught and returned as
  `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
