---
description: Run the integration-auditor on ONE integration-drafts staged folder. Returns the full audit report (P/F/FIX/WARN per check + patches). Read-only — does not copy, register, or run gates. Use for debugging or pre-merge inspection.
argument-hint: <tool-name>   e.g. okta, monday, google_calendar
allowed-tools: Read, Glob, Grep, Bash, Agent
---

## Pre-flight

!set -e
!TOOL_NAME="$ARGUMENTS"
!if [ -z "$TOOL_NAME" ]; then
!  echo "ERROR: tool name required. Usage: /audit-staged-tool <name>"
!  exit 1
!fi
!if ! echo "$TOOL_NAME" | grep -qE '^[a-z][a-z0-9_]*$'; then
!  echo "ERROR: '$TOOL_NAME' does not match pydantic regex ^[a-z][a-z0-9_]*$"
!  exit 1
!fi
!if [ -n "${DRAFTS_STAGING_DIR:-}" ]; then
!  STAGING_DIR="$DRAFTS_STAGING_DIR"
!else
!  echo "ERROR: producer staging dir not found."
!  exit 1
!fi
!STAGED_DIR="$STAGING_DIR/$TOOL_NAME"
!if [ ! -d "$STAGED_DIR" ]; then
!  echo "ERROR: '$TOOL_NAME' not found in $STAGING_DIR/. Available:"
!  ls "$STAGING_DIR" 2>/dev/null | head -20
!  exit 1
!fi
!REQUIRED=(__init__.py manifest.py tools.py outputs.py dependencies.toml README.md tests/__init__.py "tests/test_${TOOL_NAME}.py" *_NOTES.md)
!MISSING=""
!for f in "${REQUIRED[@]}"; do
!  if [ ! -f "$STAGED_DIR/$f" ]; then MISSING="$MISSING $f"; fi
!done
!echo "=========================================="
!echo "AUDIT PRE-FLIGHT"
!echo "STAGED_DIR:    $STAGED_DIR"
!echo "TOOL_NAME:     $TOOL_NAME"
!if [ -n "$MISSING" ]; then
!  echo "MISSING FILES:$MISSING"
!  echo "(auditor will report these as §0 FAIL with fix=none)"
!fi
!echo "=========================================="

---

## Main task

Dispatch the `integration-auditor` subagent on `$STAGED_DIR`. Use the
`Agent` tool with `subagent_type: "integration-auditor"`. Pass:

- `STAGED_DIR` (path above)
- `TOOL_NAME` (argument above)

Tell the auditor to read
`.claude/docs/integration-audit-checklist.md` and run every check.

After it returns, print its full report verbatim to the user (so the
human can see every PASS / FAIL / FIX / WARN with cited evidence).

Do **not** apply any patches. Do **not** copy files. Do **not** run
gates. This command is read-only — it ends after printing the auditor's
report.

If the human wants to apply the patches, they should run
`/integrate-next-tool --override <name>`.
