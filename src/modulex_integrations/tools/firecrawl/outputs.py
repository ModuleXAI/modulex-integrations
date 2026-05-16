"""Pydantic response models for the Firecrawl integration.

Firecrawl's API returns rich, heavily-nested JSON. Legacy forwarded
the upstream body wholesale as ``result``; we mirror that on ``data``
so the contract stays open. Each action gets its own typed output so
the runtime can derive distinct JSONSchemas, even though they share
fields.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "BatchScrapeOutput",
    "CheckCrawlStatusOutput",
    "CrawlOutput",
    "ExtractOutput",
    "MapWebsiteOutput",
    "ScrapeOutput",
    "SearchOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class ScrapeOutput(_Base):
    pass


class MapWebsiteOutput(_Base):
    pass


class SearchOutput(_Base):
    pass


class CrawlOutput(_Base):
    pass


class CheckCrawlStatusOutput(_Base):
    pass


class ExtractOutput(_Base):
    pass


class BatchScrapeOutput(_Base):
    pass
