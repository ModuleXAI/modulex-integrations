"""Pydantic response models for the coinmarketcap integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CryptocurrencyMapItem",
    "CryptocurrencyMetadata",
    "CryptocurrencyQuote",
    "GetCryptocurrencyMetadataOutput",
    "IdMapOutput",
    "LatestListingsOutput",
    "LatestQuotesOutput",
    "ListingItem",
    "QuoteData",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class CryptocurrencyMetadata(_Base):
    """Metadata for a single cryptocurrency."""

    id: int | None = None
    name: str | None = None
    symbol: str | None = None
    slug: str | None = None
    description: str | None = None
    logo: str | None = None
    date_added: str | None = None
    category: str | None = None


class CryptocurrencyMapItem(_Base):
    """A cryptocurrency mapping entry."""

    id: int | None = None
    name: str | None = None
    symbol: str | None = None
    slug: str | None = None
    is_active: int | None = None
    first_historical_data: str | None = None
    last_historical_data: str | None = None


class QuoteData(_Base):
    """Quote data for a single currency conversion."""

    price: float | None = None
    volume_24h: float | None = None
    market_cap: float | None = None
    percent_change_1h: float | None = None
    percent_change_24h: float | None = None
    percent_change_7d: float | None = None
    last_updated: str | None = None


class ListingItem(_Base):
    """A cryptocurrency listing entry with market data."""

    id: int | None = None
    name: str | None = None
    symbol: str | None = None
    slug: str | None = None
    cmc_rank: int | None = None
    circulating_supply: float | None = None
    total_supply: float | None = None
    max_supply: float | None = None
    quote: dict[str, QuoteData] = Field(default_factory=dict)


class CryptocurrencyQuote(_Base):
    """Quote data for a specific cryptocurrency."""

    id: int | None = None
    name: str | None = None
    symbol: str | None = None
    slug: str | None = None
    cmc_rank: int | None = None
    quote: dict[str, QuoteData] = Field(default_factory=dict)


# --- Per-action output models ----------------------------------------------


class GetCryptocurrencyMetadataOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, CryptocurrencyMetadata] = Field(default_factory=dict)


class IdMapOutput(_Base):
    success: bool
    error: str | None = None
    data: list[CryptocurrencyMapItem] = Field(default_factory=list)


class LatestListingsOutput(_Base):
    success: bool
    error: str | None = None
    data: list[ListingItem] = Field(default_factory=list)


class LatestQuotesOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, CryptocurrencyQuote] = Field(default_factory=dict)
