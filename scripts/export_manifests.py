#!/usr/bin/env python3
"""Export every integration manifest to a single ``manifests.json``.

This is the **data contract** consumed by the modulex-docs site generator
(``scripts/generate-integrations.js``) to render one documentation page per
integration. It is a build/CI tool, not part of the shipped runtime package —
it lives under ``scripts/`` and imports the installed ``modulex_integrations``.

Design (why it looks the way it does):

* **Discovery is filesystem-based, not entry-point-based.** Some integrations
  exist on disk before their ``modulex.tools`` entry point is registered in
  ``pyproject.toml``; entry-point discovery would silently drop them from the
  docs. We walk ``src/modulex_integrations/tools/*/manifest.py`` instead, and
  cross-check against the entry-point group so missing registrations surface as
  warnings (the modulex runtime can't see those tools either).

* **Manifests load in isolation.** Each ``manifest.py`` only depends on
  ``modulex_integrations.schema`` (no SDK/optional deps), so we exec it via
  ``spec_from_file_location`` *without* triggering the package ``__init__`` —
  which would import ``tools.py`` and pull in per-integration optional
  dependencies (boto3, snowflake-connector, psycopg, ...) that may not be
  installed. This guarantees all integrations export even in a base venv.

* **``output_schema`` is best-effort.** Deriving it requires importing
  ``tools.py`` (to read each ``@tool``'s pydantic return annotation via
  ``typing.get_type_hints``, mirroring modulex's ``package_loader``). When that
  import fails (missing optional dep) we emit ``null`` for that integration's
  action schemas and record a warning, rather than failing the whole export.

Usage::

    .venv/bin/python scripts/export_manifests.py            # -> dist/manifests.json
    .venv/bin/python scripts/export_manifests.py --out -    # -> stdout
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"


def _repo_root() -> Path:
    """Repo root, derived from this file's location (scripts/ is a sibling of src/)."""
    return Path(__file__).resolve().parent.parent


def _tools_dir() -> Path:
    return _repo_root() / "src" / "modulex_integrations" / "tools"


def _package_version() -> str:
    try:
        from importlib.metadata import version

        return version("modulex-integrations")
    except Exception:
        return "0.0.0+unknown"


def _registered_entry_point_names() -> set[str] | None:
    """Names in pyproject's ``modulex.tools`` entry-point table (source of truth).

    Parsed from ``pyproject.toml`` directly, NOT from installed package metadata:
    an editable install's entry-point metadata goes stale the moment a new tool
    is added to ``pyproject.toml`` without a reinstall, which would wrongly flag
    freshly-added (but correctly registered) tools as missing. Returns ``None``
    if the table can't be read, signalling callers to skip the check entirely.
    """
    try:
        import tomllib

        data = tomllib.loads(
            (_repo_root() / "pyproject.toml").read_text(encoding="utf-8")
        )
        return set(data["project"]["entry-points"]["modulex.tools"].keys())
    except Exception:
        return None


def _load_manifest(manifest_path: Path, name: str) -> Any:
    """Exec a single ``manifest.py`` in isolation and return its ``manifest`` object.

    Bypasses the package ``__init__`` (and therefore ``tools.py`` and its
    optional deps) by loading the file under a synthetic module name.
    """
    spec = importlib.util.spec_from_file_location(f"_mxi_manifest_{name}", manifest_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot build import spec for {manifest_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.manifest


def _output_schema_for(tool_obj: Any) -> dict[str, Any] | None:
    """Derive an action's output JSONSchema from its ``@tool`` return annotation.

    Mirrors modulex's ``package_loader``: unwrap the ``serialize_pydantic_return``
    wrapper (``functools.wraps`` exposes ``__wrapped__``) so ``get_type_hints``
    resolves the stringified PEP 563 annotation against the original module's
    globals, then call ``model_json_schema()`` on the pydantic return type.
    """
    fn = getattr(tool_obj, "coroutine", None) or getattr(tool_obj, "func", None)
    if fn is None:
        return None
    fn = inspect.unwrap(fn)
    try:
        from typing import get_type_hints

        hints = get_type_hints(fn)
    except Exception:
        return None
    return_type = hints.get("return")
    if return_type is None or not hasattr(return_type, "model_json_schema"):
        return None
    try:
        return return_type.model_json_schema()
    except Exception:
        return None


def _parse_readme(readme_path: Path) -> dict[str, Any]:
    """Split a 5-section README into intro + ``{heading: body}`` sections.

    The unique hand-written prose (especially 'Limits & Quotas') is what keeps
    each generated docs page from being thin/duplicate content for SEO.
    """
    if not readme_path.is_file():
        return {}
    intro_lines: list[str] = []
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []

    def _flush() -> None:
        if current is not None:
            sections[current] = "\n".join(buf).strip()

    for raw in readme_path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("# "):  # h1 title — skip, intro follows
            continue
        if raw.startswith("## "):  # new level-2 section
            _flush()
            current = raw[3:].strip()
            buf = []
            continue
        if current is None:
            intro_lines.append(raw)
        else:
            buf.append(raw)
    _flush()

    return {"intro": "\n".join(intro_lines).strip(), "sections": sections}


def _export_one(
    name: str, registered: set[str] | None, warnings: list[str]
) -> dict[str, Any] | None:
    base = _tools_dir() / name
    try:
        manifest = _load_manifest(base / "manifest.py", name)
    except Exception as exc:  # malformed/partial integration — skip, don't abort
        warnings.append(f"{name}: manifest load failed ({type(exc).__name__}: {exc})")
        return None

    data: dict[str, Any] = manifest.model_dump(mode="json")
    # ``registered`` is None when pyproject couldn't be read — treat as unknown
    # (optimistic True, no warning) rather than flag every tool.
    known = registered is not None
    data["registered_entry_point"] = (not known) or name in registered
    if known and name not in registered:
        warnings.append(
            f'{name}: on disk but NOT in pyproject [project.entry-points."modulex.tools"]'
        )

    # Best-effort output schemas (requires importing tools.py + its optional deps).
    tools_by_name: dict[str, Any] = {}
    try:
        pkg = importlib.import_module(f"modulex_integrations.tools.{name}")
        tools_by_name = {t.name: t for t in getattr(pkg, "TOOLS", ())}
    except Exception as exc:
        warnings.append(
            f"{name}: tools import failed ({type(exc).__name__}); output_schema omitted"
        )

    for action in data.get("actions", []):
        tool_obj = tools_by_name.get(action["name"])
        action["output_schema"] = _output_schema_for(tool_obj) if tool_obj else None

    data["readme"] = _parse_readme(base / "README.md")
    return data


def build() -> dict[str, Any]:
    tools_dir = _tools_dir()
    if not tools_dir.is_dir():
        raise SystemExit(f"tools dir not found: {tools_dir}")

    names = sorted(
        p.name
        for p in tools_dir.iterdir()
        if p.is_dir() and (p / "manifest.py").is_file()
    )
    registered = _registered_entry_point_names()
    warnings: list[str] = []
    integrations: list[dict[str, Any]] = []

    for name in names:
        record = _export_one(name, registered, warnings)
        if record is not None:
            integrations.append(record)

    return {
        "schema_version": SCHEMA_VERSION,
        "package_version": _package_version(),
        "integration_count": len(integrations),
        "warnings": warnings,
        "integrations": integrations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default="dist/manifests.json",
        help="output path, or '-' for stdout (default: dist/manifests.json)",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indent (default: 2)")
    args = parser.parse_args(argv)

    payload = build()
    text = json.dumps(payload, indent=args.indent, ensure_ascii=False)

    if args.out == "-":
        sys.stdout.write(text + "\n")
    else:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = _repo_root() / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {out_path} ({payload['integration_count']} integrations)", file=sys.stderr)

    schema_ok = sum(
        1
        for it in payload["integrations"]
        for a in it.get("actions", [])
        if a.get("output_schema") is not None
    )
    schema_total = sum(len(it.get("actions", [])) for it in payload["integrations"])
    print(
        f"output_schema coverage: {schema_ok}/{schema_total} actions · "
        f"{len(payload['warnings'])} warning(s)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
