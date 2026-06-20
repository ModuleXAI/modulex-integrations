"""Twilio Voice integration — discovered by modulex via the
``modulex.tools`` entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.twilio_voice.manifest import manifest
from modulex_integrations.tools.twilio_voice.tools import (
    get_recording,
    list_calls,
    make_call,
)

TOOLS = (make_call, list_calls, get_recording)

__all__ = ["TOOLS", "get_recording", "list_calls", "make_call", "manifest"]
