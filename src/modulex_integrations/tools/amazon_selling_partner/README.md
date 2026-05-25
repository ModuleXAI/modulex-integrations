# Amazon Selling Partner

Manage orders, inventory, pricing, and reports on Amazon marketplaces via the Amazon Selling Partner API (`sellingpartnerapi-na.amazon.com`).

## Authentication

### OAuth2 Authentication

- Register a Selling Partner API application at the [Amazon Developer Console](https://developer-docs.amazon.com/sp-api/docs/registering-your-application).
- Required env vars: `AMAZON_SP_OAUTH2_CLIENT_ID` (Client ID) and `AMAZON_SP_OAUTH2_CLIENT_SECRET` (Client Secret).
- OAuth redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Amazon SP-API uses Login with Amazon (LWA) OAuth; authorization is role-based rather than scope-based.

## Tools

| name | description | required params |
| --- | --- | --- |
| `check_fba_inventory_levels` | Retrieves inventory summaries from Amazon fulfillment centers to monitor stock availability | `marketplace_id` |
| `fetch_orders_by_date_range` | Retrieves a list of orders based on a specified date range, buyer email, or order ID | `marketplace_id`, `created_after` |
| `generate_sales_inventory_reports` | Requests reports on sales, inventory, and fulfillment performance | `report_types` |
| `get_order_details` | Fetches detailed information about a specific order using its order ID | `marketplace_id`, `amazon_order_id` |
| `list_inbound_shipments` | Fetches inbound shipment details to track stock movement and replenishment | `marketplace_id`, `status` |
| `list_marketplace_id_options` | Retrieves available marketplace participation options for the authenticated seller | (none) |
| `optimize_product_pricing` | Retrieves competitive pricing data to adjust product prices dynamically based on market trends | `marketplace_id`, `item_type`, `values`, `customer_type` |
| `retrieve_sales_performance_reports` | Fetches sales order metrics for visualization in dashboarding tools | `marketplace_id`, `interval`, `granularity` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- SP-API enforces per-endpoint rate limits varying by selling partner type (standard vs. grantless). Typical burst: 1-30 requests/second depending on the endpoint.
- Orders API: 1 request per second burst, with a restore rate of 1 request per second.
- Inventory API: 2 requests per second burst.
- Pricing API: 10 requests per 1 second burst (for `getCompetitivePrice`).
- Reports API: varies per report type; creation is throttled at a lower rate than retrieval.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
