"""Amazon Selling Partner integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="amazon_selling_partner",
    display_name="Amazon Selling Partner",
    description="Amazon Selling Partner API for managing orders, inventory, pricing, and reports on Amazon marketplaces",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:amazon-themed",
    app_url="https://sellercentral.amazon.com",
    categories=["E-Commerce", "Marketplace", "Fulfillment"],
    actions=[
        ActionDefinition(
            name="check_fba_inventory_levels",
            description="Retrieves inventory summaries from Amazon fulfillment centers to monitor stock availability",
            parameters={
                "marketplace_id": ParameterDef(
                    type="string",
                    description="The Amazon Marketplace ID (e.g. ATVPDKIKX0DER for US)",
                    required=True,
                ),
                "details": ParameterDef(
                    type="boolean",
                    description="Set to true to return inventory summaries with additional summarized inventory details and quantities",
                    default=False,
                ),
                "start_date_time": ParameterDef(
                    type="string",
                    description="A start date and time in ISO8601 format. If specified, all inventory summaries that have changed since then are returned. Must be no earlier than 18 months prior to the current date.",
                ),
                "seller_skus": ParameterDef(
                    type="array",
                    description="A list of seller SKUs for which to return inventory summaries (up to 50 SKUs). Elements are strings.",
                ),
            },
        ),
        ActionDefinition(
            name="fetch_orders_by_date_range",
            description="Retrieves a list of orders based on a specified date range, buyer email, or order ID",
            parameters={
                "marketplace_id": ParameterDef(
                    type="string",
                    description="The Amazon Marketplace ID",
                    required=True,
                ),
                "created_after": ParameterDef(
                    type="string",
                    description="Fetch orders created after this ISO date",
                    required=True,
                ),
                "created_before": ParameterDef(
                    type="string",
                    description="Fetch orders created before this ISO date",
                ),
                "buyer_email": ParameterDef(
                    type="string",
                    description="The email address of a buyer to filter orders",
                ),
                "amazon_order_id": ParameterDef(
                    type="string",
                    description="An order identifier specified by the seller. If provided, other filters like FulfillmentChannels, OrderStatuses, PaymentMethod cannot be used.",
                ),
            },
        ),
        ActionDefinition(
            name="generate_sales_inventory_reports",
            description="Requests reports on sales, inventory, and fulfillment performance",
            parameters={
                "report_types": ParameterDef(
                    type="array",
                    description="A list of report types used to filter reports. Refer to SP-API Report Type Values documentation. Elements are strings.",
                    required=True,
                ),
                "marketplace_id": ParameterDef(
                    type="string",
                    description="The Amazon Marketplace ID to filter reports",
                ),
                "processing_statuses": ParameterDef(
                    type="array",
                    description="A list of processing statuses used to filter reports. Valid values: CANCELLED, DONE, FATAL, IN_PROGRESS, IN_QUEUE. Elements are strings.",
                ),
                "created_since": ParameterDef(
                    type="string",
                    description="The earliest report creation date and time in ISO 8601 format. Default is 90 days ago.",
                ),
                "created_until": ParameterDef(
                    type="string",
                    description="The latest report creation date and time in ISO 8601 format. Default is now.",
                ),
            },
        ),
        ActionDefinition(
            name="get_order_details",
            description="Fetches detailed information about a specific order using its order ID",
            parameters={
                "marketplace_id": ParameterDef(
                    type="string",
                    description="The Amazon Marketplace ID",
                    required=True,
                ),
                "amazon_order_id": ParameterDef(
                    type="string",
                    description="The Amazon order ID to fetch details for",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_inbound_shipments",
            description="Fetches inbound shipment details to track stock movement and replenishment",
            parameters={
                "marketplace_id": ParameterDef(
                    type="string",
                    description="The Amazon Marketplace ID",
                    required=True,
                ),
                "status": ParameterDef(
                    type="array",
                    description="Filter inbound shipments by status. Valid values: WORKING, SHIPPED, RECEIVING, CANCELLED, DELETED, CLOSED, ERROR, IN_TRANSIT, DELIVERED, CHECKED_IN. Elements are strings.",
                    required=True,
                ),
                "last_updated_after": ParameterDef(
                    type="string",
                    description="A date for selecting inbound shipments that were last updated after (or at) a specified time",
                ),
                "last_updated_before": ParameterDef(
                    type="string",
                    description="A date for selecting inbound shipments that were last updated before (or at) a specified time",
                ),
            },
        ),
        ActionDefinition(
            name="list_marketplace_id_options",
            description="Retrieves available marketplace participation options for the authenticated seller",
            parameters={},
        ),
        ActionDefinition(
            name="optimize_product_pricing",
            description="Retrieves competitive pricing data to adjust product prices dynamically based on market trends",
            parameters={
                "marketplace_id": ParameterDef(
                    type="string",
                    description="The Amazon Marketplace ID",
                    required=True,
                ),
                "item_type": ParameterDef(
                    type="string",
                    description="Indicates whether ASIN values or seller SKU values are used to identify items. Valid values: Asin, Sku",
                    required=True,
                ),
                "values": ParameterDef(
                    type="array",
                    description="A list of ASINs or seller SKUs depending on item_type (up to 20 identifiers). Elements are strings.",
                    required=True,
                ),
                "customer_type": ParameterDef(
                    type="string",
                    description="Filters the offer listings based on customer type. Valid values: Consumer, Business",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="retrieve_sales_performance_reports",
            description="Fetches sales order metrics for visualization in dashboarding tools",
            parameters={
                "marketplace_id": ParameterDef(
                    type="string",
                    description="The Amazon Marketplace ID",
                    required=True,
                ),
                "interval": ParameterDef(
                    type="string",
                    description="A time interval for selecting order metrics. Two dates separated by two hyphens (first date inclusive; second exclusive) in ISO8601 format. Example: 2018-09-01T00:00:00-07:00--2018-09-04T00:00:00-07:00",
                    required=True,
                ),
                "granularity": ParameterDef(
                    type="string",
                    description="The granularity of the grouping of order metrics. Valid values: Hour, Day, Week, Month, Year, Total",
                    required=True,
                ),
                "granularity_time_zone": ParameterDef(
                    type="string",
                    description="An IANA-compatible time zone for determining the day boundary. Required when specifying a granularity value greater than Hour.",
                ),
                "buyer_type": ParameterDef(
                    type="string",
                    description="Filters results by buyer type. Valid values: All, B2B, B2C",
                ),
                "fulfillment_network": ParameterDef(
                    type="string",
                    description="Filters results by fulfillment network. Valid values: MFN (merchant fulfillment), AFN (Amazon fulfillment)",
                ),
                "first_day_of_week": ParameterDef(
                    type="string",
                    description="Specifies the day that the week starts on when granularity=Week. Valid values: Monday, Sunday. Default: Monday",
                ),
                "asin": ParameterDef(
                    type="string",
                    description="Filters results by ASIN. Cannot be specified together with sku.",
                ),
                "sku": ParameterDef(
                    type="string",
                    description="Filters results by SKU. Cannot be specified together with asin.",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Amazon Selling Partner OAuth (Login with Amazon)",
            setup_environment_variables=[
                EnvVar(
                    name="AMAZON_SP_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Amazon SP-API OAuth App Client ID from your developer application",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://developer-docs.amazon.com/sp-api/docs/registering-your-application",
                ),
                EnvVar(
                    name="AMAZON_SP_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Amazon SP-API OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://developer-docs.amazon.com/sp-api/docs/registering-your-application",
                ),
                EnvVar(
                    name="AMAZON_SP_API_BASE_URL",
                    display_name="SP-API Base URL",
                    description=(
                        "Selling Partner API regional endpoint. Use "
                        "https://sellingpartnerapi-na.amazon.com for North "
                        "America (default), "
                        "https://sellingpartnerapi-eu.amazon.com for "
                        "Europe, or "
                        "https://sellingpartnerapi-fe.amazon.com for the "
                        "Far East. Pick the endpoint that matches your "
                        "seller account's region."
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="https://sellingpartnerapi-na.amazon.com",
                    about_url="https://developer-docs.amazon.com/sp-api/docs/sp-api-endpoints",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://www.amazon.com/ap/oa",
                token_url="https://api.amazon.com/auth/o2/token",
                scopes=[],
            ),
            test_endpoint=TestEndpoint(
                url="{api_base_url}/sellers/v1/marketplaceParticipations",
                method="GET",
                headers={
                    "x-amz-access-token": "{access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["payload"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching marketplace participations on the configured regional endpoint",
            ),
        ),
    ],
)
