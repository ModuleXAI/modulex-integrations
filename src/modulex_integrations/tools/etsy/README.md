# Etsy

Manage Etsy marketplace listings, inventory, and properties via the Etsy Open API v3 (`openapi.etsy.com/v3`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth app at <https://www.etsy.com/developers/your-apps>.
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Scopes requested: `listings_r`, `listings_w`, `listings_d`, `transactions_r`, `shops_r`
- Required env vars (custom app only): `ETSY_OAUTH2_CLIENT_ID`, `ETSY_OAUTH2_CLIENT_SECRET`

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_draft_listing_product` | Creates a physical draft listing product in a shop on Etsy | `quantity`, `title`, `description`, `price`, `who_made`, `when_made`, `taxonomy_id`, `is_supply`, `listing_type` |
| `delete_listing` | Delete an Etsy listing by listing ID | `listing_id` |
| `get_listing` | Retrieve an Etsy listing record by listing ID | `listing_id` |
| `get_listing_inventory` | Retrieve the inventory record for a listing by listing ID | `listing_id` |
| `update_listing_inventory` | Update the inventory for a listing identified by listing ID | `listing_id` |
| `update_listing_property` | Update or populate the properties list defining product offerings for a listing | `listing_id`, `property_id`, `value_ids`, `values` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth2 credential.

## Limits & Quotas

- Etsy Open API v3 rate limit: 10,000 requests per day per API key.
- Burst limit: approximately 10 requests per second.
- Error model: non-2xx responses raise `httpx.HTTPStatusError` (Pattern A). The agent should retry on 429/5xx.

## Maintainer

ModuleX core team.
