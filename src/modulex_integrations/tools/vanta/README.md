# Vanta

Query compliance posture and manage evidence in Vanta — frameworks, controls, automated tests, evidence documents, people, policies, vendors, monitored computers, vulnerabilities, and risk scenarios — via the Vanta v1 REST API (`https://api.vanta.com/v1`, or `https://api.vanta-gov.com/v1` for the FedRAMP region).

## Authentication

### Vanta OAuth Client Credentials (custom)

- Create an API application under **Settings → Developer Console** in Vanta and
  copy its **Client ID** and **Client Secret** (the Secret is shown only once).
- Grant the application read scopes; add the `vanta-api.documents:upload` and
  write scopes if you need evidence upload or document submission.
- Env vars: `VANTA_CLIENT_ID`, `VANTA_CLIENT_SECRET`, `VANTA_REGION`
  (`us` — default — or `gov`).
- The tool performs the OAuth2 `client_credentials` grant itself: on each call
  it exchanges the Client ID + Secret at `POST /oauth/token` for a short-lived
  bearer token, then calls the API with `Authorization: Bearer <token>`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_frameworks` | List compliance frameworks with completion counts | (none) |
| `get_framework` | Get a framework by ID with requirement categories | `framework_id` |
| `list_framework_controls` | List a framework's controls | `framework_id` |
| `list_controls` | List security controls, optionally filtered by framework | (none) |
| `get_control` | Get a control by ID with status and evidence counts | `control_id` |
| `list_control_tests` | List tests mapped to a control | `control_id` |
| `list_control_documents` | List documents mapped to a control | `control_id` |
| `list_tests` | List automated tests with status/framework/category filters | (none) |
| `get_test` | Get a test by ID with status and remediation info | `test_id` |
| `list_test_entities` | List failing/deactivated entities for a test | `test_id` |
| `list_documents` | List evidence documents with framework/status filters | (none) |
| `get_document` | Get a document by ID with renewal and deactivation status | `document_id` |
| `list_document_uploads` | List files uploaded to a document | `document_id` |
| `upload_document_file` | Upload a base64 evidence file to a document | `document_id`, `file_content`, `file_name` |
| `download_document_file` | Download an uploaded file as base64 content | `document_id`, `uploaded_file_id` |
| `submit_document` | Submit a document collection for auditor review | `document_id` |
| `list_people` | List people with employment, groups, and task status | (none) |
| `get_person` | Get a person by ID | `person_id` |
| `list_policies` | List security policies with approval status | (none) |
| `get_policy` | Get a policy by ID with latest approved version | `policy_id` |
| `list_vendors` | List vendors with risk levels and contract dates | (none) |
| `get_vendor` | Get a vendor by ID | `vendor_id` |
| `list_monitored_computers` | List monitored computers with device check outcomes | (none) |
| `list_vulnerabilities` | List vulnerabilities with severity/SLA filters | (none) |
| `list_vulnerability_remediations` | List remediated vulnerabilities | (none) |
| `list_vulnerable_assets` | List vulnerable assets | (none) |
| `get_vulnerable_asset` | Get a vulnerable asset by ID with scanner details | `vulnerable_asset_id` |
| `list_risk_scenarios` | List risk register scenarios with scores and treatments | (none) |
| `get_risk_scenario` | Get a risk scenario by ID | `risk_scenario_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime
fills in from the resolved credential. List tools accept optional `page_size`,
`page_cursor`, and `max_pages` (default 1) for cursor pagination.

## Limits & Quotas

- The Manage Vanta API is rate-limited to roughly 50 requests/minute; consult
  your Vanta plan for exact limits.
- Vanta keeps only one access token active per application — the tool exchanges
  a fresh token per call.
- List actions auto-paginate up to `max_pages` (default 1); raise it to gather
  more pages in one call.
- Error model: non-2xx responses (including auth failures) are caught and
  returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
