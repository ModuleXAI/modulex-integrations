# Changelog

All notable changes to `modulex-integrations` are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial repository skeleton (src/ layout, hatchling build, pytest/ruff/mypy config).
- `IntegrationManifest` pydantic schema with discriminated-union `auth_schemas` covering oauth2, bearer_token, api_key, modulex_key, custom, internal.
- Contract tests on a github-shaped manifest.

## [0.0.1] — 2026-05-15

Project bootstrap.
