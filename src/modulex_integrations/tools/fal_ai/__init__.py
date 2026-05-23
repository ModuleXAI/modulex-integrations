"""fal.ai integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.fal_ai.manifest import manifest
from modulex_integrations.tools.fal_ai.tools import (
    add_request_to_queue,
    cancel_request,
    get_request_response,
    get_request_status,
)

TOOLS = (
    add_request_to_queue,
    cancel_request,
    get_request_response,
    get_request_status,
)

__all__ = [
    "TOOLS",
    "add_request_to_queue",
    "cancel_request",
    "get_request_response",
    "get_request_status",
    "manifest",
]
