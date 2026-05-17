# Instacart

Public Instacart actions: build shareable recipe + shopping-list pages
and look up retailers by postal code. No API key required.

## Authentication

`modulex_key` only — placeholder credential, not used in requests.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_recipe_page` | Build a shareable Instacart recipe URL | `title`, `ingredients` |
| `create_shopping_list_page` | Build a shareable shopping list URL | `title`, `items` |
| `get_nearby_retailers` | List retailers serving a postal code | `postal_code` |

## Limits & Quotas

- Recipe/list pages are pure URL builders (no API hit).
- Retailer lookup goes to Instacart's public `/v3/retailers` endpoint;
  on timeout or non-200 the tool returns a store-finder URL as a
  usable fallback (still `success=True`).
- Country supported: `US`, `CA`.

## Maintainer

ModuleX core team.
