# modulex-integrations

Community-contributable integrations (tools) for the [ModuleX](https://github.com/ModuleXAI/modulex) runtime.

## Status

**Phase 1 — early development.** This repository is being scaffolded as part of the integration-repo split. The schema contract and packaging are in place; integrations themselves will be migrated from the modulex monorepo one at a time, starting with a POC and continuing via a one-shot migration script. See [CONTRIBUTING.md](CONTRIBUTING.md) for project layout and [CHANGELOG.md](CHANGELOG.md) for progress.

## What is this?

Each integration in this package exposes one or more LangChain `@tool` functions to the ModuleX runtime, together with credential metadata (auth schemas, env vars, test endpoints). The runtime discovers integrations via the Python `modulex.tools` entry-point group and loads them at startup.

## Installation

```bash
pip install modulex-integrations
```

With every integration's optional dependencies:

```bash
pip install "modulex-integrations[all]"
```

Or only the integrations you need (extras are populated as integrations are migrated):

```bash
pip install "modulex-integrations[github,slack]"
```

## Layout

```
src/modulex_integrations/
├── schema.py                    # IntegrationManifest pydantic contract
└── tools/<name>/
    ├── manifest.py              # IntegrationManifest instance
    ├── tools.py                 # LangChain @tool functions
    ├── outputs.py               # pydantic response models (UI/docs source)
    ├── dependencies.toml        # per-integration runtime deps
    ├── README.md                # contributor-facing docs
    └── tests/
        └── test_<name>.py
```

## Development

```bash
git clone https://github.com/ModuleXAI/modulex-integrations.git
cd modulex-integrations
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src/modulex_integrations
```

## License

MIT — see [LICENSE](LICENSE).
