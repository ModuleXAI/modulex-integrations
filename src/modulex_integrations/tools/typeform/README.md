# Typeform

Online form builder for surveys, quizzes, and interactive forms via the Typeform REST API (`api.typeform.com`).

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth app at <https://admin.typeform.com/account#/section/tokens>.
- Required redirect URI: `https://api.modulex.dev/credentials/oauth2/callback`
- Scopes requested: `forms:read`, `forms:write`, `images:read`, `images:write`, `responses:read`, `accounts:read`, `workspaces:read`
- Env vars (custom app only): `TYPEFORM_OAUTH2_CLIENT_ID`, `TYPEFORM_OAUTH2_CLIENT_SECRET`

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_forms` | Retrieves a list of forms from your Typeform account | |
| `create_form` | Creates a new form with the specified title | `title` |
| `duplicate_form` | Duplicates an existing form and adds (copy) to the end of the title | `form_id` |
| `delete_form` | Deletes a form from your Typeform account | `form_id` |
| `list_images` | Retrieves a list of all images in your Typeform account | |
| `get_form` | Retrieves the details of a specific form | `form_id` |
| `lookup_responses` | Search for form responses matching a query string | `form_id`, `query` |
| `list_responses` | Returns form responses and date and time of form landing and submission | `form_id` |
| `update_form_title` | Updates an existing form's title | `form_id`, `title` |
| `delete_image` | Deletes an image from your Typeform account | `image_id` |
| `create_image` | Adds an image to your Typeform account | `file_name` |
| `update_dropdown_multiple_choice_ranking` | Update a dropdown, multiple choice, or ranking field's choices by adding a new choice | `form_id`, `field_id`, `choice` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth2 credential.

## Limits & Quotas

- **Rate limit**: Typeform API allows up to 2 requests per second per OAuth token.
- **Responses endpoint**: Maximum 1000 responses per request (page_size cap).
- **Error model**: Non-2xx responses are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
