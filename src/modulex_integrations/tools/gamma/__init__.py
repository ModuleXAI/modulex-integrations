"""Gamma integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.gamma.manifest import manifest
from modulex_integrations.tools.gamma.tools import (
    check_status,
    generate,
    generate_from_template,
    list_folders,
    list_themes,
)

TOOLS = (generate, generate_from_template, check_status, list_themes, list_folders)

__all__ = [
    "TOOLS",
    "check_status",
    "generate",
    "generate_from_template",
    "list_folders",
    "list_themes",
    "manifest",
]
