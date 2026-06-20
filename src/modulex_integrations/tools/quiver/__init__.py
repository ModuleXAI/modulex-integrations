"""Quiver integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.quiver.manifest import manifest
from modulex_integrations.tools.quiver.tools import image_to_svg, list_models, text_to_svg

TOOLS = (text_to_svg, image_to_svg, list_models)

__all__ = ["TOOLS", "image_to_svg", "list_models", "manifest", "text_to_svg"]
