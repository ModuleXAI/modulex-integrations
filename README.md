# modulex-integrations

[![CI](https://github.com/ModuleXAI/modulex-integrations/actions/workflows/validate.yml/badge.svg)](https://github.com/ModuleXAI/modulex-integrations/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/modulex-integrations.svg)](https://pypi.org/project/modulex-integrations/)

Community-contributable integrations (tools) for the [ModuleX](https://github.com/ModuleXAI/modulex) runtime.

## Why this repo exists

`modulex` is a FastAPI/Python backend that, until now, bundled 45
LangChain tool integrations inline. We are extracting those 45 tools
into this standalone, publicly pip-installable package so that:

- adding a new tool is a single-repo PR, not a multi-file edit
  across the modulex monorepo,
- integration code is publicly inspectable,
- community contributions flow through the standard GitHub PR model.

LLM providers and knowledge providers stay in modulex. Only the
`tool` integrations migrate here.

## Status

**Phase 1 — early development.** The schema contract and packaging
are in place; integrations themselves will be migrated from the
modulex monorepo one at a time, starting with a `github` POC and
continuing via a scripted bulk migration. See [CHANGELOG.md](CHANGELOG.md)
for progress and [CONTRIBUTING.md](CONTRIBUTING.md) for layout rules.

## What is this?

Each integration in this package exposes one or more LangChain
`@tool` functions to the ModuleX runtime, together with credential
metadata (auth schemas, env vars, test endpoints). The runtime
discovers integrations via the Python `modulex.tools` entry-point
group and loads them at startup.

## Installation

```bash
pip install modulex-integrations
```

With every integration's optional dependencies:

```bash
pip install "modulex-integrations[all]"
```

Or only the integrations you need (extras are populated as
integrations are migrated):

```bash
pip install "modulex-integrations[github,slack]"
```

## Per-integration layout

Every integration ships in the same shape:

```
src/modulex_integrations/tools/<name>/
├── __init__.py        # re-exports manifest + TOOLS
├── manifest.py        # IntegrationManifest instance
├── tools.py           # LangChain @tool functions
├── outputs.py         # pydantic response models (UI/docs derive JSONSchema)
├── dependencies.toml  # per-integration runtime deps
├── README.md          # 5-section strict template (see CONTRIBUTING.md)
└── tests/
    └── test_<name>.py
```

The contract is enforced by pydantic types in
[`src/modulex_integrations/schema.py`](src/modulex_integrations/schema.py)
with `extra="forbid"` everywhere — a typo in a manifest fails at
import time, not at runtime.

## Development

```bash
git clone https://github.com/ModuleXAI/modulex-integrations.git
cd modulex-integrations
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src/modulex_integrations
```

## Roadmap

- **Phase 1 — bootstrap (this commit).** Schema, packaging, CI,
  community meta files, cross-repo brief workflow.
- **Phase 2 — github POC migration.** One integration end-to-end:
  manifest, tools, outputs, tests, entry point, real
  `httpx.MockTransport` coverage of at least one action.
- **Phase 3 — scripted bulk migration.** The remaining 44
  integrations migrated by a one-shot script, then reviewed
  individually.

## License

MIT — see [LICENSE](LICENSE).
