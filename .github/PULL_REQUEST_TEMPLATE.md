<!--
Thanks for contributing to modulex-integrations.

Keep PRs focused: one integration per PR, or one infrastructure
change per PR. Bundled changes will be sent back.
-->

## Summary

<!-- 1–3 sentences: what does this PR change, and why. -->

## Linked issue

<!-- e.g. "Closes #42", or "n/a" for trivial repo-meta PRs. -->

## Type of change

- [ ] New integration
- [ ] Bug fix in an existing integration
- [ ] Schema / contract change (requires core review)
- [ ] CI / tooling / docs
- [ ] Other (describe below)

## Contributor checklist

- [ ] One integration per PR (no bundled migrations).
- [ ] Manifest constructed from `modulex_integrations.schema` types
      — no JSON file, no invented fields.
- [ ] `pytest` is green locally (`.venv/bin/pytest`).
- [ ] `ruff check src tests` is clean.
- [ ] `mypy src/modulex_integrations` is clean.
- [ ] Integration README has all 5 required sections (Display Name +
      summary, Authentication, Tools, Limits & Quotas, Maintainer).
- [ ] Tests use `httpx.MockTransport` (HTTP) or
      `unittest.mock.patch` (SDK), with at least one happy-path test
      per `@tool` action.
- [ ] `dependencies.toml` lists every new runtime dep with a pinned
      lower bound.
- [ ] `pyproject.toml` `[project.entry-points."modulex.tools"]` has
      a line for this integration (new integrations only).
- [ ] `CHANGELOG.md` updated under `## [Unreleased]`.

## Notes for reviewers

<!--
Anything reviewers should focus on: an unusual API quirk, a rate
limit that affects testing, a credential method that needed a custom
test endpoint, etc.
-->
