"""LaTeX integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.latex.manifest import manifest
from modulex_integrations.tools.latex.tools import get_package, list_fonts, search_packages

TOOLS = (search_packages, get_package, list_fonts)

__all__ = ["TOOLS", "get_package", "list_fonts", "manifest", "search_packages"]
