# DigitalOcean

Cloud infrastructure management via the DigitalOcean REST API (`api.digitalocean.com/v2`). Create and manage Droplets, domains, SSH keys, and snapshots.

## Authentication

### OAuth2 Authentication (recommended)

- Register an OAuth application at <https://cloud.digitalocean.com/account/api/applications/new>.
- Set the redirect URI to `https://api.modulex.dev/credentials/oauth2/callback`.
- Scopes requested: `read`, `write`.
- Required env vars (only for custom OAuth apps):
  - `DIGITAL_OCEAN_OAUTH2_CLIENT_ID`
  - `DIGITAL_OCEAN_OAUTH2_CLIENT_SECRET`

## Tools

| name | description | required params |
| --- | --- | --- |
| `add_ssh_key` | Add a new SSH key to your DigitalOcean account | `name`, `public_key` |
| `create_domain` | Create a new domain in DigitalOcean DNS | `name`, `ip_address` |
| `create_droplet` | Create a new DigitalOcean Droplet (virtual machine) | `name`, `region`, `image`, `size` |
| `create_snapshot` | Create a snapshot from an existing DigitalOcean Droplet | `droplet_id` |
| `list_all_droplets` | List all Droplets in your DigitalOcean account | _(none)_ |
| `turnonoff_droplet` | Turn a Droplet's power on or off | `turn_on_off`, `droplet_id` |

Every tool takes an additional `auth_type`/`auth_data` pair that the runtime fills in from the resolved OAuth credential.

## Limits & Quotas

- **Rate limit**: 5,000 requests per hour per OAuth token (returns HTTP 429 when exceeded).
- **Droplet creation**: subject to account-level Droplet limits (default 25; request increase via support).
- **Error model**: non-2xx responses and timeouts are caught and returned as `success=False` + `error` rather than raising.

## Maintainer

ModuleX core team.
