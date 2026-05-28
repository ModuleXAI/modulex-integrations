"""Figma integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.figma.manifest import manifest
from modulex_integrations.tools.figma.tools import (
    delete_comment,
    list_comments,
    post_a_comment,
)

TOOLS = (
    list_comments,
    delete_comment,
    post_a_comment,
)

__all__ = [
    "TOOLS",
    "delete_comment",
    "list_comments",
    "manifest",
    "post_a_comment",
]
