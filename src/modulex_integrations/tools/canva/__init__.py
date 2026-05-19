"""Canva integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.canva.manifest import manifest
from modulex_integrations.tools.canva.tools import (
    create_design,
    create_design_import_job,
    export_design,
    list_designs,
    upload_asset,
)

TOOLS = (
    create_design,
    create_design_import_job,
    export_design,
    list_designs,
    upload_asset,
)

__all__ = [
    "TOOLS",
    "create_design",
    "create_design_import_job",
    "export_design",
    "list_designs",
    "manifest",
    "upload_asset",
]
