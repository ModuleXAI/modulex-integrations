# LinkedIn

Professional social networking platform for managing posts, comments, likes, profiles, organizations, and ad accounts via the LinkedIn REST API (`api.linkedin.com/rest`).

## Authentication

### OAuth2 Authentication (recommended)

- Create a LinkedIn app at <https://www.linkedin.com/developers/apps>.
- Register the redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`.
- Required env vars (only for custom OAuth app):
  - `LINKEDIN_OAUTH2_CLIENT_ID` — your app's Client ID
  - `LINKEDIN_OAUTH2_CLIENT_SECRET` — your app's Client Secret
- Scopes requested: `openid`, `profile`, `email`, `w_member_social`, `r_organization_social`, `w_organization_social`, `rw_organization_admin`, `r_ads`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_comment` | Create a comment on a share or user generated content post | `urn_to_comment`, `actor`, `message` |
| `create_image_post_organization` | Create an image post on LinkedIn as an organization | `organization_id`, `image_url`, `text` |
| `create_image_post_user` | Create an image post on LinkedIn as the authenticated user | `image_url`, `text`, `visibility` |
| `create_like_on_share` | Create a like on a share or user generated content post | `parent_urn`, `actor`, `object` |
| `create_text_post_organization` | Create a text post on LinkedIn as an organization, optionally with an article URL | `organization_id`, `text` |
| `create_text_post_user` | Create a text post on LinkedIn as the authenticated user, optionally with an article URL | `visibility`, `text` |
| `delete_post` | Delete a post from LinkedIn | `post_id` |
| `fetch_ad_account` | Fetch an individual ad account given its ID | `ad_account_id` |
| `get_current_member_profile` | Get the profile of the current authenticated member | (none) |
| `get_member_profile` | Get another member's profile given their person ID | `person_id` |
| `get_multiple_member_profiles` | Get multiple member profiles at once given their person IDs | `people_ids` |
| `get_org_member_access` | Get the organization access control information of the current authenticated member | (none) |
| `get_organization_access_control` | Get a selected organization's access control information | `organization_id` |
| `get_organization_administrators` | Get the administrator members of a selected organization | `organization_id` |
| `get_profile_picture_fields` | Get the authenticated user's profile picture data including display image and metadata | (none) |
| `retrieve_comments_on_comments` | Retrieve comments on a comment given the parent comment URN | `comment_urn` |
| `retrieve_comments_shares` | Retrieve comments on a share given the share URN | `entity_urn` |
| `search_organization` | Search for an organization by vanity name or email domain | `search_by`, `search_term` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- LinkedIn API rate limits vary by product and endpoint. Generally 100 requests per day for most marketing/community management endpoints per OAuth app.
- Organization-level posting endpoints are subject to daily limits per organization.
- The `LinkedIn-Version` header is hardcoded to `202509`; LinkedIn periodically deprecates older API versions.
- Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
