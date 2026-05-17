---
description: Run the consumer-side auto-integrate pipeline once — picks one staged tool from integration-drafts/, audits it, applies patches, lands it in src/modulex_integrations/tools/, and signals the workflow to bump the rc tag.
argument-hint: [--override <name>]   optional override; skips the preselector
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

## Pre-flight (runs before the main prompt is evaluated)

The argument is `$ARGUMENTS`. Optional override: `--override <name>`.
Pre-flight validates the producer staging dir, the consumer dir, the
override (if any), and prints what the orchestrator will see.

!set -e
!REPO_ROOT="$(git rev-parse --show-toplevel)"
!cd "$REPO_ROOT"
!# Locate the producer's staging dir. Two known locations; CI overrides via env var.
!if [ -n "${DRAFTS_STAGING_DIR:-}" ]; then
!  STAGING_DIR="$DRAFTS_STAGING_DIR"
!elif [ -d "/tmp/integration-drafts/integration-drafts" ]; then
!  STAGING_DIR="/tmp/integration-drafts/integration-drafts"
!else
!  echo "ERROR: producer staging dir not found. Set DRAFTS_STAGING_DIR or clone the producer repo to /tmp/integration-drafts/."
!  exit 1
!fi
!CONSUMER_TOOLS_DIR="$REPO_ROOT/src/modulex_integrations/tools"
!if [ ! -d "$CONSUMER_TOOLS_DIR" ]; then
!  echo "ERROR: consumer tools dir not found at $CONSUMER_TOOLS_DIR"
!  exit 1
!fi
!# Parse --override (optional)
!OVERRIDE_TOOL=""
!if echo " $ARGUMENTS " | grep -qE '\-\-override\s+[a-z][a-z0-9_]*'; then
!  OVERRIDE_TOOL=$(echo " $ARGUMENTS " | sed -nE 's/.*--override\s+([a-z][a-z0-9_]*).*/\1/p')
!  if [ ! -d "$STAGING_DIR/$OVERRIDE_TOOL" ]; then
!    echo "ERROR: override tool '$OVERRIDE_TOOL' not found in staging dir $STAGING_DIR/"
!    exit 1
!  fi
!fi
!IS_CI="${GITHUB_ACTIONS:-false}"
!STAGED_COUNT=$(find "$STAGING_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
!SHIPPED_COUNT=$(find "$CONSUMER_TOOLS_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | grep -v __pycache__ | wc -l | tr -d ' ')
!echo "=========================================="
!echo "AUTO-INTEGRATE PRE-FLIGHT"
!echo "REPO_ROOT:           $REPO_ROOT"
!echo "DRAFTS_STAGING_DIR:  $STAGING_DIR ($STAGED_COUNT staged tools)"
!echo "CONSUMER_TOOLS_DIR:  $CONSUMER_TOOLS_DIR ($SHIPPED_COUNT shipped)"
!echo "OVERRIDE_TOOL:       ${OVERRIDE_TOOL:-<none — preselector will choose>}"
!echo "IS_CI:               $IS_CI"
!echo "=========================================="

---

## Main task

You are about to execute the consumer-side auto-integrate pipeline. **Follow
the `integrate-staged-tool` skill exactly** — phase order, subagent
dispatches, and gating checks are deliberate.

### Mandatory first actions

1. **Acknowledge the pre-flight output** in one sentence (staging count,
   shipped count, override status).
2. **Load the skill** by reading
   `.claude/skills/integrate-staged-tool/SKILL.md`. The skill is the
   playbook; this prompt is the entry point.
3. **Walk the skill phase by phase.** P1 (pending-release gate) is the
   single most important gate — running it correctly is the whole reason
   this command exists.

### Environment notes

- `STAGING_DIR` and `CONSUMER_TOOLS_DIR` are computed by the pre-flight
  above; reference them by name in your bash blocks.
- `OVERRIDE_TOOL` may be empty; if empty, dispatch the preselector.
- `IS_CI` decides whether the workflow handles commit/push (true) or
  this slash command does (false — interactive mode means a human will
  review before pushing).

### What you may NOT do

- **Do not push without P1 passing.** A pending release in `waiting`
  state means the human hasn't approved the last one yet; skip silently.
- **Do not commit if any merger gate failed.** The merger's revert
  protocol is mandatory; even one ruff/mypy/pytest failure must mean
  the working tree is clean by the time you exit.
- **Do not fill in test mock data.** Honest stubs with `# TODO` markers
  are intentional; the human fills them.

### Inputs the skill will need

- `STAGED_DIR` — the staging dir from pre-flight.
- `CONSUMER_TOOLS_DIR` — the consumer tools dir from pre-flight.
- `OVERRIDE_TOOL` — if set, skip P2.
- `IS_CI` — affects P8 (the workflow's job vs. yours).

Begin.
