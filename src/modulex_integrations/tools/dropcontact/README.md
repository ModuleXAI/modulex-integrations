# Dropcontact

GDPR-compliant B2B contact enrichment against the Dropcontact REST API
(`api.dropcontact.com`). Submit a partial contact and receive a
verified professional email, phone number, company firmographics, and
LinkedIn profile.

## Authentication

One method supported: an API key sent as the `X-Access-Token` request
header.

### API Key

- Sign in to your Dropcontact account at <https://app.dropcontact.com>,
  open the **API & Integrations** settings, and copy your personal API
  key.
- Required env var: `DROPCONTACT_API_KEY`.

The runtime injects the key into each tool as an `api_key` parameter
and sends it as the `X-Access-Token` header — note this is **not** the
`auth_type`/`auth_data` pair used by OAuth/bearer integrations.

## Tools

| name | description | required params |
| --- | --- | --- |
| `enrich_contact` | Enrich and verify a B2B contact (email, phone, company, LinkedIn). Async submit-then-poll, up to 2 minutes. | none individually; supply at least one of `email`, `first_name`+`last_name`+`company`, `full_name`+`company`, or `linkedin` |

`enrich_contact` accepts `email`, `first_name`, `last_name`,
`full_name`, `company`, `website`, `num_siren`, `phone`, `linkedin`,
`country`, `siren` (boolean, France-only firmographics), and
`language`. Every tool takes an additional `api_key` parameter the
runtime fills from the resolved credential.

## Limits & Quotas

- **Rate limit**: ~60 requests/second per the vendor docs.
- **Async enrichment**: requests are processed asynchronously; the tool
  polls every 5 seconds for up to 2 minutes before giving up.
- **Pay on success**: a credit is consumed only when a verified email
  is returned — no charge when no email is found.
- **Error model**: non-2xx responses, an API error flag, timeouts, and
  an expired polling window are caught and returned as `success=False`
  + `error` rather than raising. Plan retries on the agent side based on
  the error string.

## Maintainer

ModuleX core team.
