# WooCommerce

Manage orders, products, customers, refunds, and payment methods on self-hosted WooCommerce stores via the WooCommerce REST API (`{store_url}/wp-json/wc/v3`).

## Authentication

### WooCommerce REST API Credentials

- Go to your WordPress admin panel > WooCommerce > Settings > Advanced > REST API.
- Click "Add key", give it a description, choose Read/Write permissions, and generate.
- Required env vars:
  - `WOOCOMMERCE_STORE_URL` — your store's base URL (e.g. `https://mystore.com`)
  - `WOOCOMMERCE_CONSUMER_KEY` — format: `ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
  - `WOOCOMMERCE_CONSUMER_SECRET` — format: `cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- Note: The store must be served over HTTPS for this integration to work (uses HTTP Basic Auth). HTTP-only stores requiring OAuth 1.0a signing are not supported.
- Docs: <https://woocommerce.github.io/woocommerce-rest-api-docs/#authentication>

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_order` | Create a new order in the WooCommerce store. | — |
| `get_order` | Retrieve a specific order by ID. | `order_id` |
| `list_orders` | Retrieve a list of orders with optional filters. | — |
| `delete_order` | Delete an existing order. | `order_id` |
| `update_order_status` | Update the status of a specific order. | `order_id`, `status` |
| `create_product` | Create a new product in the WooCommerce store. | `name` |
| `update_product` | Update an existing product. | `product_id` |
| `get_product` | Retrieve a specific product by ID. | `product_id` |
| `list_products` | Retrieve a list of products with optional filters. | — |
| `search_customers` | Search for customers by email, name, or other criteria. | — |
| `get_customer` | Retrieve a specific customer by ID. | `customer_id` |
| `create_customer` | Create a new customer. | `email` |
| `add_order_note` | Create a new note for an order. | `order_id`, `note` |
| `get_order_note` | Retrieve a specific order note. | `order_id`, `note_id` |
| `list_order_notes` | Retrieve all notes for a specific order. | `order_id` |
| `create_refund` | Create a new refund for an order. | `order_id` |
| `list_payment_method_options` | Retrieve available payment gateway options. | — |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential (custom auth with store_url, consumer_key, and consumer_secret).

## Limits & Quotas

- WooCommerce REST API rate limits depend on the hosting provider and server configuration. Most managed hosts enforce 60-120 requests/minute.
- Pagination is server-controlled; responses include `X-WP-Total` and `X-WP-TotalPages` headers.
- Error model: non-2xx responses are caught and returned as `success=False` + `error` rather than raising. Plan for retries on the agent side based on the error string.
- No per-request pricing — WooCommerce is self-hosted.

## Maintainer

ModuleX core team.
