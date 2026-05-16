# scripts/

Utility scripts maintained alongside the package.

Planned scripts:

- `migrate_from_modulex.py` — one-shot conversion of legacy `py/app/integrations/tools/<name>_integration.json` files into `src/modulex_integrations/tools/<name>/` directories (manifest + outputs + tests stubs).
- `assemble_dependencies.py` — read every `tools/<name>/dependencies.toml` and regenerate `[project.optional-dependencies]` in the root `pyproject.toml`. Run by CI on every PR.

Neither script is implemented yet; placeholders only.
