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
- `.gitignore` no longer ignores `.python-version` (file is now committed).

## [0.0.1] — 2026-05-15

Project bootstrap.
