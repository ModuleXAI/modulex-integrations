# NPM Registry

Read-only access to the public npm registry: package info, search,
popular packages, version history, dependency graphs, and download
statistics.

## Authentication

### API Key (optional)

The public npm registry needs no credential. Pass an API key only
when querying a private registry: it is sent as
`Authorization: Bearer <token>`.

- Env var: `NPM_API_KEY` (optional).

## Tools

| name | description | required params |
| --- | --- | --- |
| `get_package_info` | Latest-version metadata for a package | `package_name` |
| `search_packages` | Keyword search across the registry | `query` |
| `get_popular_packages` | Browse high-popularity packages | — |
| `get_package_versions` | All versions + dist-tags | `package_name` |
| `get_package_dependencies` | Dependency tree at a version | `package_name` |
| `get_package_download_stats` | Aggregated + daily download counts | `package_name` |

## Limits & Quotas

- npm's public registry has loose, unenforced limits — be reasonable.
  Two API hosts are involved: `registry.npmjs.org` (metadata) and
  `api.npmjs.org` (downloads).
- `period` must be one of `last-day`, `last-week`, `last-month`,
  `last-year` (validated client-side; otherwise `success=False`).
- Search `size` is clamped to [1, 250].

## Maintainer

ModuleX core team.
