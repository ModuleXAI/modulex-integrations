# Greptile

AI-powered codebase search and Q&A against the Greptile v2 REST API
(`api.greptile.com`). Query and search codebases using natural language,
get AI-generated answers about your code with cited file references, index
repositories, and check indexing status.

## Authentication

Greptile uses an API-key credential. You provide two secrets: your Greptile
API key (sent as an `Authorization: Bearer` token) and a GitHub Personal
Access Token (sent as the `X-GitHub-Token` header) so Greptile can clone and
index your repositories.

### API Key

- Sign in at <https://app.greptile.com>, open **Settings**, and create an
  API key. Required env var: `GREPTILE_API_KEY`.
- Create a GitHub Personal Access Token with `repo` read access at
  <https://github.com/settings/tokens>. Required env var:
  `GREPTILE_GITHUB_TOKEN`. The runtime injects this into the credential so
  each tool receives it as the `github_token` parameter.

## Tools

| name | description | required params |
| --- | --- | --- |
| `query` | Natural-language question answered with cited code references | `query`, `repositories` |
| `search` | Natural-language code search returning references without an answer | `query`, `repositories` |
| `index_repo` | Submit a repository to be indexed by Greptile | `remote`, `repository`, `branch` |
| `status` | Check the indexing status of a repository | `remote`, `repository`, `branch` |

Every tool takes additional `api_key` and `github_token` parameters that the
runtime fills in from the resolved credential (the modulex `api_key`
injection convention — not the `auth_type`/`auth_data` pair).

For `query` and `search`, `repositories` is a comma-separated list using the
format `github:branch:owner/repo` or bare `owner/repo` (which defaults to
`github:main`).

## Limits & Quotas

- Indexing is asynchronous: small repositories take 3–5 minutes, larger ones
  can take over an hour. Use `index_repo` to start indexing, then poll
  `status` until it reports `completed`.
- **Error model**: non-2xx responses and timeouts are caught and returned as
  `success=False` + `error` rather than raising. Plan retries on the agent
  side based on the error string.

## Maintainer

ModuleX core team.
