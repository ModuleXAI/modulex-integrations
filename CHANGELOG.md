# Changelog

All notable changes to `modulex-integrations` are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial repository skeleton (src/ layout, hatchling build, pytest/ruff/mypy config).
- `IntegrationManifest` pydantic schema with discriminated-union `auth_schemas` covering oauth2, bearer_token, api_key, modulex_key, custom, internal.
- Contract tests on a github-shaped manifest.
- `CLAUDE.md` — project rules for Claude Code sessions in this repo.
- `external-briefs/` workflow scaffold (`README.md` spec + `modulex/` placeholder) for coordinating changes in sibling repos.
- Community meta files: `.github/CODEOWNERS`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/{bug_report.md,integration_request.md,config.yml}`, `SECURITY.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1).
- `.github/workflows/validate.yml` — lint + type-check + test on Python 3.12 and 3.13.
- `.editorconfig` and `.python-version` for consistent local tooling.

### Changed

- `README.md` expanded with "Why this repo exists", badges, per-integration layout, and a roadmap section.
- `.gitignore` no longer ignores `.python-version` (file is now committed); now also ignores the hatch-vcs-generated `src/modulex_integrations/_version.py`.
- `pyproject.toml`: switched to `dynamic = ["version"]` driven by `hatch-vcs`; static `version = "0.0.1"` removed. Static `__version__` in `__init__.py` replaced by `importlib.metadata`-based resolution.

### Added (release infrastructure)

- `.github/workflows/release.yml` — tag-triggered (`v*`) workflow that classifies pre-release vs stable via PEP 440, enforces branch-of-origin (stable from `main`, pre-release from `staging`), builds sdist + wheel, and publishes to PyPI via Trusted Publishing OIDC in the `release-pypi` environment.
- `RELEASING.md` — release process, PyPI Trusted Publisher setup checklist, and the modulex-side per-branch pinning policy.

### Added (Phase 3 — SDK pattern + further migrations)

- **tavily integration** — 3 LangChain `@tool` async actions:
  `web_search`, `answer_search`, `news_search`. First SDK-based
  integration: wraps `langchain_tavily.TavilySearch` via lazy import
  inside each tool. The lazy import + graceful "install with pip
  install langchain-tavily" fallback matches legacy modulex behavior.
- `tavily/dependencies.toml` declares `langchain-tavily>=0.2.0` for
  the future assemble script.
- `pyproject.toml` `dev` extras include `langchain-tavily` so tests
  can exercise the real SDK class via `unittest.mock.patch` — the
  CONTRIBUTING.md-specified pattern for SDK tools, now validated.
- Tests use `patch.dict(sys.modules, {"langchain_tavily": ...})` to
  both substitute a mock SDK class (happy path) and simulate the
  missing-SDK ImportError (graceful-degradation path).

### Added (Phase 3 — first bulk migrations)

- **slack integration** — 8 LangChain `@tool` async actions:
  `list_channels`, `post_message`, `reply_to_thread`, `add_reaction`,
  `get_channel_history`, `get_thread_replies`, `get_users`,
  `get_user_profile`. OAuth2 + Bot Token auth schemas. Slack's
  HTTP-200-with-`ok:false` error model is preserved as
  `success=False` + `error` on every output model.
- **exa integration** — 4 LangChain `@tool` async actions: `search`,
  `get_contents`, `find_similar`, `answer`. First migration to use
  the `api_key` runtime convention (signature is
  `(query, api_key, ...)` rather than `(auth_type, auth_data, ...)`)
  and to exercise the `api_key` + `modulex_key` auth schema variants.
- `pyproject.toml`: entry-point lines for `slack` and `exa`. End-to-end
  discovery now reports 3 integrations contributing 28 tools.
- 24 new tests (12 slack + 12 exa, includes failure-branch coverage
  for the `ok:false` and non-2xx + empty-key paths). Total package
  test count: **49**.

### Changed (schema)

- `IntegrationManifest.auth_schemas[*].test_endpoint.body` — new
  optional field (`dict[str, Any] | None = None`). Needed for POST-based
  credential checks (e.g. Exa's `POST /search` with a probe payload).
  Purely additive; existing manifests are unaffected.

### Added (github POC migration)

- First integration: `modulex_integrations.tools.github` — 16 LangChain `@tool` async actions ported from the legacy modulex inline implementation:
  `list_repositories`, `create_repository`, `delete_repository`, `get_repository`,
  `list_issues`, `create_issue`, `get_issue`, `update_issue`,
  `list_pull_requests`, `create_pull_request`, `get_pull_request`, `merge_pull_request`,
  `create_branch`, `get_file_content`, `create_commit`, `search_code`.
- `manifest.py` — pydantic `IntegrationManifest` replacing the legacy 1180-line JSON; OAuth2 + Personal Access Token auth schemas with credential test endpoints.
- `outputs.py` — 16 pydantic response models; the runtime derives output JSONSchema via `Model.model_json_schema()` (no `output_schema` field in the manifest).
- `tests/test_github.py` — 16 happy-path tests using `pytest-httpx`'s `httpx_mock` fixture plus three manifest sanity tests. Total package test count: 8 schema + 19 github = 27.
- `pyproject.toml`: entry-point line `github = "modulex_integrations.tools.github"` registered under `[project.entry-points."modulex.tools"]`. Validated end-to-end via `importlib.metadata.entry_points(group="modulex.tools")` — modulex's runtime discovery path works without changes.

## [0.0.1] — 2026-05-15

Project bootstrap.
