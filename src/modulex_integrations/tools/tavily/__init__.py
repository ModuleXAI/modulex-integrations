"""Tavily integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.tavily.manifest import manifest
from modulex_integrations.tools.tavily.tools import answer_search, news_search, web_search

TOOLS = (web_search, answer_search, news_search)

__all__ = ["TOOLS", "answer_search", "manifest", "news_search", "web_search"]
