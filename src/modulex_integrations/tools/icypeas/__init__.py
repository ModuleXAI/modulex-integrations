"""Icypeas integration: professional email finding and verification."""
from __future__ import annotations

from modulex_integrations.tools.icypeas.manifest import manifest
from modulex_integrations.tools.icypeas.tools import find_email, verify_email

TOOLS = (find_email, verify_email)

__all__ = ["TOOLS", "find_email", "manifest", "verify_email"]
