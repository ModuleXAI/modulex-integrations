---
name: integrate-staged-tool
description: Hourly pipeline that ingests one producer-staged tool from integration-drafts/, audits + patches it on the consumer side, merges it into src/modulex_integrations/tools/<name>/, registers the pyproject entry-point, runs ruff/mypy/pytest gates, and signals the workflow to bump the rc version + tag + push. Use when the user runs /integrate-next-tool or when the cron workflow fires. Routes through three subagents (preselector → auditor → merger) and the audit-checklist doc.
---

# integrate-staged-tool — consumer-side orchestration playbook

This skill is the **consumer-side counterpart** to the producer's
`integration-drafts` skill. Where the producer reads Upstream components
and writes staged scaffolds, this skill reads staged scaffolds and writes
into the modulex-integrations tree — adding the consumer-environment
gates (`ruff`, `mypy`, `pytest`, real entry-point load) that the
producer's verifier marks as `DEFER`.

If this skill disagrees with `.claude/docs/integration-audit-checklist.md`,
the checklist wins. The checklist is the contract.

---

## Phase map

```
P0. Pre-flight                  (locate producer staging dir, sanity-check)
P1. Pending-release gate        (skip if release-pypi env is awaiting approval)
P2. Preselector dispatch        (pick one tool name)
P3. Pre-merge bookkeeping       (ensure pip install -e ".[dev]" succeeds; baseline tests still green)
P4. Auditor dispatch            (deep audit → patches)
P5. Auditor verdict check       (READY | NEEDS_REWORK | REFUSE)
P6. Merger dispatch             (apply patches, copy, register, run gates)
P7. Version bump                (rc(N) → rc(N+1) on staging)
P8. Commit + tag + push         (triggers release.yml → PyPI prerelease)
P9. Final summary
```

Phases P0-P1 are cheap. P2 chooses. P3-P5 audit. P6 merges. P7-P8 ship.

---

## P0 — Pre-flight

The slash command's `!` Bash block printed:

- `DRAFTS_STAGING_DIR` — where the producer's `integration-drafts/` folder
  lives. Absolute path. Validated to exist + non-empty.
- `CONSUMER_TOOLS_DIR` — `src/modulex_integrations/tools/`. Validated.
- `OVERRIDE_TOOL` — optional. If set, skip the preselector.
- `IS_CI` — `true` if running inside the GitHub Action; `false` for
  interactive.

Acknowledge with one sentence:

> "Hourly auto-integrate: scanning <N> staged tools, <M> already shipped, looking for the next merge candidate."

If `OVERRIDE_TOOL` is set:

> "Override active: skipping preselector, integrating `<name>` directly."

---

## P1 — Pending-release gate

**Skip everything if a previous run's release is still awaiting human
approval.** The release.yml workflow uses an environment-scoped Trusted
Publisher with deployment protection rules. When release.yml fires on a
new tag, it enters the `release-pypi` environment, which pauses until the
human approves in the GitHub UI. We treat that pause as the signal to
back off — no point queueing more releases.

In interactive mode (`IS_CI=false`), do this check too — the human might
be running `/integrate-next-tool` manually after a partial-day pause.

Implementation:

```bash
gh api "repos/${GITHUB_REPOSITORY:-ModuleXAI/modulex-integrations}/actions/runs?status=waiting&per_page=10" \
  --jq '[.workflow_runs[] | select(.name == "release")] | length'
```

If the count is > 0:

- Echo: "release.yml run(s) waiting for deployment approval; skipping
  this iteration."
- Exit the skill cleanly (don't dispatch preselector). Workflow returns
  success with a `skipped=true` outcome.

If 0, proceed to P2.

The workflow-level pre-step does this same check too, so this is defense
in depth.

---

## P2 — Preselector dispatch

Use `Agent` with `subagent_type: "integration-preselector"`. Pass:

- `DRAFTS_STAGING_DIR`
- `CONSUMER_TOOLS_DIR`

Wait for its Markdown report. Parse the `chosen:` line.

If `chosen=NONE`:

- Read the `NONE rationale` paragraph.
- Echo it back to the user.
- Exit cleanly. The cron will retry next hour.

If `chosen=<name>`:

- Echo the top-3 ranking table for transparency.
- Continue to P3 with `TOOL_NAME=<name>` and
  `STAGED_DIR=$DRAFTS_STAGING_DIR/<name>/`.

If `OVERRIDE_TOOL` was set (P0), skip the preselector entirely. Validate
the override name structurally (regex + folder exists in staging).

---

## P3 — Pre-merge bookkeeping

Before dispatching the auditor, ensure the consumer environment is
healthy:

1. `.venv/bin/pip install -e ".[dev]"` — must succeed (re-install in case
   of skew).
2. `.venv/bin/pytest -x -q` — quick baseline run over the *currently
   shipping* tools. If any pre-existing test fails, our gates would
   incorrectly attribute the failure to this tool. Halt with a P3 fail
   summary.

If baseline is broken, this is a `staging-branch-broken` situation. Exit
cleanly with a notice and let the human fix. **Don't merge on top of a
red baseline.**

---

## P4 — Auditor dispatch

Use `Agent` with `subagent_type: "integration-auditor"`. Pass:

- `STAGED_DIR`
- `TOOL_NAME`

Save the auditor's report to `/tmp/auditor-report-<name>.md` for the
merger to consume.

Wait for the report. The auditor returns a single Markdown block; write
it to disk via Bash (`echo ... > /tmp/...` or pipe through `tee`).

---

## P5 — Auditor verdict check

Read the auditor's `Verdict:` line in the `## Merger decision summary`
section.

- `READY` — no patches, no BLOCK. Proceed to P6 unchanged.
- `NEEDS_REWORK` — patches exist; merger will apply them. Proceed to P6.
- `REFUSE` — BLOCK items with fix=none. Exit cleanly with the BLOCK list
  as the cron summary; the human follows up on producer side (likely a
  recipe drift the producer needs to address).

---

## P6 — Merger dispatch

Use `Agent` with `subagent_type: "integration-merger"`. Pass:

- `STAGED_DIR`
- `TOOL_NAME`
- `AUDITOR_REPORT_PATH=/tmp/auditor-report-<name>.md`
- `REPO_ROOT` (this repo)

Wait for its SUCCESS or FAILURE block.

On FAILURE:

- Echo the FAILURE block back to the orchestrator's stdout.
- **Confirm revert.** Run `git status --porcelain`. If clean, exit
  cleanly with a `merger-failed` summary. If dirty, escalate as
  `revert-dirty` — the cron workflow will set the run status to
  failure but won't push anything.
- Either way: no commit, no tag, no push.

On SUCCESS:

- Echo the SUCCESS summary.
- Save the merger's PR description draft to
  `/tmp/integrate-pr-body-<name>.md` (the workflow consumes this for the
  commit message body).
- Continue to P7.

---

## P7 — Version bump

The repo uses hatch-vcs — version is derived from the latest reachable
tag. Pre-release tags live on the `staging` branch with shape
`vX.Y.Z<rc|a|b>N`.

Bump logic (run via Bash on the workflow runner):

```bash
LATEST_TAG=$(git describe --tags --abbrev=0 --match='v*' 2>/dev/null || echo "v0.1.0rc0")
# Parse the rc number
if [[ "$LATEST_TAG" =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)rc([0-9]+)$ ]]; then
    MAJ="${BASH_REMATCH[1]}"
    MIN="${BASH_REMATCH[2]}"
    PATCH="${BASH_REMATCH[3]}"
    RC="${BASH_REMATCH[4]}"
    NEW_TAG="v${MAJ}.${MIN}.${PATCH}rc$((RC + 1))"
elif [[ "$LATEST_TAG" =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    # Latest is stable; start a new rc cycle by bumping the patch
    MAJ="${BASH_REMATCH[1]}"
    MIN="${BASH_REMATCH[2]}"
    PATCH="${BASH_REMATCH[3]}"
    NEW_TAG="v${MAJ}.${MIN}.$((PATCH + 1))rc1"
else
    echo "::error::Could not parse latest tag: $LATEST_TAG"
    exit 1
fi
echo "NEW_TAG=$NEW_TAG"
```

Save `$NEW_TAG` for P8. The bump strategy is intentionally
**minor-conservative**: every cron run increments only the rc suffix.
Major / minor / patch bumps are explicitly out of scope and remain a
human decision.

---

## P8 — Commit + tag + push

1. **Commit on staging.** Files changed are exactly what the merger
   touched: the new `src/.../tools/<name>/` folder + `pyproject.toml`
   + `CHANGELOG.md`.

   Commit message:

   ```
   auto-integrate: <name>
   
   Producer-staged by integration-drafts; consumer-side audit applied N
   patches before merge.
   
   <merger's PR description draft, inline>
   
   Co-Authored-By: auto-integrate bot <bot+auto-integrate@modulex.dev>
   ```

2. **Push to staging.** `git push origin staging`.

3. **Tag** `$NEW_TAG`. `git tag $NEW_TAG`.

4. **Push tag.** `git push origin "$NEW_TAG"`.

The tag push triggers `release.yml`. That workflow:

- Verifies the tag is on staging (it is — we just pushed).
- Builds the sdist + wheel.
- Enters the `release-pypi` environment.
- **Pauses for human approval** (the protection rule).

When the human approves in the GitHub UI, the publish step runs and the
new pre-release is on PyPI. Until then, the next cron run's P1 gate
returns "waiting > 0" and skips.

---

## P9 — Final summary

In the final assistant message (≤200 words):

1. Outcome: `<name>` integrated; tag `<NEW_TAG>` pushed.
2. Auditor stats: P PASS / F FAIL / X FIX / W WARN (raw counts).
3. Merger stats: N patches applied, M skipped (risky-semantic, awaiting
   human review).
4. Gates: ruff ✓ / mypy ✓ / pytest <X passed, Y deferred>.
5. Next: release.yml is awaiting deployment approval. Approve in the
   Actions UI to publish to PyPI as `<version-without-the-v>`.

If skipped at P1:

> "Pending release approval — no work done. Next attempt in ~1 hour."

If skipped at P2:

> "No eligible candidates in staging. Next attempt in ~1 hour."

If failed at P6/P7/P8:

> "Failed during <phase> for <name>: <one-line reason>. Working tree
> clean. Next attempt in ~1 hour will try a different candidate."

---

## Failure modes this skill specifically guards against

- **Merging on a red baseline.** P3 catches this. Don't blame the new
  tool for an old breakage.
- **Releasing while a previous release is unapproved.** P1 catches this.
  No release-spam.
- **Half-merged state.** The merger's revert protocol is mandatory; this
  skill never commits half a merge.
- **Producer drift going unnoticed.** P4 → auditor's "Producer-side
  feedback" section surfaces patterns. The skill doesn't act on them, but
  they appear in the PR description for the human to track.
- **rc tag collision.** P7 reads the latest tag fresh; can't accidentally
  re-tag a previously-pushed version.
- **Skill-vs-checklist divergence.** Skill explicitly defers to checklist
  in case of disagreement. Update both in lockstep.

---

## Idempotency

If `src/modulex_integrations/tools/<name>/` already exists (rare —
previous merger partial-failed but didn't revert cleanly):

- Merger refuses (its M4 protects against this). Re-running this skill
  with the same tool produces a `merger-refused-already-exists` outcome.
- The human's fix: `rm -rf src/modulex_integrations/tools/<name>/` +
  revert pyproject.toml entry-point line, then retry.

The skill itself does not attempt cleanup of a previous mess. It detects
and reports.

---

## Concurrency

The workflow has `concurrency: { group: auto-integrate, cancel-in-progress:
false }` — only one cron run executes at a time. The skill assumes
single-writer; no internal locking needed.

If running in interactive mode while a cron is in progress, the cron's
push will succeed first (or our local push will rebase). The user is
expected to coordinate manually in that case — interactive mode is for
debugging, not parallel ops.
