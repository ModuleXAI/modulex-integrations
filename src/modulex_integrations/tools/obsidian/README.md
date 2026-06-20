# Obsidian

Read, create, update, search, and delete notes in your Obsidian vault
via the [Obsidian Local REST API](https://obsidian.md) plugin. Manage
periodic notes, list and execute commands, work with the active file,
and patch content at specific headings, block references, or
frontmatter fields.

The plugin runs locally inside your Obsidian app and is reachable at a
`base_url` you pass on every call (default `https://127.0.0.1:27124`).
Because the plugin serves a self-signed TLS certificate, the HTTP
client does not verify the certificate chain.

## Authentication

### API Key

- Install the **Local REST API** community plugin in Obsidian and
  enable it.
- Open the plugin settings and copy the generated **API key**.
- Note the server URL shown in the plugin settings (default
  `https://127.0.0.1:27124`); supply it as the `base_url` parameter on
  each action.
- Required env var: `OBSIDIAN_API_KEY` (sensitive).

The key is sent as `Authorization: Bearer <api_key>` on every request.

## Tools

| name | description | required params |
| --- | --- | --- |
| `list_files` | List files and directories in the vault | `base_url` |
| `get_note` | Retrieve a note's Markdown content | `base_url`, `filename` |
| `create_note` | Create or replace a note | `base_url`, `filename`, `content` |
| `append_note` | Append content to an existing note | `base_url`, `filename`, `content` |
| `patch_note` | Insert/replace at a heading, block, or frontmatter field | `base_url`, `filename`, `content`, `operation`, `target_type`, `target` |
| `delete_note` | Delete a note | `base_url`, `filename` |
| `search` | Search text across vault notes | `base_url`, `query` |
| `get_active` | Read the currently active file | `base_url` |
| `append_active` | Append to the active file | `base_url`, `content` |
| `patch_active` | Patch at a target in the active file | `base_url`, `content`, `operation`, `target_type`, `target` |
| `open_file` | Open a file in the Obsidian UI | `base_url`, `filename` |
| `list_commands` | List available Obsidian commands | `base_url` |
| `execute_command` | Execute a command by ID | `base_url`, `command_id` |
| `get_periodic_note` | Read the current periodic note | `base_url`, `period` |
| `append_periodic_note` | Append to the current periodic note | `base_url`, `period`, `content` |

Every tool also takes an `api_key` parameter that the runtime fills in
from the resolved credential (the modulex `api_key` injection
convention). `base_url` is a required parameter, not a credential — it
points at the user's local plugin server.

## Limits & Quotas

- The Local REST API runs on the user's own machine, so throughput is
  bound only by the local Obsidian instance; there is no vendor rate
  limit.
- `base_url` must be reachable from where the runtime executes
  (typically the same host). The default `https://127.0.0.1:27124` only
  works for a co-located process.
- **Error model**: non-2xx responses and timeouts are caught and
  returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
