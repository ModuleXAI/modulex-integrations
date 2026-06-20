"""Pydantic response models for the Similarweb integration's @tool functions.

Similarweb's tools follow the ``api_key`` runtime convention: each
function signature takes ``api_key: str`` directly, which the runtime
injects from the resolved credential.

Error model: the upstream API returns proper HTTP status codes, but
every tool wraps its call in try/except so non-2xx responses and
timeouts surface as ``success=False`` + ``error`` rather than raising.
Every output model carries both shapes.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "BounceRateOutput",
    "BounceRatePoint",
    "PagesPerVisitOutput",
    "PagesPerVisitPoint",
    "TopCountryShare",
    "TrafficSources",
    "TrafficVisitsOutput",
    "VisitDurationOutput",
    "VisitDurationPoint",
    "VisitPoint",
    "WebsiteOverviewOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class TopCountryShare(_Base):
    """A single row in the website overview's top-countries breakdown."""

    country: str | None = None
    share: float | None = None


class TrafficSources(_Base):
    """Traffic source share breakdown for the website overview."""

    direct: float | None = None
    referrals: float | None = None
    search: float | None = None
    social: float | None = None
    mail: float | None = None
    paid_referrals: float | None = None


class VisitPoint(_Base):
    """A single point in the traffic-visits time series."""

    date: str | None = None
    visits: float | None = None


class BounceRatePoint(_Base):
    """A single point in the bounce-rate time series."""

    date: str | None = None
    bounce_rate: float | None = None


class PagesPerVisitPoint(_Base):
    """A single point in the pages-per-visit time series."""

    date: str | None = None
    pages_per_visit: float | None = None


class VisitDurationPoint(_Base):
    """A single point in the visit-duration time series (seconds)."""

    date: str | None = None
    duration_seconds: float | None = None


# --- Per-action output models ----------------------------------------------


class WebsiteOverviewOutput(_Base):
    success: bool
    error: str | None = None
    site_name: str | None = None
    description: str | None = None
    global_rank: int | None = None
    country_rank: int | None = None
    category_rank: int | None = None
    category: str | None = None
    monthly_visits: float | None = None
    engagement_visit_duration: float | None = None
    engagement_pages_per_visit: float | None = None
    engagement_bounce_rate: float | None = None
    top_countries: list[TopCountryShare] = Field(default_factory=list)
    traffic_sources: TrafficSources | None = None


class TrafficVisitsOutput(_Base):
    success: bool
    error: str | None = None
    domain: str | None = None
    country: str | None = None
    granularity: str | None = None
    last_updated: str | None = None
    visits: list[VisitPoint] = Field(default_factory=list)


class BounceRateOutput(_Base):
    success: bool
    error: str | None = None
    domain: str | None = None
    country: str | None = None
    granularity: str | None = None
    last_updated: str | None = None
    bounce_rate: list[BounceRatePoint] = Field(default_factory=list)


class PagesPerVisitOutput(_Base):
    success: bool
    error: str | None = None
    domain: str | None = None
    country: str | None = None
    granularity: str | None = None
    last_updated: str | None = None
    pages_per_visit: list[PagesPerVisitPoint] = Field(default_factory=list)


class VisitDurationOutput(_Base):
    success: bool
    error: str | None = None
    domain: str | None = None
    country: str | None = None
    granularity: str | None = None
    last_updated: str | None = None
    average_visit_duration: list[VisitDurationPoint] = Field(default_factory=list)
