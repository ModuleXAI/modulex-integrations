"""CoinMarketCap integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="coinmarketcap",
    display_name="CoinMarketCap",
    description="Cryptocurrency market data, quotes, and metadata from the CoinMarketCap API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:coinmarketcap-themed",
    app_url="https://coinmarketcap.com",
    categories=["Finance", "Cryptocurrency", "Market Data"],
    actions=[
        ActionDefinition(
            name="get_cryptocurrency_metadata",
            description="Returns all static metadata available for one or more cryptocurrencies including name, symbol, logo, description, and URLs",
            parameters={
                "ids": ParameterDef(
                    type="string",
                    description="One or more comma-separated CoinMarketCap cryptocurrency IDs. Example: 1,2,1027",
                    required=True,
                ),
                "skip_invalid": ParameterDef(
                    type="boolean",
                    description="When true, invalid lookups will be skipped allowing valid cryptocurrencies to still be returned",
                    default=False,
                ),
                "aux": ParameterDef(
                    type="string",
                    description="Comma-separated supplemental data fields to return. Valid values: urls, logo, description, tags, platform, date_added, notice, status",
                ),
            },
        ),
        ActionDefinition(
            name="id_map",
            description="Returns a mapping of all cryptocurrencies to unique CoinMarketCap IDs",
            parameters={
                "listing_status": ParameterDef(
                    type="string",
                    description="Filter by status. Valid values: active, inactive, untracked. Comma-separated for multiple.",
                ),
                "start": ParameterDef(
                    type="integer",
                    description="Offset the start (1-based index) of the paginated list of items to return",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Number of results to return. Default 100",
                    default=100,
                ),
                "sort": ParameterDef(
                    type="string",
                    description="Sort field. Valid values: cmc_rank, id",
                ),
                "symbol": ParameterDef(
                    type="string",
                    description="Comma-separated list of cryptocurrency symbols to return IDs for. If passed, other options are ignored.",
                ),
                "aux": ParameterDef(
                    type="string",
                    description="Comma-separated supplemental data fields. Valid values: platform, first_historical_data, last_historical_data, is_active, status",
                ),
            },
        ),
        ActionDefinition(
            name="latest_listings",
            description="Returns a paginated list of all active cryptocurrencies with latest market data",
            parameters={
                "start": ParameterDef(
                    type="integer",
                    description="Offset the start (1-based index) of the paginated list of items to return",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Number of results to return",
                ),
                "volume_24h_min": ParameterDef(
                    type="number",
                    description="Minimum 24 hour USD volume to filter results by",
                ),
                "convert": ParameterDef(
                    type="string",
                    description="Comma-separated list of cryptocurrency or fiat currency symbols to calculate market quotes in",
                ),
                "convert_id": ParameterDef(
                    type="string",
                    description="Comma-separated CoinMarketCap IDs to calculate market quotes in. Cannot be used with convert.",
                ),
                "sort": ParameterDef(
                    type="string",
                    description="Sort field. Valid values: market_cap, name, symbol, date_added, price, circulating_supply, total_supply, max_supply, num_market_pairs, volume_24h, percent_change_1h, percent_change_24h, percent_change_7d",
                ),
                "sort_dir": ParameterDef(
                    type="string",
                    description="Sort direction. Valid values: asc, desc",
                ),
                "cryptocurrency_type": ParameterDef(
                    type="string",
                    description="Type of cryptocurrency to include. Valid values: all, coins, tokens",
                ),
                "aux": ParameterDef(
                    type="string",
                    description="Comma-separated supplemental data fields. Valid values: num_market_pairs, cmc_rank, date_added, tags, platform, max_supply, circulating_supply, total_supply",
                ),
            },
        ),
        ActionDefinition(
            name="latest_quotes",
            description="Returns the latest market quote for one or more cryptocurrencies. At least one of id, slug, or symbol is required.",
            parameters={
                "id": ParameterDef(
                    type="string",
                    description="One or more comma-separated CoinMarketCap cryptocurrency IDs. Example: 1,2",
                ),
                "slug": ParameterDef(
                    type="string",
                    description="Comma-separated list of cryptocurrency slugs. Example: bitcoin,ethereum",
                ),
                "symbol": ParameterDef(
                    type="string",
                    description="Comma-separated cryptocurrency symbols. Example: BTC,ETH",
                ),
                "convert": ParameterDef(
                    type="string",
                    description="Comma-separated list of currency symbols to calculate quotes in",
                ),
                "convert_id": ParameterDef(
                    type="string",
                    description="Comma-separated CoinMarketCap IDs to calculate quotes in. Cannot be used with convert.",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your CoinMarketCap API key",
            setup_instructions=[
                "Go to https://coinmarketcap.com/api/ and sign up for an account",
                "Navigate to your API dashboard",
                "Copy your API key",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="COINMARKETCAP_API_KEY",
                    display_name="CoinMarketCap API Key",
                    description="Your CoinMarketCap API key from the developer dashboard",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://coinmarketcap.com/api/",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://pro-api.coinmarketcap.com/v1/cryptocurrency/map",
                method="GET",
                headers={"X-CMC_PRO_API_KEY": "{api_key}"},
                params={"limit": "1"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates the API key by fetching one cryptocurrency mapping entry",
            ),
        ),
    ],
)
