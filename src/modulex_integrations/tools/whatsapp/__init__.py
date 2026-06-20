"""WhatsApp integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.whatsapp.manifest import manifest
from modulex_integrations.tools.whatsapp.tools import send_message

TOOLS = (send_message,)

__all__ = ["TOOLS", "manifest", "send_message"]
