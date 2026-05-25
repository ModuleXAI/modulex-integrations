"""Amazon Selling Partner integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.amazon_selling_partner.manifest import manifest
from modulex_integrations.tools.amazon_selling_partner.tools import (
    check_fba_inventory_levels,
    fetch_orders_by_date_range,
    generate_sales_inventory_reports,
    get_order_details,
    list_inbound_shipments,
    list_marketplace_id_options,
    optimize_product_pricing,
    retrieve_sales_performance_reports,
)

TOOLS = (
    check_fba_inventory_levels,
    fetch_orders_by_date_range,
    generate_sales_inventory_reports,
    get_order_details,
    list_inbound_shipments,
    list_marketplace_id_options,
    optimize_product_pricing,
    retrieve_sales_performance_reports,
)

__all__ = [
    "TOOLS",
    "check_fba_inventory_levels",
    "fetch_orders_by_date_range",
    "generate_sales_inventory_reports",
    "get_order_details",
    "list_inbound_shipments",
    "list_marketplace_id_options",
    "manifest",
    "optimize_product_pricing",
    "retrieve_sales_performance_reports",
]
