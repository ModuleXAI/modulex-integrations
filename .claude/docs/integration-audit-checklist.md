# Integration audit checklist — consumer side

> Single source of truth for what the `integration-auditor` subagent checks
> when given one `integration-drafts/<name>/` staged folder. Mirrors the
> structure of the producer's `99-verification-checklist.md` but specialized
> for the consumer side: closes the producer-verifier's `DEFER` set (§8 +
> §9 — entry-point load, ruff, mypy, pytest), and adds the **drift checks**
> derived from the system analysis (`integration-drafts-system-analysis.md`).

The auditor produces a structured report keyed by check ID. Each check has:

- **ID** — stable identifier (referenced by patches and tests).
- **What** — the predicate.
- **Why** — what it protects against.
- **Evidence shape** — what the auditor cites (`file:line`, grep result,
  AST query, exit code).
- **Severity** — `BLOCK` (merger must refuse), `FIX` (auto-fixable, merger
  applies a patch), `WARN` (noted in PR description, not blocking).
- **Fixability** — `mechanical` (deterministic patch), `safe-semantic`
  (rule-based code rewrite — bounded), `risky-semantic` (would require
  changing user-facing behavior; auditor proposes, merger applies *only if*
  whitelisted), `none` (only the human can fix).

---

## §0 — Pre-flight

| ID | What | Why | Evidence | Severity | Fix |
|---|---|---|---|---|---|
| 0.1 | `integration-drafts/<name>/` exists and is non-empty | The pre-selector picked a folder that doesn't exist — bail | `Bash: test -d` | BLOCK | none |
| 0.2 | Every required file is present (8 files + tests subdir) | Half-scaffolded folder is a producer bug; refuse to import a corrupt unit | `Bash: test -f` for each | BLOCK | none |
| 0.3 | `<name>` matches `^[a-z][a-z0-9_]*$` | Folder ↔ pydantic regex agreement | regex check | BLOCK | none |
| 0.4 | `<name>` not already in `src/modulex_integrations/tools/` | Don't re-integrate something we shipped | `Bash: test -d` | BLOCK | none |

---

## §1 — Manifest validity

Run via the running `.venv/bin/python`:

```python
import runpy
from modulex_integrations.schema import IntegrationManifest
ns = runpy.run_path("<path>")
m = ns["manifest"]
IntegrationManifest.model_validate(m.model_dump())   # round-trip
```

| ID | What | Why | Evidence | Severity | Fix |
|---|---|---|---|---|---|
| 1.1 | `manifest.py` runpy-loads without exception | Will fail at modulex.tools entry-point load otherwise | exception or OK | BLOCK | mechanical (replay the runpy traceback to the LLM, fix syntax) |
| 1.2 | `manifest` symbol exported | Discovery contract | `"manifest" in ns` | BLOCK | mechanical (add the export) |
| 1.3 | `manifest` is `IntegrationManifest` | Type contract | `isinstance(...)` | BLOCK | mechanical (replace constructor call) |
| 1.4 | `model_validate(model_dump())` round-trips | Latent extra-fields / schema mismatches | exception | BLOCK | mechanical (drop the rejected field; pydantic message names it) |
| 1.5 | `manifest.name == folder_name` | Producer-side hook should have caught this; double-check | string comparison | BLOCK | mechanical (rename one to match the other — prefer fixing manifest.name) |
| 1.6 | `manifest.actions` non-empty | Empty action list = useless integration | length | BLOCK | none (refuse + report) |
| 1.7 | `manifest.auth_schemas` non-empty | No auth = uncallable in the runtime | length | BLOCK | none |
| 1.8 | Every `ParameterDef.type` ∈ `{string,integer,number,boolean,array,object}` | Schema literal type | AST walk | BLOCK | mechanical (closest match) |

---

## §2 — tools.py wiring

Combine the manifest's action names (from §1) with AST inspection of `tools.py`:

| ID | What | Why | Evidence | Severity | Fix |
|---|---|---|---|---|---|
| 2.1 | No `import requests` / `from requests import …` | Project convention: only httpx | grep | BLOCK | safe-semantic (mechanical rewrite of `requests.<x>` → `httpx.AsyncClient` calls; flag for human review) |
| 2.2 | At least one `import httpx` OR an SDK import declared in `dependencies.toml` | Some integration must do *some* network | grep | WARN | none |
| 2.3 | Imports `serialize_pydantic_return` from `modulex_integrations` | The mandatory inner decorator | grep | BLOCK | mechanical (add the import) |
| 2.4 | Every `manifest.actions[i].name` has a matching `async def <name>` | The runtime looks up by name | AST | BLOCK | none (refuse — producer bug) |
| 2.5 | Every such function decorated with `@tool(args_schema=…)` (outer) | LangChain wrapping | AST | BLOCK | mechanical (add the decorator) |
| 2.6 | Every such function decorated with `@serialize_pydantic_return` (inner) | json.dumps compatibility — silent failure if missing | AST | BLOCK | mechanical (add the decorator in the right position) |
| 2.7 | Decorator order: `@tool` line OUTER (above), `@serialize_pydantic_return` INNER (below) | Reversed order → json.dumps blows up at runtime, ruff/mypy won't catch | AST line-number comparison | BLOCK | mechanical (swap) |
| 2.8 | Every such function has a return-type annotation pointing at a class in `outputs.py` | Runtime derives JSONSchema from this | AST | BLOCK | safe-semantic (find best matching XxxOutput by name) |
| 2.9 | Function signature flavor matches manifest auth_schemas | Token-style for oauth2/bearer_token/custom; key-style for api_key/modulex_key only | AST signature inspection | BLOCK | risky-semantic (rewrite signature + body) |

---

## §3 — outputs.py wiring

| ID | What | Why | Evidence | Severity | Fix |
|---|---|---|---|---|---|
| 3.1 | A `_Base` (or similar private base class) exists with `model_config = ConfigDict(extra="forbid")` | Project invariant — no `extra="allow"` | grep + AST | **FIX** | mechanical (rewrite the ConfigDict, document in PR if any field was relying on allow-extra) |
| 3.2 | Every `XxxOutput` class declared in `outputs.py` is also referenced as a return annotation in `tools.py` | Otherwise the class is dead weight or naming drift | cross-reference | WARN | mechanical (delete the orphan) |
| 3.3 | Every XxxOutput has `success: bool` as a field | Universal envelope | AST | BLOCK | mechanical (add the field) |
| 3.4 | For Pattern B/C integrations (api_key/modulex_key/custom): every XxxOutput has `error: str \| None = None` | Inline error envelope contract | AST | FIX | mechanical (add `error: str \| None = None` to every output class) |
| 3.5 | No `extra="allow"` anywhere in this file | Stronger than 3.1 — explicit ban | grep | FIX | mechanical (replace with `extra="forbid"`) |

---

## §4 — `__init__.py` exposure

| ID | What | Why | Evidence | Severity | Fix |
|---|---|---|---|---|---|
| 4.1 | `from modulex_integrations.tools.<name>.manifest import manifest` present | Discovery target | grep | BLOCK | mechanical (add the import) |
| 4.2 | Every action function imported from `.tools` | LangChain entry | AST | BLOCK | mechanical (regenerate import block) |
| 4.3 | `TOOLS` defined and is a **tuple** (not a list) | Project convention | AST | BLOCK | mechanical (replace `[]` with `()`) |
| 4.4 | Every `manifest.actions[i].name` is in TOOLS | Discovery completeness | AST | BLOCK | mechanical (regenerate TOOLS) |
| 4.5 | `__all__` exists, is alphabetized, and includes every action name + `"TOOLS"` + `"manifest"` | ruff RUF022 compliance + discoverability | AST | FIX | mechanical (regenerate __all__) |

---

## §5 — README sections

```bash
grep -nE "^# |^## " src/modulex_integrations/tools/<name>/README.md
```

| ID | What | Why | Evidence | Severity | Fix |
|---|---|---|---|---|---|
| 5.1 | H1 equals `manifest.display_name` | Doc-site rendering | comparison | FIX | mechanical (rewrite H1) |
| 5.2 | Sections in order: `## Authentication`, `## Tools`, `## Limits & Quotas`, `## Maintainer` | CI-enforced 5-section template | section count + order | FIX | mechanical (reorder; insert missing) |
| 5.3 | Zero occurrences of `upstream` (case-insensitive) | Project-naming hygiene | grep -ci | FIX | mechanical (s/upstream/upstream API/g) |
| 5.4 | `## Tools` table has one row per `manifest.actions[i]` | Doc completeness | row count vs action count | FIX | mechanical (regenerate the table from manifest) |

---

## §6 — Tests

| ID | What | Why | Evidence | Severity | Fix |
|---|---|---|---|---|---|
| 6.1 | `tests/__init__.py` exists (empty file) | pytest discovery | `test -f` | FIX | mechanical (create empty file) |
| 6.2 | `tests/test_<name>.py` exists | Module convention | `test -f` | BLOCK | none (refuse — producer bug) |
| 6.3 | `class TestManifest` exists with ≥3 methods (count + names-match + auth-types) | Sanity trio | AST | FIX | mechanical (regenerate the class) |
| 6.4 | At least one `async def test_<action>` decorated with `@pytest.mark.asyncio` per `manifest.actions[i]` | Happy-path coverage | AST | FIX | mechanical (insert a stub per missing action) |
| 6.5 | For Pattern B/C integrations: at least one failure-path test exists (empty-credential or non-2xx) | Inline error envelope is most failure-prone | AST | FIX | mechanical (insert a stub failure test) |
| 6.6 | `pytest` runs green from the consumer venv | Behavioral contract | exit code | BLOCK | none (semantic mocks need filling — flag to human) |

---

## §7 — dependencies.toml

| ID | What | Why | Evidence | Severity | Fix |
|---|---|---|---|---|---|
| 7.1 | Parses as valid TOML | Pipeline reads it | `tomllib.load` | BLOCK | mechanical (fix TOML) |
| 7.2 | Has a top-level `dependencies` list (may be empty) | Schema | key presence | BLOCK | mechanical (add the empty list) |
| 7.3 | Every entry is a string | Schema | type check | BLOCK | mechanical (coerce) |
| 7.4 | If non-empty, every dep is also represented in root pyproject `[project.optional-dependencies].dev` so dev imports resolve | Test-time import coverage | grep against pyproject | FIX | mechanical (mirror missing deps) |

---

## §8 — Drift checks (consumer-side additions, from system-analysis.md)

These are the checks the producer's verifier did NOT run, derived from the
audit findings. Each one corresponds to a finding in
`integration-drafts-system-analysis.md` §4.

| ID | What | Why | Evidence | Severity | Fix |
|---|---|---|---|---|---|
| 8.1 | No `f-string` interpolation of input-schema fields directly into GraphQL/SQL/path-template strings | H1 — Monday GraphQL injection class | AST: for every input-schema field name, grep f-strings in tools.py; flag matches | FIX | safe-semantic (rewrite to GraphQL `$variable` form when target is `_graphql(...)`; rewrite to `params={...}` when target is `httpx.get/post`) |
| 8.2 | No `extra="allow"` in any outputs.py BaseModel (subsumes 3.5; this is the dedicated drift check) | H2 — google_calendar regression | grep | FIX | mechanical (replace; lift any field with a real "permissive" intent into an explicit `field: dict[str, Any] \| None = None`) |
| 8.3 | Every `while cursor:` / `while next_page:` / `while page_token:` loop has a hard cap (`for _ in range(N)` wrap, or explicit `pages_seen += 1; if pages_seen > N: break`) | M1 — unbounded pagination | AST walk | FIX | safe-semantic (wrap loop body in a `for _ in range(max_pages)` with `max_pages` from action params, default 50) |
| 8.4 | For Pattern B/C: every `@tool` body starts with a credential-validity short-circuit (e.g. `if not api_key or not api_key.strip(): return …Output(success=False, error=…)`) | Empty credentials should not hit the wire | AST: first statement in body | FIX | mechanical (insert the guard) |
| 8.5 | No synthetic `@tool` that *doesn't* read from `auth_data` and *doesn't* use `httpx` (with the integration's auth_type being oauth2/bearer_token) | M2 — google_calendar's `get_date_time` | AST: function-body inspection | WARN | none (flag in PR description — human decides keep/drop/relocate) |
| 8.6 | README references at most ONE auth shape (no leftover dual-auth boilerplate when the manifest is single-auth) | Sometimes the producer emits README with both OAuth and api_key sections | grep H3 count under `## Authentication` | FIX | mechanical (drop the extra section) |
| 8.7 | `populate_by_name=True` only present when ≥1 outputs.py field declares `Field(alias=…)` | L1 — purposeful, not accidental | AST cross-check | WARN | mechanical (remove if unused) |
| 8.8 | tests/test_<name>.py uses `_args(**extra)` helper, not direct dict-literal-spread, on `.ainvoke(...)` calls | Bypasses mypy TypedDict-spread issue | grep | FIX | mechanical (add helper + replace call sites) |
| 8.9 | `manifest.logo` equals exactly `"modulex:<name>-themed"` where `<name>` is the integration folder/manifest name | Project-wide logo convention — every integration must use the modulex-themed Iconify identifier so the docs site and UI render a consistent themed icon set. The producer emits arbitrary logo values (CDN URLs, `logos:vendor-icon`, etc.) — we normalize on the consumer side. | grep manifest.py for `logo=` line; compare against expected string | FIX | mechanical (rewrite the `logo=...` line to `logo="modulex:<name>-themed"`) |
| 8.10 | **No code path between `response.json()` and `return` may raise** — both halves: every parse routed through an `_as_dict()`-style guard, AND every scalar coerced (`_as_str`/`_as_bool`/`_as_int`) before model construction | Two distinct escapes. (a) Shape: `data = response.json()` is the last statement in `try:` while its consumers sit after the `except` clauses, so a bare-array/string/null body raises `AttributeError`. (b) Type: the `success=True` model construction ALSO sits after the `except` clauses, so a well-shaped body with a wrong-typed field raises `pydantic.ValidationError` — even when every `.json()` is guarded. Mocked tests cannot catch either: fixtures are always well-shaped AND well-typed. Note that a per-field `typeof x === 'string'` check in the reference source is load-bearing under pydantic; dropping it is a silent regression. | **Probe both:** drive an action through a transport returning `[]`, then through one returning a well-shaped body with a numeric id (`{"id": 12345}`) | FIX | safe-semantic (route parses through `_as_dict(...)` and scalars through the coercer set, inside the `_parse_<entity>()` helpers; leave deliberately polymorphic actions with their explicit `isinstance` branch) |
| 8.11 | No action parameter reaches the request **netloc** without a closed-map lookup or an anchored regex, plus `.strip().lower()` | A param interpolated into the host (`region`, `subdomain`, `workspace`, `datacenter`, `shop`) is an LLM-facing SSRF vector: `region='us-east-1@attacker.example'` sends the signed `Authorization` header and the request body to an attacker-chosen host. Path-label `quote(x, safe="")` does NOT cover this. A mixed-case value also yields a signed `host:` that disagrees with the sent `Host:` — a guaranteed 403. Prefer a closed map whenever a secret is sent to that host. | grep for f-strings building a host; capture the outgoing request with hostile values | BLOCK | safe-semantic (validate at the single request chokepoint, returning the normal error envelope) |
| 8.12 | A hand-rolled request signer ships a differential test against the reference implementation | Asserting the `Authorization` header's prefix or shape passes with a wrong signature, and every mocked test stays green while every real call 403s. | check tests for an `importorskip`-guarded byte-for-byte comparison covering query/unicode/empty-body/encoded-path cases; confirm it fails under a mutated signer | FIX | mechanical (add the differential test) |

---

## §9 — Consumer-environment gates (the producer's DEFER set)

Cannot run on the producer side; mandatory here.

| ID | What | Why | Evidence | Severity | Fix |
|---|---|---|---|---|---|
| 9.1 | Entry-point line in pyproject.toml under `[project.entry-points."modulex.tools"]` exists for `<name>` and points to `modulex_integrations.tools.<name>` | Without this the runtime doesn't see the integration | grep | BLOCK | mechanical (Edit pyproject.toml, alphabetically) |
| 9.2 | `pip install -e ".[dev]"` succeeds | Editable install with new entry-point | exit code | BLOCK | none (read pip output, retry; if still failing, escalate) |
| 9.3 | `python -c "from modulex_integrations.tools.<name> import manifest, TOOLS"` succeeds | The same load the runtime does | exit code | BLOCK | none (read the import error, route to §1-§4) |
| 9.4 | `ruff check src/modulex_integrations/tools/<name>` exits 0 | Project lint baseline | exit code | FIX | mechanical (run `ruff check --fix`; reread; if still issues, route to specific rule's fix) |
| 9.5 | `mypy --strict src/modulex_integrations/tools/<name>` exits 0 | Project type baseline | exit code | FIX | safe-semantic (add missing annotations; widen too-narrow params to `dict[str, Any]` where appropriate) |
| 9.6 | `pytest src/modulex_integrations/tools/<name>/tests/ -v` exits 0 | Behavioral baseline | exit code | BLOCK | none (test mocks may be stubs — flag to human, surface in PR description) |

---

## Severity policy

When the auditor compiles its report, the merger's decision tree is:

```
1. Any BLOCK with fix=none           →  REFUSE. Workflow exits, no commit.
2. Any BLOCK with fix=mechanical     →  Apply patch in staging copy, then re-run §1-§9.
3. Any FIX                           →  Apply patch in staging copy, no re-run needed.
4. Any WARN                          →  Note in PR description, proceed.
```

The merger keeps a patch log (`/tmp/auto-integrate-patches-<name>.diff`). On
final commit, this log is appended to the PR / commit body so the human
reviewer sees exactly what the bot rewrote vs. what the producer staged.

---

## What the auditor MUST NOT do

- **No aesthetic rewrites.** If the integration is structurally sound but
  has odd-but-legal style choices (e.g., one-line lambdas), let them through.
- **No semantic test mocks.** Filling in mock response bodies with
  hallucinated upstream payloads is forbidden. Tests that are stubs after
  the bot's pass remain stubs — the human fills them.
- **No silent fixes.** Every applied patch must appear in the patch log.
- **No double dispatch.** If the auditor decides a fix needs a verifier
  re-run, it dispatches itself once. After 2 self-iterations with FIX
  items remaining, escalate as a FAILED result.

---

## What the auditor SHOULD do

- **Cite line numbers everywhere** — same standard as the producer's verifier.
- **Treat the producer's NOTES.md as context, not as truth** — the bot can
  be wrong; cross-check ambiguity resolutions against what's actually in
  the code.
- **Preserve hand-edits.** If `src/modulex_integrations/tools/<name>/`
  already exists from a previous merger run, prefer `Edit` over `Write` and
  surface diffs.
- **Surface unfixable findings clearly.** Things the auditor can't fix
  (e.g., the upstream API's auth method changed, requiring a recipe update
  in the producer repo) belong in a separate "Producer-side feedback"
  section of the PR description.
