"""Pydantic response models for the Brandfetch integration's @tool functions.

Brandfetch's tools follow the modulex *api_key* runtime convention: the
function signature takes ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair), and the modulex ``ToolExecutor``
injects it by reading the API key from the resolved credential.

Error model: the API returns proper HTTP status codes; each tool wraps
its call in try/except so non-2xx responses and timeouts surface as
``success=False`` + ``error`` rather than exceptions. Every output model
carries both shapes and keeps every data field permissive (the upstream
payload is read with ``.get()`` throughout).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "BrandColor",
    "BrandFont",
    "BrandLink",
    "BrandLogo",
    "BrandLogoFormat",
    "GetBrandOutput",
    "SearchOutput",
    "SearchResultItem",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class BrandLink(_Base):
    """A single social/website link entry."""

    name: str | None = None
    url: str | None = None


class BrandLogoFormat(_Base):
    """One downloadable format for a logo asset."""

    src: str | None = None
    format: str | None = None
    width: int | None = None
    height: int | None = None
    background: str | None = None
    size: int | None = None


class BrandLogo(_Base):
    """A logo asset with its theme and available formats."""

    type: str | None = None
    theme: str | None = None
    formats: list[BrandLogoFormat] = Field(default_factory=list)


class BrandColor(_Base):
    """A brand color with its hex value and role."""

    hex: str | None = None
    type: str | None = None
    brightness: int | None = None


class BrandFont(_Base):
    """A brand font with its name, role, and origin."""

    name: str | None = None
    type: str | None = None
    origin: str | None = None
    origin_id: str | None = None
    weights: list[int] = Field(default_factory=list)


class SearchResultItem(_Base):
    """A single brand match returned by ``search``."""

    brand_id: str | None = None
    name: str | None = None
    domain: str | None = None
    claimed: bool | None = None
    icon: str | None = None


# --- Per-action output models ----------------------------------------------


class GetBrandOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    domain: str | None = None
    claimed: bool | None = None
    description: str | None = None
    long_description: str | None = None
    links: list[BrandLink] = Field(default_factory=list)
    logos: list[BrandLogo] = Field(default_factory=list)
    colors: list[BrandColor] = Field(default_factory=list)
    fonts: list[BrandFont] = Field(default_factory=list)
    company: dict[str, Any] | None = None
    quality_score: float | None = None
    is_nsfw: bool | None = None


class SearchOutput(_Base):
    success: bool
    error: str | None = None
    results: list[SearchResultItem] = Field(default_factory=list)
    total_results: int = 0
