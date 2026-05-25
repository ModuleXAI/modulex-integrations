# Pipedrive

Sales CRM and pipeline management platform. Connects to the Pipedrive REST API
(`{your-domain}.pipedrive.com/api/v1` and `/api/v2`) to manage deals, contacts,
leads, activities, organizations, and notes.

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth app at the [Pipedrive Developer Hub](https://developers.pipedrive.com/).
- Redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Scopes requested: `deals:full`, `contacts:full`, `leads:full`, `activities:full`, `search:read`, `users:read`, `admin`
- Env vars (only when using your own OAuth app):
  - `PIPEDRIVE_OAUTH2_CLIENT_ID` — your app's Client ID
  - `PIPEDRIVE_OAUTH2_CLIENT_SECRET` — your app's Client Secret

The OAuth token response includes an `api_domain` field (e.g. `https://yourcompany.pipedrive.com`) which is used as the base URL for all API calls.

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_activity` | Add a new activity in Pipedrive | `subject`, `type` |
| `add_deal` | Add a new deal in Pipedrive | `title` |
| `add_labels` | Add labels to a lead, person, deal, or organization | `type`, `label_ids` |
| `add_lead` | Create a new lead in Pipedrive | `title` |
| `add_note` | Add a new note to a lead, deal, person, or organization | `content` |
| `add_organization` | Add a new organization in Pipedrive | `name` |
| `add_person` | Add a new person (contact) in Pipedrive | `name` |
| `get_all_leads` | Get all leads with optional filtering | — |
| `get_deal` | Get a deal by its ID | `deal_id` |
| `get_lead_by_id` | Get a lead by its ID | `lead_id` |
| `get_person_details` | Get details of a person by their ID | `person_id` |
| `list_deals` | List deals with optional filtering and pagination | — |
| `list_lead_label_ids_options` | Retrieve available lead label options | — |
| `list_organization_label_ids_options` | Retrieve available organization label options | — |
| `list_person_label_ids_options` | Retrieve available person label options | — |
| `list_user_id_options` | Retrieve available user options | — |
| `merge_deals` | Merge two deals | `deal_id`, `target_deal_id` |
| `merge_persons` | Merge two persons | `person_id`, `target_person_id` |
| `remove_duplicate_notes` | Remove duplicate notes from an object | — |
| `remove_labels` | Remove labels from a lead, person, deal, or organization | `type`, `entity_id`, `label_ids` |
| `search_leads` | Search for leads by name or email | `term` |
| `search_notes` | Search for notes with filtering options | — |
| `search_persons` | Search for persons by name, email, phone, or notes | `term` |
| `update_deal` | Update the properties of a deal | `deal_id` |
| `update_lead` | Update a lead | `lead_id` |
| `update_person` | Update an existing person | `person_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential. The `auth_data` includes `access_token` and `api_domain`.

## Limits & Quotas

- **Rate limits**: Pipedrive enforces per-plan rate limits. Professional plan: 200 requests/10 seconds; Enterprise plan: 400 requests/10 seconds. Exceeding the limit returns HTTP 429.
- **Pagination**: List endpoints use cursor-based (v2) or offset-based (v1) pagination. The `list_deals` tool supports cursor; `get_all_leads` auto-paginates.
- **Error model**: Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising. The error string includes the HTTP status code and response body for debugging.

## Maintainer

ModuleX core team.
