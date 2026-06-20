# Kalshi

Access Kalshi prediction markets and trade event contracts against the
Kalshi Trade API v2 (`api.elections.kalshi.com/trade-api/v2`). Retrieve
markets, events, series, orderbooks, trades, and candlesticks; manage
your balance, positions, orders, fills, and settlements; check exchange
status; and place, cancel, or amend orders.

## Authentication

Kalshi does not use a static bearer token. Each request is signed with
your RSA private key: the runtime sends `KALSHI-ACCESS-KEY` (your key
id), `KALSHI-ACCESS-TIMESTAMP` (Unix milliseconds), and
`KALSHI-ACCESS-SIGNATURE` (a base64 RSA-PSS / SHA-256 signature over
`timestamp + METHOD + path`). The signing material never leaves the
runtime.

### API Key Authentication

- Sign in at <https://kalshi.com> and open **Account → API Keys**.
- Create a new API key; download the RSA private key (PEM) and copy the
  **Key ID**.
- Required env vars:
  - `KALSHI_KEY_ID` — your API Key ID.
  - `KALSHI_PRIVATE_KEY` — the full PEM private key (sensitive). Keys
    pasted with escaped newlines or wrapped lines are normalized
    automatically.

Both values are injected into every action as `key_id` / `private_key`.
Public market-data actions (`get_markets`, `get_market`, `get_events`,
`get_event`, `get_orderbook`, `get_trades`, `get_candlesticks`,
`get_event_candlesticks`, `get_series_by_ticker`, `get_series_list`,
`get_exchange_status`, `get_exchange_schedule`,
`get_exchange_announcements`) do not require a signature and run without
credentials.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_markets` | List prediction markets with full filtering | — |
| `get_market` | Get one market by ticker | `ticker` |
| `get_events` | List events with optional filtering | — |
| `get_event` | Get one event by ticker | `event_ticker` |
| `get_balance` | Account balance and portfolio value | `key_id`, `private_key` |
| `get_positions` | Open market and event positions | `key_id`, `private_key` |
| `get_orders` | Your orders with optional filtering | `key_id`, `private_key` |
| `get_order` | Get one order by ID | `key_id`, `private_key`, `order_id` |
| `get_orderbook` | Yes/no bids for a market | `ticker` |
| `get_trades` | Recent public trades | — |
| `get_candlesticks` | OHLC candlesticks for a market | `series_ticker`, `ticker`, `start_ts`, `end_ts`, `period_interval` |
| `get_event_candlesticks` | Event-level aggregated candlesticks | `series_ticker`, `event_ticker`, `start_ts`, `end_ts`, `period_interval` |
| `get_fills` | Your portfolio fills/trades | `key_id`, `private_key` |
| `get_settlements` | Your settlement history | `key_id`, `private_key` |
| `get_series_by_ticker` | Get one series by ticker | `series_ticker` |
| `get_series_list` | List market series with filtering | — |
| `get_exchange_status` | Current exchange/trading status | — |
| `get_exchange_schedule` | Trading schedule and maintenance windows | — |
| `get_exchange_announcements` | Exchange-wide announcements | — |
| `create_order` | Place a new order | `key_id`, `private_key`, `ticker`, `side`, `action` |
| `cancel_order` | Cancel an existing order | `key_id`, `private_key`, `order_id` |
| `amend_order` | Modify an order's price or quantity | `key_id`, `private_key`, `order_id`, `ticker`, `side`, `action` |

## Limits & Quotas

- **Base URL**: `https://api.elections.kalshi.com/trade-api/v2`.
- **Pricing**: prices and counts are returned in cents (and as
  fixed-point `_fp` / dollar string variants where the API provides
  them).
- **Rate limits**: Kalshi enforces per-tier request rate limits; consult
  the official docs for current values. Authenticated portfolio and
  trading calls are signed per request, so clock skew on the host can
  cause signature rejections — keep the system clock in sync.
- **Error model**: non-2xx responses, timeouts, invalid private keys,
  and unexpected exceptions are caught and returned as `success=False` +
  `error` rather than raising. On failure the data fields stay at their
  defaults.

## Maintainer

ModuleX core team.
