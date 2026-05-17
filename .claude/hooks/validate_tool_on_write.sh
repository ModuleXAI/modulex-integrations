#!/usr/bin/env bash
# PostToolUse hook: re-validate an integration's manifest + import-path
# after every Write/Edit that touches its core files.
#
# Fires on writes to:
#   src/modulex_integrations/tools/<name>/manifest.py
#   src/modulex_integrations/tools/<name>/__init__.py
#   src/modulex_integrations/tools/<name>/tools.py
#   src/modulex_integrations/tools/<name>/outputs.py
#
# Two-tier validation:
#   Tier 1: py_compile (syntax). Always runs.
#   Tier 2: runpy(manifest.py) + IntegrationManifest.model_validate
#           round-trip. Requires the consumer's editable install
#           (`.venv/bin/python -c "import modulex_integrations"`).
#           Degrades to a one-line warning if the venv is unavailable.
#
# Exit codes (Claude Code hook protocol):
#   0  — success / not applicable / non-fatal-warning; Claude continues.
#   2  — blocking error: prints remediation to stderr; Claude is told to fix.
#
# Mirror of the producer's validate_manifest.sh but adapted for the
# consumer-repo paths.

set -uo pipefail

# Read the tool-input JSON payload from stdin
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

# Only fire for consumer-side tool files
case "$file_path" in
  */src/modulex_integrations/tools/*/manifest.py) ;;
  */src/modulex_integrations/tools/*/__init__.py) ;;
  */src/modulex_integrations/tools/*/tools.py) ;;
  */src/modulex_integrations/tools/*/outputs.py) ;;
  *) exit 0 ;;
esac

if [ ! -f "$file_path" ]; then
  exit 0
fi

# Tier 1 — syntax check. Always runs.
if ! python3 -m py_compile "$file_path" 2>/tmp/validate_tool.err; then
  echo "validate_tool BLOCKED: $file_path has a Python syntax error:" >&2
  cat /tmp/validate_tool.err >&2
  echo "Reference: .claude/docs/integration-audit-checklist.md" >&2
  rm -f /tmp/validate_tool.err
  exit 2
fi
rm -f /tmp/validate_tool.err

# Discover the consumer venv. The repo lives at $CLAUDE_PROJECT_DIR which
# is set by Claude Code. If we're elsewhere, climb up to find a sibling
# .venv.
REPO_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
PYTHON=""
for cand in \
  "$REPO_ROOT/.venv/bin/python" \
  "python3"; do
  if [ -x "$cand" ] || command -v "$cand" >/dev/null 2>&1; then
    if "$cand" -c "import modulex_integrations" 2>/dev/null; then
      PYTHON="$cand"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo "validate_tool: syntax OK (deep validation skipped — modulex_integrations not importable; run \`pip install -e \".[dev]\"\`)"
  exit 0
fi

# Determine the tool name from the file path
tool_dir=$(dirname "$file_path")
tool_name=$(basename "$tool_dir")

# If we just edited __init__.py, ensure the import resolves end-to-end.
# Otherwise validate just the manifest.py.
if [[ "$file_path" == *"/manifest.py" ]]; then
  "$PYTHON" - "$file_path" "$tool_name" <<'PYEOF'
import os, runpy, sys, traceback
path = sys.argv[1]
tool_name = sys.argv[2]
try:
    ns = runpy.run_path(path, run_name="__validate__")
except Exception:
    print("validate_tool BLOCKED: failed to execute manifest.py:", file=sys.stderr)
    traceback.print_exc()
    sys.exit(2)
if "manifest" not in ns:
    print("validate_tool BLOCKED: manifest.py does not export `manifest` symbol", file=sys.stderr)
    sys.exit(2)
from modulex_integrations.schema import IntegrationManifest
m = ns["manifest"]
if not isinstance(m, IntegrationManifest):
    print(f"validate_tool BLOCKED: manifest is {type(m).__name__}, not IntegrationManifest", file=sys.stderr)
    sys.exit(2)
try:
    IntegrationManifest.model_validate(m.model_dump())
except Exception as e:
    print(f"validate_tool BLOCKED: model_validate round-trip failed: {e}", file=sys.stderr)
    sys.exit(2)
if m.name != tool_name:
    print(f"validate_tool BLOCKED: manifest.name={m.name!r} != folder name={tool_name!r}", file=sys.stderr)
    sys.exit(2)
print(f"validate_tool: OK — {tool_name} ({len(m.auth_schemas)} auth schema(s), {len(m.actions)} action(s))")
PYEOF
elif [[ "$file_path" == *"/__init__.py" ]]; then
  # __init__.py changed — confirm the full from-import works
  "$PYTHON" -c "from modulex_integrations.tools.$tool_name import manifest, TOOLS" 2>/tmp/validate_init.err
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "validate_tool BLOCKED: \`from modulex_integrations.tools.$tool_name import manifest, TOOLS\` failed:" >&2
    cat /tmp/validate_init.err >&2
    echo "" >&2
    echo "Check: entry-point line in pyproject.toml; TOOLS tuple in __init__.py; manifest import." >&2
    rm -f /tmp/validate_init.err
    exit 2
  fi
  rm -f /tmp/validate_init.err
  echo "validate_tool: OK — $tool_name import resolves"
else
  # tools.py or outputs.py — syntax-only Tier 1 already passed
  # (alignment check is in a separate hook)
  echo "validate_tool: OK — $file_path syntax clean"
fi
