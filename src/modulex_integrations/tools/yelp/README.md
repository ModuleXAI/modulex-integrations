# Yelp

Search for businesses, read reviews, and get business details via the Yelp Fusion API (`api.yelp.com/v3`).

## Authentication

### API Key Authentication

- Sign in at <https://www.yelp.com/developers> and navigate to "Manage App" or create a new app.
- Copy your API Key from the app settings page.
- Required env var: `YELP_API_KEY` (format: long alphanumeric string).
- The API key is sent as a Bearer token in the Authorization header.

## Tools

| name | description | required params |
| --- | --- | --- |
| `search_businesses` | Search businesses matching given criteria such as location, term, categories, price, and attributes | (one of `location` or `latitude`+`longitude`) |
| `get_business_details` | Get detailed information about a specific business by its Yelp ID or alias | `business_id_or_alias` |
| `list_business_reviews` | List the reviews for a specific business | `business_id_or_alias` |
| `search_businesses_by_phone_number` | Search for businesses by phone number | `phone` |

Every tool takes an additional `api_key` parameter that the runtime fills in from the resolved credential.

## Limits & Quotas

- **Rate limit**: 5,000 API calls per day (per Yelp Fusion free tier).
- **Search pagination**: Maximum offset of 1,000 results; each page returns up to 50 businesses.
- **Reviews**: Returns up to 3 reviews per business (Yelp API limitation).
- **Error model**: Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
