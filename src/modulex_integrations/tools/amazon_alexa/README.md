# Amazon Alexa

Simulate and test Alexa skills via the Alexa Skills Management API (`api.amazonalexa.com/v2`).

## Authentication

### OAuth2 Authentication

- Register an OAuth app at the [Amazon Developer Console](https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html).
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Scopes requested: `alexa::ask:skills:readwrite`, `alexa::ask:skills:test`
- Required env vars (only when bringing your own OAuth app):
  - `AMAZON_ALEXA_OAUTH2_CLIENT_ID` (format: `amzn1.application-oa2-client.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
  - `AMAZON_ALEXA_OAUTH2_CLIENT_SECRET`

## Tools

| name | description | required params |
| --- | --- | --- |
| `simulate_skill` | Simulate a dialog from an Alexa-enabled device and receive the skill response for the specified utterance. | `skill_id`, `stage`, `content` |
| `get_simulation_results` | Get the results of a specified simulation for an Alexa skill. | `skill_id`, `stage`, `simulation_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- The Alexa SMAPI is rate-limited per developer account; exact limits are not publicly documented but throttling may occur at high request volumes.
- Simulation requests are asynchronous: `simulate_skill` returns a simulation ID immediately; poll with `get_simulation_results` to retrieve outcomes.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
