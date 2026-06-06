"""Mailchimp integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    BasicAuthSpec,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


def _list_id_param() -> ParameterDef:
    return ParameterDef(
        type="string", description="The unique list/audience ID", required=True
    )


def _email_param() -> ParameterDef:
    return ParameterDef(
        type="string", description="Subscriber email address", required=True
    )


def _campaign_id_param() -> ParameterDef:
    return ParameterDef(type="string", description="Campaign ID", required=True)


def _count_offset_params(default_count: int = 10) -> dict[str, ParameterDef]:
    return {
        "count": ParameterDef(
            type="integer", description="Results (max 1000)", default=default_count
        ),
        "offset": ParameterDef(
            type="integer", description="Results to skip", default=0
        ),
    }


manifest = IntegrationManifest(
    name="mailchimp",
    display_name="Mailchimp",
    description=(
        "Mailchimp marketing platform: list/audience CRUD, subscriber "
        "upsert, campaign lifecycle, tags, notes, and segments."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:mailgun-icon",
    app_url="https://mailchimp.com",
    categories=["Marketing & Advertising", "Marketing & Email", "Email Marketing", "CRM"],
    actions=[
        # --- Lists ---------------------------------------------------------
        ActionDefinition(
            name="get_lists",
            description="List all audiences",
            parameters=_count_offset_params(),
        ),
        ActionDefinition(
            name="get_list",
            description="Get details for a specific list/audience",
            parameters={"list_id": _list_id_param()},
        ),
        ActionDefinition(
            name="create_list",
            description="Create a new audience",
            parameters={
                "name": ParameterDef(
                    type="string", description="List name", required=True
                ),
                "contact_company": ParameterDef(
                    type="string", description="Company name", required=True
                ),
                "contact_address1": ParameterDef(
                    type="string", description="Street address", required=True
                ),
                "contact_city": ParameterDef(
                    type="string", description="City", required=True
                ),
                "contact_state": ParameterDef(
                    type="string", description="State/province", required=True
                ),
                "contact_zip": ParameterDef(
                    type="string", description="Postal code", required=True
                ),
                "contact_country": ParameterDef(
                    type="string",
                    description="ISO3166 country code (e.g. 'US')",
                    required=True,
                ),
                "permission_reminder": ParameterDef(
                    type="string",
                    description="Permission reminder text",
                    required=True,
                ),
                "from_name": ParameterDef(
                    type="string", description="Default from name", required=True
                ),
                "from_email": ParameterDef(
                    type="string", description="Default from email", required=True
                ),
                "subject": ParameterDef(
                    type="string",
                    description="Default subject line",
                    required=True,
                ),
                "language": ParameterDef(
                    type="string", description="Default language", default="en"
                ),
                "email_type_option": ParameterDef(
                    type="boolean",
                    description="Allow subscribers to choose HTML or text",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="delete_list",
            description="Delete an audience (permanent)",
            parameters={"list_id": _list_id_param()},
        ),
        # --- Subscribers ---------------------------------------------------
        ActionDefinition(
            name="get_list_members",
            description="List members in an audience (optional status filter)",
            parameters={
                "list_id": _list_id_param(),
                **_count_offset_params(),
                "status": ParameterDef(
                    type="string",
                    description=(
                        "subscribed/unsubscribed/cleaned/pending/"
                        "transactional/archived"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="get_subscriber",
            description="Get a subscriber by email (MD5 hash lookup)",
            parameters={
                "list_id": _list_id_param(),
                "email": _email_param(),
            },
        ),
        ActionDefinition(
            name="add_or_update_subscriber",
            description=(
                "Upsert a subscriber via PUT (members/{md5_hash}); if tags "
                "are provided, POST them in a follow-up call"
            ),
            parameters={
                "list_id": _list_id_param(),
                "email": _email_param(),
                "status_if_new": ParameterDef(
                    type="string",
                    description="Status if new (default 'subscribed')",
                    default="subscribed",
                ),
                "status": ParameterDef(
                    type="string", description="Current status"
                ),
                "email_type": ParameterDef(
                    type="string", description="'html' or 'text'"
                ),
                "merge_fields": ParameterDef(
                    type="object",
                    description="Merge fields (e.g. {'FNAME': 'John'})",
                ),
                "language": ParameterDef(
                    type="string", description="Subscriber language"
                ),
                "vip": ParameterDef(type="boolean", description="VIP status"),
                "tags": ParameterDef(
                    type="array", description="Tags to add (active)"
                ),
            },
        ),
        ActionDefinition(
            name="delete_subscriber",
            description=(
                "Permanently delete a subscriber via DELETE "
                "/members/{md5_hash}/actions/delete-permanent"
            ),
            parameters={
                "list_id": _list_id_param(),
                "email": _email_param(),
            },
        ),
        # --- Campaigns -----------------------------------------------------
        ActionDefinition(
            name="get_campaigns",
            description="List campaigns (optional type/status filters)",
            parameters={
                **_count_offset_params(),
                "type": ParameterDef(
                    type="string",
                    description="regular/plaintext/absplit/rss/variate",
                ),
                "status": ParameterDef(
                    type="string",
                    description="save/paused/schedule/sending/sent",
                ),
            },
        ),
        ActionDefinition(
            name="get_campaign",
            description="Get a specific campaign",
            parameters={"campaign_id": _campaign_id_param()},
        ),
        ActionDefinition(
            name="create_campaign",
            description="Create a campaign (settings flattened from kwargs)",
            parameters={
                "type": ParameterDef(
                    type="string",
                    description="Campaign type",
                    default="regular",
                ),
                "list_id": _list_id_param(),
                "subject_line": ParameterDef(
                    type="string", description="Subject line", required=True
                ),
                "from_name": ParameterDef(
                    type="string", description="From name", required=True
                ),
                "reply_to": ParameterDef(
                    type="string", description="Reply-to email", required=True
                ),
                "title": ParameterDef(
                    type="string", description="Campaign title"
                ),
                "preview_text": ParameterDef(
                    type="string", description="Preview text"
                ),
            },
        ),
        ActionDefinition(
            name="delete_campaign",
            description="Delete a campaign",
            parameters={"campaign_id": _campaign_id_param()},
        ),
        ActionDefinition(
            name="send_campaign",
            description="Send a campaign (POST /actions/send)",
            parameters={"campaign_id": _campaign_id_param()},
        ),
        ActionDefinition(
            name="get_campaign_report",
            description="Get a campaign's send/open/click report",
            parameters={"campaign_id": _campaign_id_param()},
        ),
        # --- Tags ----------------------------------------------------------
        ActionDefinition(
            name="get_member_tags",
            description="Get tags attached to a subscriber",
            parameters={
                "list_id": _list_id_param(),
                "email": _email_param(),
            },
        ),
        ActionDefinition(
            name="update_member_tags",
            description="Update tags on a subscriber (active/inactive list)",
            parameters={
                "list_id": _list_id_param(),
                "email": _email_param(),
                "tags": ParameterDef(
                    type="array",
                    description=(
                        "List of {name, status} where status is "
                        "'active' or 'inactive'"
                    ),
                    required=True,
                ),
            },
        ),
        # --- Notes ---------------------------------------------------------
        ActionDefinition(
            name="add_note_to_subscriber",
            description="Add an internal note to a subscriber (max 1000 chars)",
            parameters={
                "list_id": _list_id_param(),
                "email": _email_param(),
                "note": ParameterDef(
                    type="string", description="Note content", required=True
                ),
            },
        ),
        # --- Segments ------------------------------------------------------
        ActionDefinition(
            name="get_segments",
            description="List segments in an audience",
            parameters={
                "list_id": _list_id_param(),
                **_count_offset_params(),
            },
        ),
        ActionDefinition(
            name="add_member_to_segment",
            description="Add a subscriber email to a static segment",
            parameters={
                "list_id": _list_id_param(),
                "segment_id": ParameterDef(
                    type="string", description="Segment ID", required=True
                ),
                "email": _email_param(),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description=(
                "Connect using Mailchimp OAuth2 (recommended — avoids "
                "datacenter discovery and Basic Auth headaches)."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="MAILCHIMP_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Mailchimp OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://mailchimp.com/developer/marketing/guides/access-user-data-oauth-2/",
                ),
                EnvVar(
                    name="MAILCHIMP_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Mailchimp OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://mailchimp.com/developer/marketing/guides/access-user-data-oauth-2/",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://login.mailchimp.com/oauth2/authorize",
                token_url="https://login.mailchimp.com/oauth2/token",
                scopes=[],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://login.mailchimp.com/oauth2/metadata",
                method="GET",
                headers={"Authorization": "OAuth {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["dc", "api_endpoint"],
                ),
                cost_level="free",
                description=(
                    "Validates the OAuth token via the metadata endpoint; "
                    "response includes the user's datacenter (dc) and "
                    "api_endpoint, which tools.py can route to."
                ),
            ),
        ),
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description=(
                "Authenticate using your Mailchimp API key. The key "
                "includes the datacenter suffix (e.g. xxx-us10)."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="MAILCHIMP_API_KEY",
                    display_name="Mailchimp API Key",
                    description=(
                        "Your Mailchimp API key (with datacenter suffix)"
                    ),
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-us10",
                    about_url="https://mailchimp.com/help/about-api-keys/",
                ),
                EnvVar(
                    name="MAILCHIMP_DATACENTER",
                    display_name="Datacenter",
                    description=(
                        "Datacenter portion of your API key (suffix after the "
                        "dash, e.g. 'us10', 'us20', 'eu1'). Mailchimp routes "
                        "API requests to the datacenter where your account "
                        "lives."
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="us10",
                    about_url="https://mailchimp.com/help/about-api-keys/",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://{MAILCHIMP_DATACENTER}.api.mailchimp.com/3.0/ping",
                method="GET",
                # Mailchimp Basic Auth: literal "anystring" as username,
                # API key as password. The modulex runtime synthesises
                # ``Authorization: Basic <base64(anystring:KEY)>``.
                auth=BasicAuthSpec(
                    username_placeholder="anystring",
                    password_placeholder="MAILCHIMP_API_KEY",
                ),
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["health_status"]
                ),
                cost_level="free",
                description="Validates API key + datacenter via /ping (Basic Auth).",
            ),
        ),
    ],
)
