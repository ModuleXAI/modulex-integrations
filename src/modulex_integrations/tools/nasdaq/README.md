# Nasdaq Data Link

Read-only access to the Nasdaq Data Link E360 platform via the
official ``nasdaqdatalink`` Python SDK. Covers balance sheets, cash
flows, company stats, fundamental details/summary, and reference
data for publicly traded companies.

## Authentication

### API Key (query string)

- Required env var: `NASDAQ_API_KEY`.
- Sign up at <https://data.nasdaq.com/sign-up>, copy your key.
- Credential validation: GET against
  `data.nasdaq.com/api/v3/datatables/NDAQ/RD.json?api_key=<key>` —
  uses the new `TestEndpoint.params` field (`?api_key={api_key}`).
- At runtime, the SDK reads the key from global mutable state:
  `nasdaqdatalink.ApiConfig.api_key = <key>` set per call. Ugly,
  but it's the SDK's documented auth contract.

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_balance_sheet` | NDAQ/BS table | symbol OR figi |
| `get_cash_flow` | NDAQ/CF table | symbol OR figi |
| `get_company_stats` | NDAQ/STAT table | symbol OR figi |
| `get_fundamental_details` | NDAQ/FD table | symbol OR figi |
| `get_fundamental_summary` | NDAQ/FS table | symbol OR figi |
| `get_reference_data` | NDAQ/RD table | — (legacy permissive) |
| `list_available_fields` | hardcoded field reference (no API call) | `table_type` |

## Limits & Quotas

- Subscription-gated. E360 endpoints require an active Nasdaq Data
  Link subscription on the NDAQ table family.
- DataFrame results are converted to JSON-safe lists of dicts
  (`NaN` → `None`). Empty DataFrames return `records=[]` with a
  `message: "No data found..."` (matches legacy).
- Lazy SDK import — if `nasdaq-data-link` isn't installed, every
  table-query tool degrades to `success=False` with an "install
  with: pip install nasdaq-data-link" error.

## Maintainer

ModuleX core team.
