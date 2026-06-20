# Daytona

Run AI-generated code and shell commands in secure, isolated cloud
sandboxes via the Daytona REST API (`app.daytona.io`) and per-sandbox
toolbox API (`proxy.app.daytona.io/toolbox`). Create and manage
sandboxes, execute commands, run Python/JavaScript/TypeScript, transfer
files, and clone Git repositories.

## Authentication

### API Key

- Sign in at <https://app.daytona.io>, open the dashboard, and go to the
  **Keys** (API Keys) section.
- Create a new API key and copy it.
- Required env var: `DAYTONA_API_KEY`.

The key is sent as `Authorization: Bearer <api_key>` on every request.
The runtime fills the `api_key` parameter from the resolved credential
(not the `auth_type`/`auth_data` pair used by OAuth integrations). The
credential is validated against `GET /api/sandbox?limit=1`.

## Tools

| name | description | required params |
| --- | --- | --- |
| `create_sandbox` | Create a new sandbox for isolated code execution | — |
| `run_code` | Run Python/JavaScript/TypeScript inside a sandbox | `sandbox_id`, `code`, `language` |
| `execute_command` | Execute a shell command inside a sandbox | `sandbox_id`, `command` |
| `upload_file` | Upload a base64-encoded file into a sandbox | `sandbox_id`, `destination_path`, `file_content_base64` |
| `download_file` | Download a file from a sandbox (returned base64-encoded inline) | `sandbox_id`, `file_path` |
| `list_files` | List files in a directory of a sandbox | `sandbox_id` |
| `git_clone` | Clone a Git repository into a sandbox | `sandbox_id`, `url`, `path` |
| `list_sandboxes` | List sandboxes in the organization | — |
| `get_sandbox` | Get details of a sandbox | `sandbox_id` |
| `start_sandbox` | Start a stopped sandbox | `sandbox_id` |
| `stop_sandbox` | Stop a running sandbox | `sandbox_id` |
| `delete_sandbox` | Delete a sandbox | `sandbox_id` |

Every tool also takes an `api_key` parameter that the runtime injects
from the resolved credential.

## Limits & Quotas

- **Downloads**: capped at 100MB; larger files return
  `success=False` with an error. Content is returned base64-encoded
  inline in `content_base64`.
- **Uploads**: provide file bytes via the `file_content_base64`
  parameter.
- **Sandbox IDs**: `get_sandbox`, `start_sandbox`, `stop_sandbox`, and
  `delete_sandbox` accept either the sandbox ID or its name; all other
  sandbox-scoped operations require the ID.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
