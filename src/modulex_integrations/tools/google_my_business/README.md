# Google My Business

Manage Google Business Profile posts, reviews, and replies via the Google My Business API (`mybusiness.googleapis.com/v4`).

## Authentication

### OAuth2 Authentication

- Sign in at the [Google Cloud Console](https://console.cloud.google.com/apis/credentials), create an OAuth 2.0 client, and enable the Google My Business API.
- Required env vars (only when bringing your own OAuth app):
  - `GOOGLE_MY_BUSINESS_OAUTH2_CLIENT_ID` (format: `123456789-xxx.apps.googleusercontent.com`)
  - `GOOGLE_MY_BUSINESS_OAUTH2_CLIENT_SECRET` (format: `GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx`)
- Scopes requested: `https://www.googleapis.com/auth/business.manage`
- Redirect URI to register: `https://api.modulex.dev/credentials/oauth2/callback`

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_post` | Create a new local post associated with a location | `account`, `location`, `topic_type` |
| `create_update_reply_to_review` | Create or update a reply to the specified review | `account`, `location`, `review`, `comment` |
| `get_reviews_multiple_locations` | Get reviews from multiple locations at once | `account`, `location_names` |
| `get_specific_review` | Return a specific review by name | `account`, `location`, `review` |
| `list_all_reviews` | List all reviews of a location to audit reviews in bulk | `account`, `location` |
| `list_posts` | List local posts associated with a location | `account`, `location` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- Google My Business API is subject to Google Cloud project quotas (typically 60 requests/minute per project by default).
- Some endpoints may return 429 status if quota is exceeded.
- Error model: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
