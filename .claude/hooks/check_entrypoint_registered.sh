#!/usr/bin/env bash
# PostToolUse hook: when a new tool's __init__.py is written, confirm
# pyproject.toml has the matching entry-point line.
#
# Fires only on writes to:
#   src/modulex_integrations/tools/<name>/__init__.py
#
# Behavior:
#   - If `<name> = "modulex_integrations.tools.<name>"` is present under
#     [project.entry-points."modulex.tools"] → OK.
#   - If absent → emit a stderr warning with the exact line to add.
#     Non-blocking (exit 0) — the merger agent is expected to add this
#     line in its M5 phase, after the __init__.py is written. The hook
#     is a safety net for interactive sessions where a human is writing
#     the __init__.py by hand.
#
# Exit codes:
#   0  — always (this hook is advisory, never blocks).

set -uo pipefail

payload=$(cat || true)
if [ -z "$payload" ]; then
  exit 0
fi

file_path=$(printf '%s' "$payload" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print(data.get('tool_input', {}).get('file_path', ''))
" 2>/dev/null)

case "$file_path" in
  */src/modulex_integrations/tools/*/__init__.py) ;;
  *) exit 0 ;;
esac

# Tool name = parent dir of __init__.py
tool_dir=$(dirname "$file_path")
tool_name=$(basename "$tool_dir")

# Locate pyproject.toml relative to the file. Prefer the file's own repo
# root so a write into a git worktree checks THAT worktree's pyproject
# (where the merger's M5 phase adds the entry-point), then fall back to
# $CLAUDE_PROJECT_DIR. Backward-compatible for main-repo writes.
REPO_ROOT="$(cd "$tool_dir/../../../.." 2>/dev/null && pwd || true)"
[ -z "$REPO_ROOT" ] && REPO_ROOT="${CLAUDE_PROJECT_DIR:-$tool_dir}"
pyproject="$REPO_ROOT/pyproject.toml"

if [ ! -f "$pyproject" ]; then
  exit 0
fi

# Grep for the expected entry-point line. The line format is:
#   <name> = "modulex_integrations.tools.<name>"
expected_line="${tool_name} = \"modulex_integrations.tools.${tool_name}\""

if ! grep -qF "$expected_line" "$pyproject"; then
  echo "check_entrypoint_registered: WARNING — '$tool_name' is not in pyproject.toml entry-points." >&2
  echo "" >&2
  echo "Add this line under [project.entry-points.\"modulex.tools\"] in $pyproject," >&2
  echo "alphabetically:" >&2
  echo "" >&2
  echo "    $expected_line" >&2
  echo "" >&2
  echo "Then run: .venv/bin/pip install -e \".[dev]\"" >&2
  # Non-blocking: the merger agent adds this in M5 phase.
  exit 0
fi

echo "check_entrypoint_registered: OK — $tool_name registered in pyproject.toml"
