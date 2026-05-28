# PostGrid

Programmatic direct mail delivery via the PostGrid Print & Mail API (`api.postgrid.com/print-mail/v1`).

## Authentication

### API Key Authentication

- Sign in at [app.postgrid.com](https://app.postgrid.com), navigate to Settings > API Keys.
- Copy your live or test API key.
- Required env var: `POSTGRID_API_KEY` (format: `live_sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_contact` | Create a new contact in PostGrid | `first_name`, `address_line1` |
| `create_letter` | Create a new letter in PostGrid | `to`, `from_contact`, `html` |
| `create_postcard` | Create a new postcard in PostGrid | `to`, `from_contact`, `front_html`, `back_html`, `size` |

Every tool takes an additional `api_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- No publicly documented rate limits. PostGrid applies per-account request limits based on plan tier.
- Sending physical mail incurs per-item costs based on the PostGrid pricing plan.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
