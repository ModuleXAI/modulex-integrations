"""Instantly integration manifest.

Instantly V2 cold-email outreach API — manage leads, lead lists,
campaigns, and Unibox emails. Key-based (``api_key``) auth: the runtime
injects the API key, which each tool sends as
``Authorization: Bearer <api_key>``.
"""
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
    name="instantly",
    display_name="Instantly",
    description=(
        "Integrate the Instantly V2 cold-email outreach API. Create and list "
        "leads, manage lead interest status, delete leads in bulk, list and "
        "create campaigns, reply to emails, and manage lead lists."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:instantly",
    app_url="https://instantly.ai",
    categories=["Marketing & Advertising", "email", "sales-engagement"],
    actions=[
        ActionDefinition(
            name="list_leads",
            description=(
                "Retrieve leads with search, campaign, list, and pagination filters."
            ),
            parameters={
                "search": ParameterDef(
                    type="string",
                    description="Search by first name, last name, or email",
                ),
                "filter": ParameterDef(
                    type="string",
                    description=(
                        "Lead filter value, such as FILTER_VAL_CONTACTED or FILTER_VAL_ACTIVE"
                    ),
                ),
                "campaign": ParameterDef(
                    type="string", description="Campaign ID to filter leads"
                ),
                "list_id": ParameterDef(
                    type="string", description="Lead list ID to filter leads"
                ),
                "in_campaign": ParameterDef(
                    type="boolean", description="Whether the lead is in a campaign"
                ),
                "in_list": ParameterDef(
                    type="boolean", description="Whether the lead is in a list"
                ),
                "ids": ParameterDef(type="array", description="Lead IDs to include"),
                "excluded_ids": ParameterDef(type="array", description="Lead IDs to exclude"),
                "contacts": ParameterDef(
                    type="array", description="Lead email addresses to include"
                ),
                "organization_user_ids": ParameterDef(
                    type="array", description="Organization user IDs to filter leads"
                ),
                "smart_view_id": ParameterDef(
                    type="string", description="Smart view ID to filter leads"
                ),
                "is_website_visitor": ParameterDef(
                    type="boolean", description="Whether the lead is a website visitor"
                ),
                "distinct_contacts": ParameterDef(
                    type="boolean", description="Whether to return distinct contacts"
                ),
                "enrichment_status": ParameterDef(
                    type="integer", description="Enrichment status filter"
                ),
                "esg_code": ParameterDef(
                    type="string", description="Email security gateway code filter"
                ),
                "limit": ParameterDef(
                    type="integer", description="Number of leads to return, from 1 to 100"
                ),
                "starting_after": ParameterDef(
                    type="string",
                    description="Forward pagination cursor from next_starting_after",
                ),
            },
        ),
        ActionDefinition(
            name="get_lead",
            description="Retrieve a lead by ID.",
            parameters={
                "lead_id": ParameterDef(
                    type="string", description="Lead ID", required=True
                ),
            },
        ),
        ActionDefinition(
            name="create_lead",
            description="Create a lead in a campaign or lead list.",
            parameters={
                "campaign": ParameterDef(
                    type="string", description="Campaign ID associated with the lead"
                ),
                "list_id": ParameterDef(
                    type="string", description="Lead list ID associated with the lead"
                ),
                "email": ParameterDef(
                    type="string",
                    description="Lead email address. Required when adding to a campaign.",
                ),
                "first_name": ParameterDef(type="string", description="Lead first name"),
                "last_name": ParameterDef(type="string", description="Lead last name"),
                "company_name": ParameterDef(type="string", description="Lead company name"),
                "job_title": ParameterDef(type="string", description="Lead job title"),
                "phone": ParameterDef(type="string", description="Lead phone number"),
                "website": ParameterDef(type="string", description="Lead website"),
                "personalization": ParameterDef(
                    type="string", description="Lead personalization text"
                ),
                "lt_interest_status": ParameterDef(
                    type="integer", description="Lead interest status value"
                ),
                "pl_value_lead": ParameterDef(
                    type="string", description="Potential value of the lead"
                ),
                "assigned_to": ParameterDef(
                    type="string", description="Organization user ID assigned to the lead"
                ),
                "skip_if_in_workspace": ParameterDef(
                    type="boolean",
                    description="Skip if the lead already exists in the workspace",
                ),
                "skip_if_in_campaign": ParameterDef(
                    type="boolean",
                    description="Skip if the lead already exists in the campaign",
                ),
                "skip_if_in_list": ParameterDef(
                    type="boolean", description="Skip if the lead already exists in the list"
                ),
                "blocklist_id": ParameterDef(
                    type="string", description="Blocklist ID to check for the lead"
                ),
                "verify_leads_for_lead_finder": ParameterDef(
                    type="boolean",
                    description="Whether to verify leads imported from Lead Finder",
                ),
                "verify_leads_on_import": ParameterDef(
                    type="boolean", description="Whether to verify leads on import"
                ),
                "custom_variables": ParameterDef(
                    type="object",
                    description=(
                        "Custom variable object with string, number, boolean, or null values"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="delete_leads",
            description="Delete leads in bulk from a campaign or lead list.",
            parameters={
                "campaign_id": ParameterDef(
                    type="string",
                    description=(
                        "Campaign ID to delete leads from. Required if list_id is not provided."
                    ),
                ),
                "list_id": ParameterDef(
                    type="string",
                    description=(
                        "Lead list ID to delete leads from. Required if campaign_id is not "
                        "provided."
                    ),
                ),
                "status": ParameterDef(
                    type="integer", description="Optional lead status filter"
                ),
                "ids": ParameterDef(type="array", description="Specific lead IDs to delete"),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of matching leads to delete, up to 10000",
                ),
            },
        ),
        ActionDefinition(
            name="update_lead_interest_status",
            description="Submit a background job to update a lead interest status.",
            parameters={
                "lead_email": ParameterDef(
                    type="string", description="Lead email address", required=True
                ),
                "interest_value": ParameterDef(
                    type="integer",
                    description="Interest status value. Pass null to reset to Lead.",
                ),
                "campaign_id": ParameterDef(
                    type="string", description="Campaign ID for the lead"
                ),
                "list_id": ParameterDef(
                    type="string", description="Lead list ID for the lead"
                ),
                "ai_interest_value": ParameterDef(
                    type="integer", description="AI interest value to set for the lead"
                ),
                "disable_auto_interest": ParameterDef(
                    type="boolean", description="Whether to disable auto interest"
                ),
            },
        ),
        ActionDefinition(
            name="list_campaigns",
            description=(
                "Retrieve campaigns with search, status, tag, and pagination filters."
            ),
            parameters={
                "limit": ParameterDef(
                    type="integer", description="Number of campaigns to return, from 1 to 100"
                ),
                "starting_after": ParameterDef(
                    type="string", description="Pagination cursor from next_starting_after"
                ),
                "search": ParameterDef(type="string", description="Search by campaign name"),
                "tag_ids": ParameterDef(
                    type="string", description="Comma-separated campaign tag IDs"
                ),
                "ai_sales_agent_id": ParameterDef(
                    type="string", description="AI Sales Agent ID filter"
                ),
                "status": ParameterDef(
                    type="integer", description="Campaign status enum value"
                ),
            },
        ),
        ActionDefinition(
            name="create_campaign",
            description="Create a campaign using the documented campaign schedule schema.",
            parameters={
                "name": ParameterDef(
                    type="string", description="Campaign name", required=True
                ),
                "campaign_schedule": ParameterDef(
                    type="object",
                    description="Campaign schedule object with schedules array",
                    required=True,
                ),
                "sequences": ParameterDef(
                    type="array", description="Campaign sequence definitions"
                ),
                "email_list": ParameterDef(type="array", description="Sending email accounts"),
                "daily_limit": ParameterDef(type="integer", description="Daily sending limit"),
                "daily_max_leads": ParameterDef(
                    type="integer", description="Daily maximum new leads to contact"
                ),
                "open_tracking": ParameterDef(
                    type="boolean", description="Whether to track opens"
                ),
                "stop_on_reply": ParameterDef(
                    type="boolean", description="Whether to stop the campaign on reply"
                ),
                "link_tracking": ParameterDef(
                    type="boolean", description="Whether to track links"
                ),
                "text_only": ParameterDef(
                    type="boolean", description="Whether the campaign is text only"
                ),
                "email_gap": ParameterDef(
                    type="integer", description="Gap between emails in minutes"
                ),
                "pl_value": ParameterDef(
                    type="number", description="Value of every positive lead"
                ),
            },
        ),
        ActionDefinition(
            name="patch_campaign",
            description="Update documented campaign fields.",
            parameters={
                "campaign_id": ParameterDef(
                    type="string", description="Campaign ID", required=True
                ),
                "name": ParameterDef(type="string", description="Campaign name"),
                "campaign_schedule": ParameterDef(
                    type="object",
                    description="Campaign schedule object with schedules array",
                ),
                "sequences": ParameterDef(
                    type="array", description="Campaign sequence definitions"
                ),
                "email_list": ParameterDef(type="array", description="Sending email accounts"),
                "daily_limit": ParameterDef(type="integer", description="Daily sending limit"),
                "daily_max_leads": ParameterDef(
                    type="integer", description="Daily maximum new leads to contact"
                ),
                "open_tracking": ParameterDef(
                    type="boolean", description="Whether to track opens"
                ),
                "stop_on_reply": ParameterDef(
                    type="boolean", description="Whether to stop the campaign on reply"
                ),
                "link_tracking": ParameterDef(
                    type="boolean", description="Whether to track links"
                ),
                "text_only": ParameterDef(
                    type="boolean", description="Whether the campaign is text only"
                ),
                "email_gap": ParameterDef(
                    type="integer", description="Gap between emails in minutes"
                ),
                "pl_value": ParameterDef(
                    type="number", description="Value of every positive lead"
                ),
            },
        ),
        ActionDefinition(
            name="activate_campaign",
            description="Activate, start, or resume a campaign.",
            parameters={
                "campaign_id": ParameterDef(
                    type="string", description="Campaign ID", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_emails",
            description="Retrieve Unibox emails with search and pagination filters.",
            parameters={
                "limit": ParameterDef(
                    type="integer", description="Number of emails to return, from 1 to 100"
                ),
                "starting_after": ParameterDef(
                    type="string", description="Pagination cursor from next_starting_after"
                ),
                "search": ParameterDef(
                    type="string",
                    description="Search query, email address, or thread:<thread-id>",
                ),
                "campaign_id": ParameterDef(type="string", description="Campaign ID filter"),
                "list_id": ParameterDef(type="string", description="Lead list ID filter"),
                "i_status": ParameterDef(
                    type="integer", description="Email interest status filter"
                ),
                "eaccount": ParameterDef(
                    type="string", description="Sending email account filter"
                ),
                "lead": ParameterDef(type="string", description="Lead email address filter"),
                "is_unread": ParameterDef(type="boolean", description="Unread status filter"),
            },
        ),
        ActionDefinition(
            name="reply_to_email",
            description="Send a reply to an existing Unibox email.",
            parameters={
                "eaccount": ParameterDef(
                    type="string",
                    description="Connected email account used to send the reply",
                    required=True,
                ),
                "reply_to_uuid": ParameterDef(
                    type="string", description="Email ID to reply to", required=True
                ),
                "subject": ParameterDef(
                    type="string", description="Reply subject", required=True
                ),
                "body_text": ParameterDef(
                    type="string", description="Reply body as plain text"
                ),
                "body_html": ParameterDef(type="string", description="Reply body as HTML"),
                "cc_address_email_list": ParameterDef(
                    type="string", description="Comma-separated CC email addresses"
                ),
                "bcc_address_email_list": ParameterDef(
                    type="string", description="Comma-separated BCC email addresses"
                ),
            },
        ),
        ActionDefinition(
            name="list_lead_lists",
            description="Retrieve lead lists with search and pagination filters.",
            parameters={
                "limit": ParameterDef(
                    type="integer", description="Number of lead lists to return, from 1 to 100"
                ),
                "starting_after": ParameterDef(
                    type="string", description="Starting-after cursor from next_starting_after"
                ),
                "has_enrichment_task": ParameterDef(
                    type="boolean", description="Filter by enrichment task setting"
                ),
                "search": ParameterDef(
                    type="string", description="Search query to filter lead lists by name"
                ),
            },
        ),
        ActionDefinition(
            name="create_lead_list",
            description="Create a lead list.",
            parameters={
                "name": ParameterDef(
                    type="string", description="Lead list name", required=True
                ),
                "has_enrichment_task": ParameterDef(
                    type="boolean",
                    description="Whether this list runs enrichment for every added lead",
                ),
                "owned_by": ParameterDef(
                    type="string", description="User ID of the lead list owner"
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Instantly V2 API key",
            setup_instructions=[
                "Sign in at https://app.instantly.ai",
                "Open Settings and navigate to the 'API Keys' (Integrations) section",
                "Create a new V2 API key with the required scopes",
                "Copy the key and paste it below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="INSTANTLY_API_KEY",
                    display_name="Instantly API Key",
                    description="Your Instantly V2 API key with the required scopes",
                    required=True,
                    sensitive=True,
                    about_url="https://developer.instantly.ai/",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.instantly.ai/api/v2/campaigns",
                method="GET",
                headers={"Authorization": "Bearer {api_key}"},
                params={"limit": "1"},
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description="Validates the API key with a minimal campaigns list (1 result)",
            ),
        ),
    ],
)
