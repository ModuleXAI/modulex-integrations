# CoinMarketCap

Cryptocurrency market data, quotes, and metadata from the CoinMarketCap REST API (`pro-api.coinmarketcap.com`).

## Authentication

### API Key Authentication

- Sign up at <https://coinmarketcap.com/api/> to get your API key.
- Required env var: `COINMARKETCAP_API_KEY` (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).
- The API key is passed via the `X-CMC_PRO_API_KEY` header on every request.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_cryptocurrency_metadata` | Returns all static metadata available for one or more cryptocurrencies | `ids` |
| `id_map` | Returns a mapping of all cryptocurrencies to unique CoinMarketCap IDs | _(none)_ |
| `latest_listings` | Returns a paginated list of all active cryptocurrencies with latest market data | _(none)_ |
| `latest_quotes` | Returns the latest market quote for one or more cryptocurrencies | _(none — but at least one of id, slug, or symbol must be provided)_ |

Every tool takes an additional `api_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- **Basic (free) plan**: 333 calls/day, 10,000 calls/month.
- **Hobbyist plan**: 10,000 calls/month.
- **Standard plan and above**: higher limits per the pricing page.
- Rate limiting is applied per API key. Exceeding limits returns HTTP 429.
- **Error model**: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
