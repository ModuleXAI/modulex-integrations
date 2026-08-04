"""ArXiv integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.arxiv.manifest import manifest
from modulex_integrations.tools.arxiv.tools import get_author_papers, get_paper, search

TOOLS = (search, get_paper, get_author_papers)

__all__ = ["TOOLS", "get_author_papers", "get_paper", "manifest", "search"]
