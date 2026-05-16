"""Pydantic response models for the Scrape.do integration.

Scrape.do returns one of three shapes depending on the request and
upstream response:

- JSON body (e.g. screenshot capture with ``returnJSON=true``,
  ``get_usage_stats``)
- Plain text (HTML/markdown/raw response body)
- Binary blob (base64-encoded image data when the upstream returns
  ``image/*`` content)

The output models expose ``content_type``, ``data`` (text or base64),
and ``is_binary`` to disambiguate, plus a raw ``payload`` for JSON
shapes.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "GetUsageStatsOutput",
    "ScrapeOutput",
    "ScrapeToMarkdownOutput",
    "ScrapeWithJsOutput",
    "TakeScreenshotOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None
    status_code: int | None = None


class _ScrapeBase(_Base):
    content_type: str | None = None
    data: str | None = None
    is_binary: bool = False
    # When the upstream returns JSON, surface it whole on ``payload``.
    payload: dict[str, Any] | None = None


class ScrapeOutput(_ScrapeBase):
    pass


class ScrapeWithJsOutput(_ScrapeBase):
    pass


class TakeScreenshotOutput(_ScrapeBase):
    pass


class ScrapeToMarkdownOutput(_Base):
    # markdown text; preserves the raw response for callers that need it.
    markdown: str | None = None
    raw: dict[str, Any] | None = None


class GetUsageStatsOutput(_Base):
    stats: dict[str, Any] | None = None
