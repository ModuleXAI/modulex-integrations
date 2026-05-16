# Coinbase

Cryptocurrency trading and wallet management via the **Coinbase
Developer Platform (CDP) API** (v2 + v3 brokerage). Pure HTTP; the
only runtime dependency added is `cryptography` for local JWT signing.

## Authentication

- **`custom` auth_type.** CDP credentials are a key *pair* (key ID +
  private key material) — neither the standard `api_key` nor `oauth2`
  schemas fit, so this lands on `CustomAuthSchema`.
- Env vars: `COINBASE_API_KEY` (key ID, not sensitive) +
  `COINBASE_API_SECRET` (PEM-for-ECDSA or base64-for-Ed25519,
  sensitive).
- **No `test_endpoint`** — every CDP request needs a fresh JWT
  signature, which the credential-tester layer doesn't construct. The
  runtime simply skips validation.

## Runtime convention

Token-based: every `@tool` accepts `(auth_type, auth_data, ...)`.
`auth_type` is informational; the tool body pulls `api_key` /
`api_secret` directly out of `auth_data` and mints a fresh JWT
per request.

## JWT signing

`generate_jwt(api_key_id, api_key_secret, method, path)` picks Ed25519
(EdDSA) or ECDSA (ES256) based on whether the secret looks like a
PEM. Both signing helpers lazy-import from `cryptography` to keep the
package importable even without that dep installed (useful for
manifest-only inspection in the modulex runtime).

## Tools

| name | description |
| --- | --- |
| `get_accounts` | List all wallets/portfolios |
| `get_account` | One wallet by ID |
| `get_transactions` | Historical order fills (v3 fills API) |
| `place_buy_order` | Market buy (IOC) — `amount` is USD quote spend |
| `withdraw_funds` | Crypto withdrawal to external address |
| `get_exchange_rates` | Rates table for a base currency |
| `get_spot_price` | Current spot price for a pair |
| `get_payment_methods` | All configured payment methods |

## Notes

- 30s timeout on every request.
- Every action wraps the body in `try/except` → unified
  `success=False` envelope (exa-style).
- `place_buy_order` checks for Coinbase's `error_response` block in
  the 200 body (CDP returns 200 with a structured failure for order
  rejections).

## Maintainer

ModuleX core team.
