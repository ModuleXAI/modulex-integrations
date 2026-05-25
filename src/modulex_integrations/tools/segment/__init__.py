"""Segment integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.segment.manifest import manifest
from modulex_integrations.tools.segment.tools import (
    alias,
    group,
    identify,
    page,
    screen,
    track,
)

TOOLS = (
    alias,
    group,
    identify,
    page,
    screen,
    track,
)

__all__ = [
    "TOOLS",
    "alias",
    "group",
    "identify",
    "manifest",
    "page",
    "screen",
    "track",
]
