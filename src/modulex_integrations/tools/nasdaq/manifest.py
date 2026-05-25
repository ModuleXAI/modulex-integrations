"""Nasdaq Data Link integration manifest."""
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


def _symbol_or_figi_params() -> dict[str, ParameterDef]:
    return {
        "symbol": ParameterDef(
            type="string", description="Stock ticker symbol (e.g. 'AAPL', 'MSFT')"
        ),
        "figi": ParameterDef(
            type="string",
            description="Bloomberg FIGI identifier (e.g. 'BBG000BPH459')",
        ),
    }


def _periodic_query_params() -> dict[str, ParameterDef]:
    return {
        **_symbol_or_figi_params(),
        "calendardate": ParameterDef(
            type="string", description="Calendar date in YYYY-MM-DD format"
        ),
        "dimension": ParameterDef(
            type="string",
            description=(
                "Dimensional view: MRQ (Quarterly), MRY (Annual), or MRT "
                "(Trailing-twelve-months)"
            ),
        ),
    }


manifest = IntegrationManifest(
    name="nasdaq",
    display_name="Nasdaq Data Link",
    description=(
        "Access comprehensive financial data from Nasdaq Data Link E360 "
        "platform including balance sheets, cash flows, fundamentals, "
        "company statistics, and reference data for publicly traded "
        "companies."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:nasdaq",
    app_url="https://data.nasdaq.com",
    categories=["finance", "data", "research", "analytics"],
    actions=[
        ActionDefinition(
            name="get_balance_sheet",
            description=(
                "Fetch balance sheet data including assets, liabilities, "
                "equity, cash position, and debt levels"
            ),
            parameters=_periodic_query_params(),
        ),
        ActionDefinition(
            name="get_cash_flow",
            description=(
                "Fetch cash flow statement data including operating, "
                "investing, and financing activities"
            ),
            parameters=_periodic_query_params(),
        ),
        ActionDefinition(
            name="get_company_stats",
            description=(
                "Fetch company statistics including market cap, 52-week "
                "highs/lows, P/E ratios, and dividend information"
            ),
            parameters=_symbol_or_figi_params(),
        ),
        ActionDefinition(
            name="get_fundamental_details",
            description=(
                "Fetch detailed fundamental data including revenue, "
                "profitability, margins, and valuation ratios"
            ),
            parameters=_periodic_query_params(),
        ),
        ActionDefinition(
            name="get_fundamental_summary",
            description=(
                "Fetch fundamental summary with key financial ratios "
                "including P/E, ROA, ROE, and debt-to-equity"
            ),
            parameters=_periodic_query_params(),
        ),
        ActionDefinition(
            name="get_reference_data",
            description=(
                "Fetch company reference data including exchange, sector, "
                "industry, and SEC filings URL"
            ),
            parameters=_symbol_or_figi_params(),
        ),
        ActionDefinition(
            name="list_available_fields",
            description=(
                "List available fields and their descriptions for a "
                "specific data table"
            ),
            parameters={
                "table_type": ParameterDef(
                    type="string",
                    description=(
                        "Table type to list fields for: 'balance_sheet', "
                        "'cash_flow', 'company_stats', 'fundamental_details', "
                        "'fundamental_summary', 'reference_data'"
                    ),
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Nasdaq Data Link API key",
            setup_environment_variables=[
                EnvVar(
                    name="NASDAQ_API_KEY",
                    display_name="Nasdaq Data Link API Key",
                    description="Your Nasdaq Data Link API key for authentication",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxx",
                    about_url="https://data.nasdaq.com/sign-up",
                ),
            ],
            test_endpoint=TestEndpoint(
                # The /datatables/NDAQ/RD endpoint requires a premium
                # subscription and returns 403 on free-tier keys. We
                # use /databases which is free for all valid API keys
                # and only lists available databases — minimal data
                # transfer, no premium scope needed.
                url="https://data.nasdaq.com/api/v3/databases.json?api_key={api_key}&per_page=1",
                method="GET",
                headers={"Accept": "application/json"},
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["databases"]
                ),
                cost_level="free",
                description="Validates API key via the free /databases list endpoint",
            ),
        ),
    ],
)
