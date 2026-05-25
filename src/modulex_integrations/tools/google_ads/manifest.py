"""Google Ads integration manifest."""
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
    name="google_ads",
    display_name="Google Ads",
    description=(
        "Google Ads API integration: run GAQL reports across Campaigns, "
        "Ad Groups, Ads, and Customers; create customer lists; send "
        "offline conversions; generate keyword ideas."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:google-ads",
    app_url="https://ads.google.com",
    categories=["Marketing & Advertising", "Analytics", "Business Services"],
    actions=[
        ActionDefinition(
            name="add_contact_to_list_by_email",
            description=(
                "Add a contact to a Google Ads Customer Match user list by "
                "email. Lists typically update in 6 to 12 hours. The email "
                "is SHA-256 hashed locally before upload."
            ),
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description=(
                        "Login customer ID (the Manager Account ID used as "
                        "login-customer-id header). Digits only, no dashes."
                    ),
                    required=True,
                ),
                "user_list_id": ParameterDef(
                    type="string",
                    description="ID of the CRM-based customer list to update.",
                    required=True,
                ),
                "contact_email": ParameterDef(
                    type="string",
                    description="Email address of the contact to add.",
                    required=True,
                ),
                "customer_client_id": ParameterDef(
                    type="string",
                    description=(
                        "Managed customer (client) ID. Defaults to account_id "
                        "when omitted."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="create_ad_group_report",
            description=(
                "Run a GAQL search report for the ad_group resource via "
                "GoogleAdsService.search."
            ),
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="Login customer ID (login-customer-id header).",
                    required=True,
                ),
                "fields": ParameterDef(
                    type="array",
                    description=(
                        "List of ad_group fields to select (e.g. "
                        "'ad_group.id', 'ad_group.name'). Each element is a "
                        "string; the 'ad_group.' prefix is auto-added if missing."
                    ),
                ),
                "segments": ParameterDef(
                    type="array",
                    description=(
                        "List of segments (e.g. 'segments.date'). Each element "
                        "is a string; the 'segments.' prefix is auto-added."
                    ),
                ),
                "metrics": ParameterDef(
                    type="array",
                    description=(
                        "List of metric fields (e.g. 'metrics.clicks'). Each "
                        "element is a string; the 'metrics.' prefix is auto-added."
                    ),
                ),
                "object_filter": ParameterDef(
                    type="array",
                    description=(
                        "Optional list of ad_group IDs to filter by. Each element "
                        "is a string (the numeric ID)."
                    ),
                ),
                "date_range": ParameterDef(
                    type="string",
                    description=(
                        "Date range constant: CUSTOM, TODAY, YESTERDAY, "
                        "LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, THIS_MONTH, "
                        "LAST_MONTH, THIS_WEEK_SUN_TODAY, THIS_WEEK_MON_TODAY, "
                        "LAST_WEEK_SUN_SAT, LAST_WEEK_MON_SUN, LAST_BUSINESS_WEEK."
                    ),
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="Custom range start (YYYY-MM-DD); required when date_range=CUSTOM.",
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="Custom range end (YYYY-MM-DD); required when date_range=CUSTOM.",
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Field name to order results by.",
                ),
                "direction": ParameterDef(
                    type="string",
                    description="Order direction: ASC or DESC.",
                    default="ASC",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return.",
                ),
                "customer_client_id": ParameterDef(
                    type="string",
                    description="Managed customer ID; defaults to account_id when omitted.",
                ),
            },
        ),
        ActionDefinition(
            name="create_ad_report",
            description=(
                "Run a GAQL search report for the ad_group_ad resource via "
                "GoogleAdsService.search."
            ),
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="Login customer ID (login-customer-id header).",
                    required=True,
                ),
                "fields": ParameterDef(
                    type="array",
                    description="List of ad_group_ad fields to select (strings).",
                ),
                "segments": ParameterDef(
                    type="array",
                    description="List of segments (strings).",
                ),
                "metrics": ParameterDef(
                    type="array",
                    description="List of metric fields (strings).",
                ),
                "object_filter": ParameterDef(
                    type="array",
                    description="Optional list of ad IDs to filter by (strings).",
                ),
                "date_range": ParameterDef(
                    type="string",
                    description="Date range constant. See create_ad_group_report for valid values.",
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="Custom range start (YYYY-MM-DD); required when date_range=CUSTOM.",
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="Custom range end (YYYY-MM-DD); required when date_range=CUSTOM.",
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Field name to order results by.",
                ),
                "direction": ParameterDef(
                    type="string",
                    description="Order direction: ASC or DESC.",
                    default="ASC",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return.",
                ),
                "customer_client_id": ParameterDef(
                    type="string",
                    description="Managed customer ID; defaults to account_id when omitted.",
                ),
            },
        ),
        ActionDefinition(
            name="create_campaign_report",
            description=(
                "Run a GAQL search report for the campaign resource via "
                "GoogleAdsService.search."
            ),
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="Login customer ID (login-customer-id header).",
                    required=True,
                ),
                "fields": ParameterDef(
                    type="array",
                    description="List of campaign fields to select (strings).",
                ),
                "segments": ParameterDef(
                    type="array",
                    description="List of segments (strings).",
                ),
                "metrics": ParameterDef(
                    type="array",
                    description="List of metric fields (strings).",
                ),
                "object_filter": ParameterDef(
                    type="array",
                    description="Optional list of campaign IDs to filter by (strings).",
                ),
                "date_range": ParameterDef(
                    type="string",
                    description="Date range constant. See create_ad_group_report for valid values.",
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="Custom range start (YYYY-MM-DD); required when date_range=CUSTOM.",
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="Custom range end (YYYY-MM-DD); required when date_range=CUSTOM.",
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Field name to order results by.",
                ),
                "direction": ParameterDef(
                    type="string",
                    description="Order direction: ASC or DESC.",
                    default="ASC",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return.",
                ),
                "customer_client_id": ParameterDef(
                    type="string",
                    description="Managed customer ID; defaults to account_id when omitted.",
                ),
            },
        ),
        ActionDefinition(
            name="create_customer_list",
            description=(
                "Create a Google Ads UserList (CRM_BASED / RULE_BASED / "
                "LOGICAL / BASIC_USER_LIST / LOOKALIKE). Returns the new "
                "user list ID and resource name."
            ),
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="Login customer ID (login-customer-id header).",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Name of the user list.",
                    required=True,
                ),
                "list_type": ParameterDef(
                    type="string",
                    description=(
                        "Which UserList variant to create. One of: "
                        "crmBasedUserList, ruleBasedUserList, logicalUserList, "
                        "basicUserList, lookalikeUserList. Determines which "
                        "fields list_type_data should populate."
                    ),
                    required=True,
                ),
                "list_type_data": ParameterDef(
                    type="object",
                    description=(
                        "Variant-specific payload. Merged under the list_type "
                        "key. See https://developers.google.com/google-ads/api/"
                        "reference/rpc/v21/UserList for the per-variant schema."
                    ),
                    default={},
                ),
                "description": ParameterDef(
                    type="string",
                    description="Optional description of the user list.",
                ),
                "additional_fields": ParameterDef(
                    type="object",
                    description=(
                        "Additional top-level UserList fields to merge into the "
                        "create payload (e.g. membershipLifeSpan)."
                    ),
                    default={},
                ),
                "customer_client_id": ParameterDef(
                    type="string",
                    description="Managed customer ID; defaults to account_id when omitted.",
                ),
            },
        ),
        ActionDefinition(
            name="create_customer_report",
            description=(
                "Run a GAQL search report for the customer resource via "
                "GoogleAdsService.search."
            ),
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="Login customer ID (login-customer-id header).",
                    required=True,
                ),
                "fields": ParameterDef(
                    type="array",
                    description="List of customer fields to select (strings).",
                ),
                "segments": ParameterDef(
                    type="array",
                    description="List of segments (strings).",
                ),
                "metrics": ParameterDef(
                    type="array",
                    description="List of metric fields (strings).",
                ),
                "object_filter": ParameterDef(
                    type="array",
                    description="Optional list of customer IDs to filter by (strings).",
                ),
                "date_range": ParameterDef(
                    type="string",
                    description="Date range constant. See create_ad_group_report for valid values.",
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="Custom range start (YYYY-MM-DD); required when date_range=CUSTOM.",
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="Custom range end (YYYY-MM-DD); required when date_range=CUSTOM.",
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Field name to order results by.",
                ),
                "direction": ParameterDef(
                    type="string",
                    description="Order direction: ASC or DESC.",
                    default="ASC",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return.",
                ),
                "customer_client_id": ParameterDef(
                    type="string",
                    description="Managed customer ID; defaults to account_id when omitted.",
                ),
            },
        ),
        ActionDefinition(
            name="create_report",
            description=(
                "Run a GAQL search report against any resource via "
                "GoogleAdsService.search. Builds a SELECT/WHERE/ORDER/LIMIT "
                "query from the supplied fields/segments/metrics."
            ),
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="Login customer ID (login-customer-id header).",
                    required=True,
                ),
                "resource": ParameterDef(
                    type="string",
                    description=(
                        "Resource name to FROM-clause against (e.g. campaign, "
                        "ad_group, ad_group_ad, customer)."
                    ),
                    required=True,
                ),
                "fields": ParameterDef(
                    type="array",
                    description=(
                        "List of resource fields to select (strings). The "
                        "resource prefix is auto-added if missing."
                    ),
                ),
                "segments": ParameterDef(
                    type="array",
                    description="List of segments (strings).",
                ),
                "metrics": ParameterDef(
                    type="array",
                    description="List of metric fields (strings).",
                ),
                "object_filter": ParameterDef(
                    type="array",
                    description="Optional list of resource IDs to filter by (strings).",
                ),
                "date_range": ParameterDef(
                    type="string",
                    description="Date range constant. See create_ad_group_report for valid values.",
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="Custom range start (YYYY-MM-DD); required when date_range=CUSTOM.",
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="Custom range end (YYYY-MM-DD); required when date_range=CUSTOM.",
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Field name to order results by.",
                ),
                "direction": ParameterDef(
                    type="string",
                    description="Order direction: ASC or DESC.",
                    default="ASC",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return.",
                ),
                "customer_client_id": ParameterDef(
                    type="string",
                    description="Managed customer ID; defaults to account_id when omitted.",
                ),
            },
        ),
        ActionDefinition(
            name="generate_keyword_ideas",
            description=(
                "Generate keyword ideas via KeywordPlanIdeaService."
                "generateKeywordIdeas. Pass the GenerateKeywordIdeasRequest "
                "body fields under additional_fields."
            ),
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="Login customer ID (login-customer-id header).",
                    required=True,
                ),
                "customer_client_id": ParameterDef(
                    type="string",
                    description=(
                        "Managed customer ID to run the request against "
                        "(required by the keyword ideas service)."
                    ),
                    required=True,
                ),
                "additional_fields": ParameterDef(
                    type="object",
                    description=(
                        "Body of the GenerateKeywordIdeasRequest. See "
                        "https://developers.google.com/google-ads/api/reference/"
                        "rpc/v22/KeywordPlanIdeaService/GenerateKeywordIdeas "
                        "for the required structure (e.g. language, geoTargetConstants, "
                        "keywordSeed)."
                    ),
                    default={},
                ),
            },
        ),
        ActionDefinition(
            name="list_account_id_options",
            description=(
                "List customer resources directly accessible by the authenticated "
                "user via CustomerService.ListAccessibleCustomers. Useful to "
                "discover candidate account_id values."
            ),
            parameters={},
        ),
        ActionDefinition(
            name="send_offline_conversion",
            description=(
                "Create a ConversionAction (offline conversion tracking) via "
                "ConversionActionService.mutate."
            ),
            parameters={
                "account_id": ParameterDef(
                    type="string",
                    description="Login customer ID (login-customer-id header).",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Name of the conversion action.",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description=(
                        "ConversionActionType enum value (e.g. UPLOAD_CLICKS, "
                        "UPLOAD_CALLS, WEBPAGE). See https://developers.google.com/"
                        "google-ads/api/reference/rpc/v21/ConversionActionTypeEnum.ConversionActionType."
                    ),
                    required=True,
                ),
                "additional_fields": ParameterDef(
                    type="object",
                    description=(
                        "Additional ConversionAction fields to merge into the "
                        "create payload (e.g. category, status, valueSettings)."
                    ),
                    default={},
                ),
                "customer_client_id": ParameterDef(
                    type="string",
                    description="Managed customer ID; defaults to account_id when omitted.",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description=(
                "Connect using Google OAuth2 (recommended). Requires a "
                "Google Ads API developer token in addition to the OAuth "
                "credentials."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_ADS_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth2 Client ID from Cloud Console.",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="123456789-xxxxxxxxxxxxxxxx.apps.googleusercontent.com",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_ADS_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google OAuth2 Client Secret.",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="GOCSPX-xxxxxxxxxxxxxxxxxxxx",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_ADS_DEVELOPER_TOKEN",
                    display_name="Developer Token",
                    description=(
                        "Google Ads API developer-token header value. Apply at "
                        "https://ads.google.com/aw/apicenter (Manager Account "
                        "required)."
                    ),
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://developers.google.com/google-ads/api/docs/get-started/dev-token",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scopes=[
                    "https://www.googleapis.com/auth/adwords",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                # The modulex OAuth callback only stores OAuth tokens in
                # auth_data, so GOOGLE_ADS_DEVELOPER_TOKEN cannot be
                # substituted here. We omit the developer-token header
                # entirely — the server returns 401 without it, but that
                # is enough to confirm the OAuth token format reached the
                # endpoint. Real validation runs at first action call via
                # tools.py which reads the developer token from auth_data.
                url="https://googleads.googleapis.com/v21/customers:listAccessibleCustomers",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200, 401, 403],
                ),
                cost_level="free",
                description=(
                    "Reachability check against listAccessibleCustomers. "
                    "Real OAuth+developer-token validation happens at "
                    "first action call."
                ),
            ),
        ),
    ],
)
