# Shopify

E-commerce platform integration for managing products, orders, customers, collections, blogs, pages, metafields, metaobjects, fulfillments, and inventory via the Shopify Admin GraphQL API (`{shop_id}.myshopify.com/admin/api/2025-01/graphql.json`).

## Authentication

### Shopify OAuth Access Token

Shopify uses shop-specific OAuth URLs (`https://{shop}.myshopify.com/admin/oauth/authorize`), which require custom auth handling. You need a Shopify Admin API access token, obtainable by creating a custom app in the Shopify Partner Dashboard or store admin.

- Required env var: `SHOPIFY_SHOP_ID` (your store subdomain, e.g. `my-store` from `my-store.myshopify.com`)
- Required env var: `SHOPIFY_ACCESS_TOKEN` (format: `shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
- Create a custom app at <https://admin.shopify.com> > Settings > Apps and sales channels > Develop apps
- Grant the necessary Admin API access scopes: `read_products`, `write_products`, `read_orders`, `write_orders`, `read_customers`, `read_content`, `write_content`, `read_inventory`, `write_inventory`, `read_fulfillments`, `read_assigned_fulfillment_orders`, `read_draft_orders`, `write_draft_orders`

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_product_to_custom_collection` | Add one or more products to a custom collection | `shop_id`, `collection_id`, `product_ids` |
| `add_tags` | Add tags to a Shopify resource | `shop_id`, `resource_type`, `gid`, `tags` |
| `create_article` | Create a new blog article | `shop_id`, `blog_id`, `title`, `author` |
| `create_blog` | Create a new blog | `shop_id`, `title` |
| `create_custom_collection` | Create a new custom collection | `shop_id`, `title` |
| `create_metafield` | Create a metafield definition | `shop_id`, `owner_resource`, `name`, `namespace`, `key`, `type` |
| `create_metaobject` | Create a metaobject | `shop_id`, `type` |
| `create_page` | Create a new page | `shop_id`, `title`, `body` |
| `create_product` | Create a new product | `shop_id`, `title` |
| `create_product_variant` | Create a new product variant | `shop_id`, `product_id`, `option_ids` |
| `create_smart_collection` | Create a smart collection with rules | `shop_id`, `title`, `rules` |
| `delete_article` | Delete a blog article | `shop_id`, `article_id` |
| `delete_blog` | Delete a blog | `shop_id`, `blog_id` |
| `delete_metafield` | Delete a metafield | `shop_id`, `metafield_id` |
| `delete_page` | Delete a page | `shop_id`, `page_id` |
| `get_articles` | Retrieve articles from a blog | `shop_id`, `blog_id` |
| `get_assigned_fulfillment_orders` | Retrieve assigned fulfillment orders | `shop_id` |
| `get_customer` | Retrieve a customer by ID | `shop_id`, `customer_id` |
| `get_customers` | Retrieve a list of customers | `shop_id` |
| `get_draft_order` | Retrieve a draft order by ID | `shop_id`, `draft_order_id` |
| `get_draft_orders` | Retrieve a list of draft orders | `shop_id` |
| `get_fulfillment` | Retrieve a fulfillment by ID | `shop_id`, `fulfillment_id` |
| `get_fulfillment_order` | Retrieve a fulfillment order by ID | `shop_id`, `fulfillment_order_id` |
| `get_fulfillment_orders` | Retrieve a list of fulfillment orders | `shop_id` |
| `get_metafields` | Retrieve metafields for a resource | `shop_id`, `owner_resource`, `owner_id` |
| `get_metaobjects` | Retrieve metaobjects by type | `shop_id`, `type` |
| `get_pages` | Retrieve a list of pages | `shop_id` |
| `search_custom_collection_by_name` | Search collections by name | `shop_id` |
| `search_orders` | Search for orders | `shop_id` |
| `search_product_variant` | Search for a product variant | `shop_id`, `product_id` |
| `search_products` | Search for products | `shop_id` |
| `update_article` | Update a blog article | `shop_id`, `article_id` |
| `update_inventory_level` | Set inventory level at a location | `shop_id`, `location_id`, `inventory_item_id`, `available`, `reason` |
| `update_metafield` | Update a metafield value | `shop_id`, `owner_id`, `metafield_id`, `value` |
| `update_metaobject` | Update a metaobject | `shop_id`, `metaobject_id` |
| `update_order` | Update an existing order | `shop_id`, `order_id` |
| `update_page` | Update a page | `shop_id`, `page_id` |
| `update_product` | Update a product | `shop_id`, `product_id` |
| `update_product_variant` | Update a product variant | `shop_id`, `product_id`, `product_variant_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential. The `shop_id` parameter is required for every action to construct the shop-specific GraphQL endpoint URL.

## Limits & Quotas

- **Standard Shopify API rate limit**: 50 points per second for the GraphQL Admin API (each query/mutation costs 1+ points depending on complexity).
- **Throttling**: Shopify returns `THROTTLED` errors in the GraphQL response extensions when the limit is exceeded. Retry after a short delay.
- **Pagination**: List actions are capped at 250 items per request via the GraphQL `first` argument. For larger datasets, implement cursor-based pagination.
- **Error model**: GraphQL `userErrors` arrays are returned inline as `success=False` + `error` with the first error message. HTTP-level errors (network, auth) are caught and returned as `success=False` + `error`.

## Maintainer

ModuleX core team.
