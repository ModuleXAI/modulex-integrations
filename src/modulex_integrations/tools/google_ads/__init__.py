"""Google Ads integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_ads.manifest import manifest
from modulex_integrations.tools.google_ads.tools import (
    add_contact_to_list_by_email,
    create_ad_group_report,
    create_ad_report,
    create_campaign_report,
    create_customer_list,
    create_customer_report,
    create_report,
    generate_keyword_ideas,
    list_account_id_options,
    send_offline_conversion,
)

TOOLS = (
    add_contact_to_list_by_email,
    create_ad_group_report,
    create_ad_report,
    create_campaign_report,
    create_customer_list,
    create_customer_report,
    create_report,
    generate_keyword_ideas,
    list_account_id_options,
    send_offline_conversion,
)

__all__ = [
    "TOOLS",
    "add_contact_to_list_by_email",
    "create_ad_group_report",
    "create_ad_report",
    "create_campaign_report",
    "create_customer_list",
    "create_customer_report",
    "create_report",
    "generate_keyword_ideas",
    "list_account_id_options",
    "manifest",
    "send_offline_conversion",
]
