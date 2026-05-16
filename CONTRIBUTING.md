# Contributing to modulex-integrations

This repository expects every integration to ship with the same set of files in the same shape. Reviews are mechanical: if the structure is wrong, the PR is sent back. If the structure is right, review focuses on correctness of the API calls.

## Project layout

```
src/modulex_integrations/tools/<name>/
├── __init__.py                  # re-exports `manifest` and `TOOLS`
├── manifest.py                  # IntegrationManifest instance
├── tools.py                     # LangChain @tool functions
├── outputs.py                   # pydantic response models
├── dependencies.toml            # runtime deps (assembled into root pyproject by CI)
├── README.md                    # 5 required sections (see template below)
└── tests/
    └── test_<name>.py           # ≥1 happy-path test per @tool
```

## Required README sections

Every integration's `README.md` must contain these top-level headings, in this order:

1. `# <Display Name>` + 1–2 sentence summary
2. `## Authentication` — auth methods supported, where to get credentials, OAuth scopes if applicable
3. `## Tools` — table of `name | description | required params`
4. `## Limits & Quotas` — rate limits, known issues
5. `## Maintainer` — github handle or "ModuleX core team"

CI enforces the section list.

## Test requirements

- **HTTP tools (using `httpx`):** at least one `httpx.MockTransport` test per action's happy path.
- **SDK tools** (using a vendor SDK such as `hubspot-api-client`): at least one `unittest.mock.patch` test stubbing the SDK client per action.

## Schema contract

The full set of types is in [`src/modulex_integrations/schema.py`](src/modulex_integrations/schema.py). Use these symbols — do not invent fields:

- `IntegrationManifest` — top-level
- `ActionDefinition`, `ParameterDef`
- `OAuth2AuthSchema`, `BearerTokenAuthSchema`, `ApiKeyAuthSchema`, `ModulexKeyAuthSchema`, `CustomAuthSchema`, `InternalAuthSchema`
- `OAuthConfig`, `EnvVar`, `TestEndpoint`, `SuccessIndicators`

All models use `extra="forbid"` — typos fail at import time.

## Local workflow

```bash
pip install -e ".[dev]"
pytest                                                         # all tests
pytest src/modulex_integrations/tools/<name>/tests/            # one integration
ruff check src tests
mypy src/modulex_integrations
```

## Adding a new integration

> TODO: flesh out once the POC migration of the github tool lands. The intent is straightforward — copy an existing integration's folder, edit the manifest/tools/outputs/tests, open a PR.
