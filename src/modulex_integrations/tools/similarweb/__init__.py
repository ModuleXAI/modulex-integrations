"""Similarweb integration for the ModuleX runtime."""
from __future__ import annotations

from modulex_integrations.tools.similarweb.manifest import manifest
from modulex_integrations.tools.similarweb.tools import (
    bounce_rate,
    pages_per_visit,
    traffic_visits,
    visit_duration,
    website_overview,
)

TOOLS = (
    website_overview,
    traffic_visits,
    bounce_rate,
    pages_per_visit,
    visit_duration,
)

__all__ = [
    "TOOLS",
    "bounce_rate",
    "manifest",
    "pages_per_visit",
    "traffic_visits",
    "visit_duration",
    "website_overview",
]
