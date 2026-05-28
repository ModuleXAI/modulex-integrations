# Instructure Canvas LMS

Learning management system integration for [Instructure Canvas](https://www.instructure.com/canvas) — course, assignment, and user management via the Canvas REST API (`https://{your-domain}/api/v1`).

## Authentication

### Canvas OAuth Token + Domain

Canvas LMS is self-hosted (each institution runs its own instance), so both your instance domain and an access token are required.

- **Canvas Domain**: Your Canvas instance hostname (e.g. `myschool.instructure.com`). Required env var: `CANVAS_DOMAIN`.
- **Access Token**: Generate from Account > Settings > Approved Integrations in your Canvas instance. Required env var: `CANVAS_ACCESS_TOKEN` (format: `7~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).
- Guide: [Managing API Access Tokens](https://community.canvaslms.com/t5/Admin-Guide/How-do-I-manage-API-access-tokens-as-an-admin/ta-p/89)

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_accounts` | List Canvas accounts accessible to the authenticated user. | _(none)_ |
| `list_assignments` | Retrieve a list of assignments for a user in a specific course. | `user_id`, `course_id` |
| `list_courses` | List all courses associated with a given user. | `user_id` |
| `search_course_content` | Search for content in a course using Canvas smart search. | `course_id`, `query` |
| `update_assignment` | Update an existing assignment in a course. | `course_id`, `assignment_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved credential (token-style injection).

## Limits & Quotas

- **Rate limits**: Canvas enforces per-user rate limits (typically 700 requests per 10 minutes for the default configuration, varies by institution).
- **Pagination**: List endpoints may return paginated results; current implementation fetches the first page.
- **Error model**: Non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
