# Okta

Manage users and user-type metadata in an Okta tenant via the Okta Management
REST API (`https://<subdomain>.okta.com/api/v1`).

## Authentication

A single auth method is supported — Okta API tokens (`SSWS`) scoped to a tenant
subdomain. Both the subdomain and the token are required because Okta's host
is tenant-specific.

### Okta API Token

- Sign in to your Okta admin console, open **Security -> API -> Tokens**, and
  click **Create Token**. The SSWS token is shown only once; copy it now.
- Identify your tenant subdomain from your admin URL: for `acme.okta.com` the
  subdomain is `acme` (do not include the `.okta.com` suffix).
- Required env vars:
  - `OKTA_SUBDOMAIN` (format: `acme`) — see
    <https://developer.okta.com/docs/guides/find-your-domain/main/>.
  - `OKTA_API_TOKEN` (format: `00xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`) — see
    <https://developer.okta.com/docs/guides/create-an-api-token/main/>.
- Note: credential validation runs in the tool body (no automatic
  `test_endpoint`) because the modulex credential tester does not template a
  per-tenant subdomain into the URL for custom auth.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_user` | Create a new user; activated by default unless `activate=false`. | `first_name`, `last_name`, `email`, `login` |
| `get_user` | Fetch a single Okta user by ID, login, or email. | `user_id` |
| `list_type_id_options` | Enumerate available user-type IDs for the tenant. | _none_ |
| `update_user` | Partially update an Okta user's profile (existing profile merged with your changes). | `user_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved credential; the integration reads `subdomain` and
`api_token` out of `auth_data` to build the per-tenant URL and the
`Authorization: SSWS <token>` header.

## Limits & Quotas

- Okta enforces per-org rate limits that vary by endpoint and plan; common
  defaults are 600 requests/minute for the Users endpoints on developer orgs
  and higher on production tiers. See
  <https://developer.okta.com/docs/reference/rl-global-mgmt/>.
- Each response includes `X-Rate-Limit-Limit`, `X-Rate-Limit-Remaining`, and
  `X-Rate-Limit-Reset` headers; agents that hit `429` should back off until
  the reset epoch.
- `update_user` issues one `GET` plus one `PUT` per call (the existing profile
  is merged client-side so partial updates do not blank out fields).
- **Error model**: non-2xx responses and timeouts are caught and returned as
  `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
